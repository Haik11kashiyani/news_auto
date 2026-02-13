import os
import json
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

class YouTubeUploader:
    def __init__(self):
        self.creds = None
        self.service = None
        self.scopes = ["https://www.googleapis.com/auth/youtube.upload"]

    def authenticate(self):
        """
        Authenticate using credentials from env var YOUTUBE_CREDS_JSON.
        Expects the JSON structure of a 'token.json' (refresh token included).
        """
        creds_json = os.getenv("YOUTUBE_CREDS_JSON")
        
        # Fallback: Check for local token.json if env var is missing
        if not creds_json and os.path.exists("token.json"):
            print("Env var YOUTUBE_CREDS_JSON not found. Using local token.json...")
            with open("token.json", "r") as f:
                creds_json = f.read()

        if not creds_json:
            print("Error: YOUTUBE_CREDS_JSON environment variable not found and no local token.json.")
            return False

        try:
            # Parse the JSON string
            info = json.loads(creds_json)
            
            # Create Credentials object
            self.creds = google.oauth2.credentials.Credentials.from_authorized_user_info(info, self.scopes)

            # Refresh if expired
            if self.creds and self.creds.expired and self.creds.refresh_token:
                print("Refreshing access token...")
                self.creds.refresh(Request())

            self.service = build("youtube", "v3", credentials=self.creds)
            print("YouTube Service Built Successfully.")
            return True

        except Exception as e:
            print(f"Authentication failed: {e}")
            return False

    def upload_video(self, file_path, title, description, tags, category_id="25", privacy_status="public"):
        """
        Uploads a video to YouTube.
        category_id 25 = News & Politics
        """
        if not self.service:
            if not self.authenticate():
                return None

        print(f"Uploading file: {file_path}")
        
        body = {
            "snippet": {
                "title": title[:100], # Max 100 chars
                "description": description[:5000], # Max 5000 chars
                "tags": tags,
                "categoryId": category_id
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False
            }
        }

        try:
            # Resumable upload
            media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
            request = self.service.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media
            )
            
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    print(f"Uploaded {int(status.progress() * 100)}%")

            print(f"Upload Complete! Video ID: {response.get('id')}")
            return response.get('id')

        except Exception as e:
            print(f"Upload failed: {e}")
            return None
