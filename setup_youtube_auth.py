import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

# Scopes required by the bot
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def main():
    print("=== YouTube Authentication Helper ===")
    print("This script will help you generate the JSON for your GitHub Secret: YOUTUBE_CREDS_JSON")
    print("\nPrerequisites:")
    print("1. Go to Google Cloud Console (https://console.cloud.google.com/)")
    print("2. Create a Project (or use existing)")
    print("3. Enable 'YouTube Data API v3'")
    print("4. Go to Credentials -> Create Credentials -> OAuth Client ID -> Desktop App")
    print("5. Download the JSON file and save it as 'client_secret.json' in this folder.")
    
    if not os.path.exists("client_secret.json"):
        print("\nERROR: 'client_secret.json' not found!")
        print("Please download it from Google Cloud Console and save it here.")
        return

    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            "client_secret.json", SCOPES
        )
        # prompt='consent' ensures we get a refresh token even if we've authorized before.
        # authorization_prompt_message is purely cosmetic for the CLI.
        creds = flow.run_local_server(
            port=0,
            authorization_prompt_message="Please visit this URL: {url}",
            prompt='consent'
        )
        
        # Convert credentials to JSON format suitable for storing in secrets
        creds_json = creds.to_json()
        
        print("\nSUCCESS! Authentication complete.")
        print("\nCopy the following JSON content EXACTLY (including braces) and paste it into GitHub Secret 'YOUTUBE_CREDS_JSON':")
        print("-" * 50)
        print(creds_json)
        print("-" * 50)
        
        # Also save to file just in case
        with open("token.json", "w") as f:
            f.write(creds_json)
        print(f"\n(Also saved to 'token.json' for reference)")
        
    except Exception as e:
        print(f"\nError during authentication: {e}")

if __name__ == "__main__":
    main()
