from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import os
import base64
import json
import tempfile
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")
TOKEN_PATH = os.path.join(BASE_DIR, "token.pickle")

def get_gmail_service():
    creds = None

    # ✅ FIX 1: Try loading token from environment variable (for Render deployment)
    token_b64 = os.environ.get("GMAIL_TOKEN_BASE64")
    if token_b64:
        token_data = base64.b64decode(token_b64)
        creds = pickle.loads(token_data)

    # ✅ FIX 2: Fall back to local token.pickle (for local development)
    elif os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "rb") as token:
            creds = pickle.load(token)

    # Refresh token if expired
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # Save refreshed token back to env or file
        if not token_b64 and os.path.exists(TOKEN_PATH):
            with open(TOKEN_PATH, "wb") as token:
                pickle.dump(creds, token)

    # ✅ FIX 3: Only run local OAuth flow if no token at all (local dev only)
    elif not creds:
        # ✅ FIX 4: Load credentials from env var if file doesn't exist
        google_creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
        if google_creds_json:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                f.write(google_creds_json)
                temp_path = f.name
            flow = InstalledAppFlow.from_client_secrets_file(temp_path, SCOPES)
            os.unlink(temp_path)
        elif os.path.exists(CREDENTIALS_PATH):
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
        else:
            raise FileNotFoundError(
                f"credentials.json not found at {CREDENTIALS_PATH}. "
                "Please place it in the same folder as gmail_auth.py."
            )

        creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "wb") as token:
            pickle.dump(creds, token)

    return build("gmail", "v1", credentials=creds)