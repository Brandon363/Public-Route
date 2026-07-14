import os
import json
import base64
import wave
import io
from typing import Dict, Any
from google import genai
from google.genai import types
from pydantic import BaseModel

# Import centralized model variables
from Config.variables import TRANSCRIPTION_MODEL, TTS_MODEL

class VoiceAnalysisResponse(BaseModel):
    transcription: str
    translated_text: str
    is_complete: bool
    extracted_issue: str
    extracted_location: str
    response_text: str
    response_text_en: str
    response_lang: str

class VoiceService:
    """
    Handles transcription, translation, details extraction (issue and location) 
    via Gemini, and generates spoken response audio using the Gemini TTS model.
    """
    def __init__(self):
        # Initialises the client (automatically uses GEMINI_API_KEY from environment)
        self.client = genai.Client()

    def _add_wav_header(self, pcm_data: bytes, channels: int = 1, rate: int = 24000, sample_width: int = 2) -> bytes:
        wav_buf = io.BytesIO()
        with wave.open(wav_buf, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(rate)
            wf.writeframes(pcm_data)
        return wav_buf.getvalue()

    def process_voice_message(
        self,
        audio_bytes: bytes,
        mime_type: str,
        accumulated_description: str,
        accumulated_location: str
    ) -> Dict[str, Any]:
        prompt = (
            "You are a helpful public service intake assistant. The user is reporting a service issue "
            "(e.g., burst pipe, pothole, electricity failure, waste dump, etc.) or answering your question via voice.\n\n"
            "We want to extract two critical details from their message:\n"
            "1. 'extracted_issue': Description of what the service issue is (what is wrong, what happened).\n"
            "2. 'extracted_location': Description of where the issue is located (street name, landmarks, district).\n\n"
            "Please combine what is mentioned in this voice note with the existing accumulated information:\n"
            f"- Existing accumulated issue description: \"{accumulated_description or ''}\"\n"
            f"- Existing accumulated location: \"{accumulated_location or ''}\"\n\n"
            "Analyze the voice note:\n"
            "- First transcribe it verbatim and translate it to English if it is in another language (e.g. Shona, Ndebele, Zulu).\n"
            "- Merge any new description details or locations spoken in the voice note with the existing accumulated variables.\n"
            "- Determine if we now have both details (description AND location) to submit the report. If both are present, set 'is_complete' to true. Otherwise, set it to false.\n"
            "- Formulate a polite, conversational voice assistant response ('response_text') to the user:\n"
            "  * If 'is_complete' is true: speak a success/confirmation message. Summarize the issue and location we have, e.g., 'Thank you. I have captured your report of a [brief issue description] at [location description]. You can now review the details and submit.'\n"
            "  * If location is missing: ask them to describe the location, e.g., 'I got the details of the issue, but where is it located?'\n"
            "  * If issue description is missing: ask them what the issue is, e.g., 'I got the location, but could you describe what the issue is there?'\n"
            "  * If both are missing (e.g. the user just said hello or a greeting): respond with a friendly greeting in their language and ask how you can help them report a service issue (e.g. 'Mhoroi! Ndingakubatsirai sei nhasi? Ndapota tsanangurai dambudziko renyu uye kwariri.'). Otherwise, ask them to describe the issue and location.\n"
            "- CRITICAL: If the user spoke in a language other than English (e.g., Shona, Ndebele, Zulu), translate 'response_text' to their language so they hear the question/confirmation in their language, and set 'response_lang' to the language code of the translated response (e.g., 'sn' for Shona, 'zu' for Zulu, 'en' for English). Otherwise, output in English ('en').\n"
            "- Also formulate an English translation of the response_text, and return it under the key 'response_text_en'.\n\n"
        )

        try:
            # 1. Speech-to-Text & extraction using Gemini Flash model
            res = self.client.models.generate_content(
                model=TRANSCRIPTION_MODEL,
                contents=[
                    types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                    prompt
                ],
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json",
                    response_schema=VoiceAnalysisResponse
                )
            )
            analysis = json.loads(res.text)
        except Exception as e:
            print(f"Error invoking Gemini STT/parsing: {e}")
            raise ValueError(f"Failed to process voice note with Gemini: {str(e)}")

        # 2. Text-to-Speech using the preview TTS model
        response_text = analysis.get("response_text", "Sorry, something went wrong.")
        
        try:
            # Call TTS interaction API
            interaction = self.client.interactions.create(
                model=TTS_MODEL,
                input=f"Read the following text naturally in a calm and friendly tone: {response_text}",
                response_format={"type": "audio"},
                generation_config={
                    "speech_config": [
                        {"voice": "Kore"}
                    ]
                }
            )
            
            # Decode the base64 raw PCM bytes and wrap them in a standard WAV container
            raw_pcm = base64.b64decode(interaction.output_audio.data)
            wav_bytes = self._add_wav_header(raw_pcm)
            
            analysis["audio_base64"] = base64.b64encode(wav_bytes).decode("utf-8")
        except Exception as e:
            print(f"Error generating TTS audio using {TTS_MODEL}: {e}")
            analysis["audio_base64"] = ""

        return analysis

    def process_text_message(
        self,
        user_text: str,
        accumulated_description: str,
        accumulated_location: str
    ) -> Dict[str, Any]:
        prompt = (
            "You are a helpful public service intake assistant. The user is reporting a service issue "
            "(e.g., burst pipe, pothole, electricity failure, waste dump, etc.) or answering your question via text.\n\n"
            "We want to extract two critical details from their message:\n"
            "1. 'extracted_issue': Description of what the service issue is (what is wrong, what happened).\n"
            "2. 'extracted_location': Description of where the issue is located (street name, landmarks, district).\n\n"
            "Please combine what is mentioned in this new message with the existing accumulated information:\n"
            f"- Existing accumulated issue description: \"{accumulated_description or ''}\"\n"
            f"- Existing accumulated location: \"{accumulated_location or ''}\"\n\n"
            "Analyze the message:\n"
            "- If the message is not in English (e.g. Shona, Ndebele, Zulu), translate it to English.\n"
            "- Merge any new description details or locations written in the message with the existing accumulated variables.\n"
            "- Determine if we now have both details (description AND location) to submit the report. If both are present, set 'is_complete' to true. Otherwise, set it to false.\n"
            "- Formulate a polite, conversational voice assistant response ('response_text') to the user:\n"
            "  * If 'is_complete' is true: speak a success/confirmation message. Summarize the issue and location we have, e.g., 'Thank you. I have captured your report of a [brief issue description] at [location description]. You can now review the details and submit.'\n"
            "  * If location is missing: ask them to describe the location, e.g., 'I got the details of the issue, but where is it located?'\n"
            "  * If issue description is missing: ask them what the issue is, e.g., 'I got the location, but could you describe what the issue is there?'\n"
            "  * If both are missing (e.g. the user just said hello or a greeting): respond with a friendly greeting in their language and ask how you can help them report a service issue (e.g. 'Mhoroi! Ndingakubatsirai sei nhasi? Ndapota tsanangurai dambudziko renyu uye kwariri.'). Otherwise, ask them to describe the issue and location.\n"
            "- CRITICAL: If the user wrote in a language other than English (e.g., Shona, Ndebele, Zulu), translate 'response_text' to their language so they hear the question/confirmation in their language, and set 'response_lang' to the language code of the translated response (e.g., 'sn' for Shona, 'zu' for Zulu, 'en' for English). Otherwise, output in English ('en').\n"
            "- Also formulate an English translation of the response_text, and return it under the key 'response_text_en'.\n\n"
        )

        try:
            # Generate content using text input
            res = self.client.models.generate_content(
                model=TRANSCRIPTION_MODEL,
                contents=[
                    prompt + f"\n\nNew user message: \"{user_text}\""
                ],
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json",
                    response_schema=VoiceAnalysisResponse
                )
            )
            analysis = json.loads(res.text)
        except Exception as e:
            print(f"Error invoking Gemini text parsing: {e}")
            raise ValueError(f"Failed to process text message with Gemini: {str(e)}")

        # 2. Text-to-Speech using the preview TTS model
        response_text = analysis.get("response_text", "Sorry, something went wrong.")
        
        try:
            interaction = self.client.interactions.create(
                model=TTS_MODEL,
                input=f"Read the following text naturally in a calm and friendly tone: {response_text}",
                response_format={"type": "audio"},
                generation_config={
                    "speech_config": [
                        {"voice": "Kore"}
                    ]
                }
            )
            raw_pcm = base64.b64decode(interaction.output_audio.data)
            wav_bytes = self._add_wav_header(raw_pcm)
            
            analysis["audio_base64"] = base64.b64encode(wav_bytes).decode("utf-8")
        except Exception as e:
            print(f"Error generating TTS audio using {TTS_MODEL}: {e}")
            analysis["audio_base64"] = ""

        return analysis
