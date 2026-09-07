"""
uploader.py - Uploads videos to YouTube using the Data API v3.
OAuth token is saved locally and auto-refreshed — no re-authentication needed.
"""
import os
import pickle
import logging
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _get_service(config: dict):
    """Return an authenticated YouTube API service."""
    token_path   = config.get("youtube_token_path",          "token.json")
    secrets_path = config.get("youtube_client_secrets_path", "client_secrets.json")

    credentials = None

    # Load cached token
    if os.path.exists(token_path):
        with open(token_path, "rb") as fh:
            credentials = pickle.load(fh)

    # Refresh if expired
    if credentials and credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
            with open(token_path, "wb") as fh:
                pickle.dump(credentials, fh)
            logger.info("OAuth token refreshed automatically")
        except Exception as e:
            logger.warning(f"Token refresh failed: {e}")
            credentials = None

    # Full OAuth flow (opens browser once)
    if not credentials or not credentials.valid:
        if not os.path.exists(secrets_path):
            raise FileNotFoundError(
                f"\n❌ '{secrets_path}' not found!\n"
                "Run  python setup_youtube_auth.py  first."
            )
        flow = InstalledAppFlow.from_client_secrets_file(secrets_path, SCOPES)
        credentials = flow.run_local_server(port=0)
        with open(token_path, "wb") as fh:
            pickle.dump(credentials, fh)
        logger.info("New OAuth token saved")

    return build("youtube", "v3", credentials=credentials)


def _upload_single(youtube, video_path: str, meta: dict,
                   category_id: str = "27", privacy: str = "public") -> tuple:
    """Upload one video file. Returns (video_id, url)."""
    body = {
        "snippet": {
            "title":       meta["title"],
            "description": meta["description"],
            "tags":        meta.get("tags", []),
            "categoryId":  category_id,
        },
        "status": {
            "privacyStatus":              privacy,
            "selfDeclaredMadeForKids":    True,   # ← marks as kids content
        },
    }

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=5 * 1024 * 1024,  # 5 MB chunks
    )

    req = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    logger.info(f"Uploading: {meta['title']}")
    response = None
    while response is None:
        status, response = req.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            logger.info(f"  Upload progress: {pct}%")

    video_id = response["id"]
    url = f"https://www.youtube.com/shorts/{video_id}"
    logger.info(f"Uploaded → {url}")
    return video_id, url


def upload_to_youtube(config: dict, video_paths: list, metadata_list: list) -> list:
    """
    Upload Part 1 and Part 2 to YouTube.

    Returns:
        list of dicts: [{part, video_id, url}, ...]
    """
    youtube = _get_service(config)
    cat_id  = config.get("video_category_id", "27")   # 27 = Education
    privacy = config.get("privacy_status",    "public")

    results = []
    for i, (vpath, meta) in enumerate(zip(video_paths, metadata_list), start=1):
        try:
            vid_id, url = _upload_single(youtube, vpath, meta, cat_id, privacy)
            results.append({"part": i, "video_id": vid_id, "url": url})
        except HttpError as e:
            logger.error(f"YouTube API error (Part {i}): {e}")
            results.append({"part": i, "error": str(e)})
        except Exception as e:
            logger.error(f"Upload failed (Part {i}): {e}")
            results.append({"part": i, "error": str(e)})

    return results
