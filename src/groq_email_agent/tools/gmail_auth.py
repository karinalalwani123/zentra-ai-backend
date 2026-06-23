from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import os
import base64
import tempfile

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")
TOKEN_PATH = os.path.join(BASE_DIR, "token.pickle")


def get_gmail_service():
    creds = None

    # ===== STEP 1: Load token from environment variable (Render) =====
    token_b64 = os.environ.get("GMAIL_TOKEN_BASE64")
    if token_b64:
        try:
            token_data = base64.b64decode(token_b64)
            creds = pickle.loads(token_data)
            print("✅ Token loaded from environment variable")
        except Exception as e:
            print(f"❌ Failed to load token from env: {e}")
            creds = None

    # ===== STEP 2: Load from local token.pickle (local dev) =====
    if not creds and os.path.exists(TOKEN_PATH):
        try:
            with open(TOKEN_PATH, "rb") as token:
                creds = pickle.load(token)
            print("✅ Token loaded from local file")
        except Exception as e:
            print(f"❌ Failed to load local token: {e}")
            creds = None

    # ===== STEP 3: Refresh token if expired =====
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            print("🔄 Token refreshed successfully")
            # Save refreshed token locally if running locally
            if not token_b64 and os.path.exists(TOKEN_PATH):
                with open(TOKEN_PATH, "wb") as token:
                    pickle.dump(creds, token)
                print("💾 Refreshed token saved locally")
        except Exception as e:
            print(f"❌ Token refresh failed: {e}")
            # Delete invalid token
            if os.path.exists(TOKEN_PATH):
                os.remove(TOKEN_PATH)
                print("🗑️ Invalid token deleted")
            creds = None

    # ===== STEP 4: Re-authenticate if no valid token =====
    if not creds:
        print("🔐 No valid token — starting OAuth flow")
        
        google_creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
        
        if google_creds_json:
            # Load credentials from environment variable
            try:
                with tempfile.NamedTemporaryFile(
                    mode='w', suffix='.json', delete=False
                ) as f:
                    f.write(google_creds_json)
                    temp_path = f.name
                flow = InstalledAppFlow.from_client_secrets_file(temp_path, SCOPES)
                os.unlink(temp_path)
                print("✅ Credentials loaded from environment variable")
            except Exception as e:
                raise Exception(f"Failed to load credentials from env: {e}")

        elif os.path.exists(CREDENTIALS_PATH):
            # Load credentials from local file
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, SCOPES
            )
            print("✅ Credentials loaded from local file")

        else:
            raise FileNotFoundError(
                f"credentials.json not found at {CREDENTIALS_PATH}. "
                "Please place it in the same folder as gmail_auth.py "
                "or set GOOGLE_CREDENTIALS_JSON environment variable."
            )

        # Run OAuth flow
        creds = flow.run_local_server(port=0)
        print("✅ OAuth flow completed successfully")

        # Save new token locally
        with open(TOKEN_PATH, "wb") as token:
            pickle.dump(creds, token)
        print("💾 New token saved to token.pickle")

        # Print base64 for Render
        token_b64_new = base64.b64encode(
            open(TOKEN_PATH, "rb").read()
        ).decode()
        print(f"\n📋 Copy this to Render GMAIL_TOKEN_BASE64:\n{token_b64_new}\n")

    return build("gmail", "v1", credentials=creds)