"""YouTube upload module using Data API v3."""
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from src.retry import retry_with_backoff


SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.force-ssl"]


def build_video_metadata(
    title: str,
    description: str,
    tags: list[str],
    privacy: str | None = None,
) -> dict:
    """Build YouTube API video resource metadata."""
    return {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "17",  # Sports
        },
        "status": {
            "privacyStatus": privacy or "private",
            "selfDeclaredMadeForKids": False,
        },
    }


def get_authenticated_service(credentials_path: str = "credentials.json",
                               token_path: str = "token.json"):
    """Authenticate with YouTube API using OAuth 2.0."""
    creds = None
    token_file = Path(token_path)
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        token_file.write_text(creds.to_json())
    return build("youtube", "v3", credentials=creds)


@retry_with_backoff(max_retries=3, base_delay=2.0, exceptions=(Exception,))
def upload_video(
    video_path: str,
    title: str,
    description: str,
    tags: list[str],
    privacy: str = "private",
    thumbnail_path: str | None = None,
    credentials_path: str = "credentials.json",
    token_path: str = "token.json",
) -> str:
    """Upload a video to YouTube. Returns video ID."""
    youtube = get_authenticated_service(credentials_path, token_path)
    metadata = build_video_metadata(title, description, tags, privacy)
    media = MediaFileUpload(
        video_path, mimetype="video/mp4", resumable=True,
        chunksize=10 * 1024 * 1024,
    )
    request = youtube.videos().insert(
        part="snippet,status", body=metadata, media_body=media,
    )
    response = None
    while response is None:
        _, response = request.next_chunk()
    video_id = response["id"]
    if thumbnail_path and Path(thumbnail_path).exists():
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_path, mimetype="image/jpeg"),
        ).execute()
    return video_id
