#!/usr/bin/env python3
"""
setup_youtube_auth.py
=====================
Run this ONCE to connect your YouTube account.
After this, main.py uploads automatically — no browser needed again.

What it does:
  1. Opens Google OAuth in your browser
  2. You sign in and grant permission
  3. Saves token.json — auto-refreshes forever
"""
import os
import sys
import pickle
import webbrowser

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def main():
    print("=" * 60)
    print("  YouTube OAuth Setup")
    print("=" * 60)

    # Check client_secrets.json
    if not os.path.exists("client_secrets.json"):
        print("""
❌  client_secrets.json NOT found!

Follow these steps to get it (takes ~3 minutes):

  1. Go to: https://console.cloud.google.com/
  2. Create a NEW project  (top bar → New Project)
  3. Search "YouTube Data API v3" → Enable it
  4. Left menu → APIs & Services → Credentials
  5. Click "+ Create Credentials" → "OAuth 2.0 Client IDs"
  6. Application type → "Desktop app" → Create
  7. Click DOWNLOAD (⬇) button → save the JSON file
  8. Rename the downloaded file to:  client_secrets.json
  9. Put it in this folder (YoutubeAutomation/)
 10. Run this script again:  python setup_youtube_auth.py

Opening Google Cloud Console now…
""")
        webbrowser.open("https://console.cloud.google.com/apis/credentials")
        return

    print("\n✅  client_secrets.json found!")
    print("🌐  Opening browser for Google sign-in…\n")

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", SCOPES)
        credentials = flow.run_local_server(port=0)

        with open("token.json", "wb") as fh:
            pickle.dump(credentials, fh)

        print("""
✅  Authentication successful!
✅  token.json saved — you will NOT need to do this again.
    (Token auto-refreshes every time main.py runs)

You can now run:
    python main.py
""")
    except Exception as e:
        print(f"\n❌  OAuth error: {e}")
        print("Make sure client_secrets.json is valid and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
