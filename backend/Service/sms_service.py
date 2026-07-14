import os
import requests
import urllib3
from dotenv import load_dotenv
from typing import List, Optional

# Suppress insecure request warnings from certificate verification bypass
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SMSService:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("AFRICAS_TALKING_KEY")
        self.username = os.getenv("AFRICAS_TALKING_USERNAME", "sandbox")
        self.sender_id = os.getenv("AFRICAS_TALKING_SENDER_ID")

        if not self.api_key:
            print("WARNING: AFRICAS_TALKING_KEY is missing from the environment configuration.")

    def send_sms(self, message: str, phone_numbers: List[str], sender_id: Optional[str] = None) -> dict:
        """
        Sends Bulk SMS to specified recipients using Africa's Talking API.
        Uses application/x-www-form-urlencoded payload format for both Sandbox and Production.
        """
        if not self.api_key:
            raise ValueError("AFRICAS_TALKING_KEY is not configured in .env.")

        # Clean quotes and spaces from configurations
        username_clean = self.username.strip('"\'').lower().strip()
        api_key_clean = self.api_key.strip('"\'').strip()
        
        headers = {
            "Accept": "application/json",
            "apiKey": api_key_clean
        }

        # Determine target endpoint based on environment
        if username_clean == "sandbox":
            url = "https://api.sandbox.africastalking.com/version1/messaging"
        else:
            url = "https://api.africastalking.com/version1/messaging"

        # Build url-encoded form payload (expects 'to' comma-separated string, and 'from' for senderId)
        payload = {
            "username": username_clean,
            "to": ",".join(phone_numbers),
            "message": message
        }

        active_sender = sender_id or self.sender_id
        if active_sender:
            payload["from"] = active_sender.strip('"\'')

        try:
            # Passing dict to 'data' parameter instructs requests to encode as application/x-www-form-urlencoded
            response = requests.post(url, headers=headers, data=payload, verify=False, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_detail = str(e)
            if e.response is not None:
                try:
                    error_detail = e.response.json()
                except ValueError:
                    error_detail = e.response.text
            print(f"Africa's Talking SMS failed: {error_detail}")
            raise Exception(f"SMS delivery failed: {error_detail}")
