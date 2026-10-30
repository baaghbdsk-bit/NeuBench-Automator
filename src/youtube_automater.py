import os
import sys
import base64
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

# Ensure UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger("YouTubeAutomater")

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtubepartner"
]

class YouTubeAutomater:
    """
    Automates uploading YouTube Shorts and associated .srt Closed Captions
    using the YouTube Data API v3.
    """

    def __init__(self, token_path: Optional[str] = None):
        self.base_dir = Path(__file__).resolve().parent.parent
        self.token_path = Path(token_path) if token_path else self.base_dir / "youtube_token.json"
        self.service = None
        self._initialize_service()

    def _initialize_service(self):
        """Initializes YouTube API client using saved token or GitHub secret base64 env var."""
        creds = None

        # Check for base64 encoded token in environment (for CI/CD GitHub Actions)
        env_token_b64 = os.environ.get("YOUTUBE_TOKEN_BASE64")
        if env_token_b64:
            try:
                token_json = base64.b64decode(env_token_b64).decode("utf-8")
                token_data = json.loads(token_json)
                creds = Credentials.from_authorized_user_info(token_data, SCOPES)
                logger.info("Loaded YouTube credentials from YOUTUBE_TOKEN_BASE64 environment variable.")
            except Exception as e:
                logger.warning(f"Failed to load credentials from YOUTUBE_TOKEN_BASE64: {e}")

        # Fallback to local youtube_token.json file
        if not creds and self.token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)
                logger.info(f"Loaded YouTube credentials from {self.token_path}")
            except Exception as e:
                logger.warning(f"Failed to load credentials from file {self.token_path}: {e}")

        if creds:
            if creds.expired and creds.refresh_token:
                try:
                    logger.info("Refreshing expired YouTube access token...")
                    creds.refresh(Request())
                    # If we have a local token path, persist the updated token
                    if self.token_path.parent.exists():
                        with open(self.token_path, "w", encoding="utf-8") as f:
                            f.write(creds.to_json())
                except Exception as e:
                    logger.error(f"Failed to refresh YouTube access token: {e}")
                    creds = None

        if creds and creds.valid:
            self.service = build("youtube", "v3", credentials=creds)
            logger.info("YouTube API client initialized successfully.")
        else:
            logger.warning(
                "YouTube credentials not found or invalid. "
                "Run 'python scripts/login_youtube.py' to generate your youtube_token.json."
            )

    @property
    def is_authenticated(self) -> bool:
        return self.service is not None

    def upload_short(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: Optional[List[str]] = None,
        privacy_status: str = "public",
        srt_path: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Uploads a vertical Short to YouTube and attaches CC subtitles if provided.
        """
        if not self.is_authenticated:
            logger.error("Cannot upload video: YouTube service is not authenticated.")
            return None

        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return None

        # Guarantee #Shorts is present in title/tags for YouTube Shorts classification
        if "#Shorts" not in title and "#shorts" not in title:
            title = f"{title} #Shorts"

        default_tags = ["Shorts", "AI", "MachineLearning", "Python", "DeepLearning", "Tech"]
        if tags:
            merged_tags = list(set(tags + default_tags))
        else:
            merged_tags = default_tags

        body = {
            "snippet": {
                "title": title[:100],  # Max 100 chars
                "description": description,
                "tags": merged_tags,
                "categoryId": "28"  # Science & Technology
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False
            }
        }

        media = MediaFileUpload(
            video_path,
            mimetype="video/mp4",
            resumable=True,
            chunksize=1024 * 1024 * 5
        )

        try:
            logger.info(f"Uploading '{title}' to YouTube ({privacy_status})...")
            request = self.service.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    print(f"[YouTube Upload] Progress: {progress}%", end="\r")

            video_id = response.get("id")
            video_url = f"https://youtube.com/shorts/{video_id}"
            logger.info(f"Successfully uploaded YouTube Short: {video_url}")

            # Upload Subtitles / Closed Captions if provided
            if srt_path and os.path.exists(srt_path):
                self._upload_captions(video_id, srt_path)

            return {
                "video_id": video_id,
                "url": video_url,
                "title": title
            }

        except Exception as e:
            logger.error(f"YouTube upload failed: {e}")
            return None

    def _upload_captions(self, video_id: str, srt_path: str, language: str = "en", name: str = "English"):
        """Attaches an .srt subtitle file to the uploaded video."""
        try:
            logger.info(f"Uploading subtitle track ({srt_path}) to video {video_id}...")
            media = MediaFileUpload(srt_path, mimetype="text/plain")
            caption_body = {
                "snippet": {
                    "videoId": video_id,
                    "language": language,
                    "name": name,
                    "isDraft": False
                }
            }
            self.service.captions().insert(
                part="snippet",
                body=caption_body,
                media_body=media
            ).execute()
            logger.info("Successfully uploaded Closed Captions (.srt) track to YouTube!")
        except Exception as e:
            logger.warning(f"Caption upload error (video is still uploaded): {e}")
