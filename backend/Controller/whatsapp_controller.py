import os
import base64
import urllib.request
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Form, Request, Response
from sqlalchemy.orm import Session

from Config.database import get_db
from Repository.whatsapp_session_repository import WhatsAppSessionRepository
from Service.voice_service import VoiceService
from Service.submission_service import SubmissionService
from Service.case_service import CaseService
from Schema.submission_schema import SubmissionCreate
from Utils.Enums import ChannelEnum, ConsentStatusEnum

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])

# Create uploads directory for serving dynamic media
UPLOAD_DIR = os.path.join("uploads", "whatsapp")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/webhook")
async def whatsapp_webhook(
    request: Request,
    From: str = Form(...),
    Body: Optional[str] = Form(None),
    MediaUrl0: Optional[str] = Form(None),
    MediaContentType0: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Twilio WhatsApp Webhook. Processes incoming text and audio notes,
    maintains conversation session state, and replies with text/audio TwiML.
    """
    repo = WhatsAppSessionRepository(db)
    voice_service = VoiceService()
    submission_service = SubmissionService(db)
    case_service = CaseService(db)

    # 1. Retrieve or create session state for user
    session = repo.get_by_phone(From)
    acc_desc = session.accumulated_description if session else ""
    acc_loc = session.accumulated_location if session else ""

    is_voice = bool(MediaUrl0)

    # 2. Process voice note if present, otherwise process text
    if is_voice:
        # Download audio from Twilio
        try:
            req = urllib.request.Request(
                MediaUrl0,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=20) as response:
                audio_bytes = response.read()
            mime_type = MediaContentType0 or "audio/ogg"
            result = voice_service.process_voice_message(
                audio_bytes=audio_bytes,
                mime_type=mime_type,
                accumulated_description=acc_desc,
                accumulated_location=acc_loc
            )
        except Exception as e:
            print(f"Error downloading or processing audio: {e}")
            return Response(
                content="<?xml version=\"1.0\" encoding=\"UTF-8\"?><Response><Message><Body>Sorry, I had trouble reading your voice note. Please try speaking again or type your message.</Body></Message></Response>",
                media_type="application/xml"
            )
    else:
        # Process text message
        text_body = Body.strip() if Body else ""
        if not text_body:
            return Response(
                content="<?xml version=\"1.0\" encoding=\"UTF-8\"?><Response><Message><Body>Please send a text message or a voice note describing the service issue.</Body></Message></Response>",
                media_type="application/xml"
            )
            
        try:
            result = voice_service.process_text_message(
                user_text=text_body,
                accumulated_description=acc_desc,
                accumulated_location=acc_loc
            )
        except Exception as e:
            print(f"Error processing text: {e}")
            return Response(
                content="<?xml version=\"1.0\" encoding=\"UTF-8\"?><Response><Message><Body>Sorry, something went wrong processing your message.</Body></Message></Response>",
                media_type="application/xml"
            )

    # 3. Read extracted results
    extracted_issue = result.get("extracted_issue", "")
    extracted_location = result.get("extracted_location", "")
    is_complete = result.get("is_complete", False)
    response_text = result.get("response_text", "Thank you.")
    audio_base64 = result.get("audio_base64", "")

    # Clean phone identifier (e.g. "whatsapp:+263771234567" -> "+263771234567")
    phone_clean = From.replace("whatsapp:", "")
    channel = ChannelEnum.WHATSAPP_VOICE if MediaUrl0 else ChannelEnum.WHATSAPP_TEXT

    # 4. Handle complete report vs partial state
    if is_complete:
        # Submit the finalized case to the database!
        try:
            # Create a mock/complete payload for submission
            sub_payload = SubmissionCreate(
                channel=channel,
                received_at=datetime.now(timezone.utc),
                service_description=extracted_issue,
                location_text=extracted_location,
                language_code=result.get("response_lang", "en"),
                consent_status=ConsentStatusEnum.NOT_REQUIRED,
                contact_phone=phone_clean
            )
            
            # Save submission and run classification/routing immediately
            submission = submission_service.create_submission(sub_payload)
            case = case_service.create_case_from_submission(
                submission_id=submission.id,
                actor_channel=channel.value
            )
            
            # Delete session state on success so user starts fresh next time
            repo.delete_by_phone(From)
            
            # Send completion response with Reference Number
            completion_text = (
                f"Thank you! Your report has been submitted.\n\n"
                f"📋 Reference Number: {case.reference_number}\n"
                f"📍 Location: {extracted_location}\n\n"
                f"Our team is on it."
            )
            return Response(
                content=f'<?xml version="1.0" encoding="UTF-8"?><Response><Message><Body>{completion_text}</Body></Message></Response>',
                media_type="application/xml"
            )
        except Exception as e:
            print(f"Error saving submission from WhatsApp: {e}")
            return Response(
                content="<?xml version=\"1.0\" encoding=\"UTF-8\"?><Response><Message><Body>Sorry, I had an error submitting your report. Please try again.</Body></Message></Response>",
                media_type="application/xml"
            )
    else:
        # Update session state with accumulated info
        repo.create_or_update(
            phone_number=From,
            description=extracted_issue,
            location=extracted_location
        )
        
        if is_voice:
            # Save generated audio response as MP3 for Twilio/WhatsApp compatibility
            # We use a base64 encoded MD5/hash of From to create a unique filename
            filename = f"{base64.b32encode(From.encode()).decode().replace('=', '')}.mp3"
            file_path = os.path.join(UPLOAD_DIR, filename)
            response_lang = result.get("response_lang", "en")
            
            try:
                # Fallback text to speak if Google TTS doesn't support the native tongue sn/zu
                if response_lang not in ["en", "sw"]:
                    text_to_speak = result.get("response_text_en", response_text)
                    tts_lang = "en"
                else:
                    text_to_speak = response_text
                    tts_lang = response_lang

                # Generate highly-compatible MP3 audio response using Google Translate TTS
                import urllib.parse
                encoded_text = urllib.parse.quote(text_to_speak)
                tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl={tts_lang}&client=tw-ob&q={encoded_text}"
                
                req = urllib.request.Request(
                    tts_url,
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                with urllib.request.urlopen(req, timeout=12) as response:
                    audio_data = response.read()
                    
                with open(file_path, "wb") as f:
                    f.write(audio_data)
                
                # Format TwiML with both Text and Media Voice audio response
                public_url = str(request.base_url).rstrip("/")
                media_link = f"{public_url}/api/v1/whatsapp/media/{filename}"
                
                twiml_res = (
                    f'<?xml version="1.0" encoding="UTF-8"?>'
                    f'<Response>'
                    f'    <Message>'
                    f'        <Body>{response_text}</Body>'
                    f'        <Media>{media_link}</Media>'
                    f'    </Message>'
                    f'</Response>'
                )
            except Exception as e:
                print(f"Error generating Google TTS MP3 or formatting media TwiML: {e}")
                twiml_res = f'<?xml version="1.0" encoding="UTF-8"?><Response><Message><Body>{response_text}</Body></Message></Response>'
        else:
            # Text only response — do not generate voice audio response
            twiml_res = f'<?xml version="1.0" encoding="UTF-8"?><Response><Message><Body>{response_text}</Body></Message></Response>'
            
        return Response(content=twiml_res, media_type="application/xml")


from fastapi.responses import FileResponse

@router.get("/media/{filename}")
def get_whatsapp_media(filename: str):
    """
    Serves the generated response MP3/WAV files to Twilio WhatsApp API.
    """
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        media_type = "audio/mpeg" if filename.endswith(".mp3") else "audio/wav"
        return FileResponse(file_path, media_type=media_type)
    return Response(status_code=404)
