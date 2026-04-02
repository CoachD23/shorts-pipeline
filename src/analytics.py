"""YouTube Analytics — pull video performance data."""
from datetime import datetime, timedelta


def build_analytics_request(
    youtube_analytics,
    channel_id: str,
    video_id: str = "",
    days: int = 28,
) -> dict:
    """Build a YouTube Analytics API request for video metrics.

    Args:
        youtube_analytics: Authenticated YouTube Analytics API service.
        channel_id: YouTube channel ID.
        video_id: Specific video ID (empty = all videos).
        days: Number of days to look back.

    Returns:
        Analytics response dict with rows of metric data.
    """
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    kwargs = {
        "ids": f"channel=={channel_id}",
        "startDate": start_date,
        "endDate": end_date,
        "metrics": "views,estimatedMinutesWatched,averageViewDuration,likes,shares,subscribersGained",
        "dimensions": "video",
        "sort": "-views",
        "maxResults": 25,
    }

    if video_id:
        kwargs["filters"] = f"video=={video_id}"
        kwargs.pop("dimensions", None)
        kwargs.pop("sort", None)
        kwargs.pop("maxResults", None)

    return youtube_analytics.reports().query(**kwargs).execute()


def format_analytics_report(response: dict, title: str = "Channel Analytics") -> str:
    """Format analytics response into readable text report.

    Args:
        response: YouTube Analytics API response.
        title: Report title.

    Returns:
        Formatted text report.
    """
    lines = [f"📊 {title}", "=" * 50]

    headers = [col["name"] for col in response.get("columnHeaders", [])]
    rows = response.get("rows", [])

    if not rows:
        lines.append("No data available for this period.")
        return "\n".join(lines)

    # Single video report (no video dimension)
    if "video" not in headers and rows:
        row = rows[0]
        metric_names = {
            "views": "👀 Views",
            "estimatedMinutesWatched": "⏱️ Watch Time (min)",
            "averageViewDuration": "📏 Avg Duration (sec)",
            "likes": "👍 Likes",
            "shares": "🔄 Shares",
            "subscribersGained": "📈 New Subscribers",
        }
        for header, value in zip(headers, row):
            name = metric_names.get(header, header)
            if isinstance(value, float):
                lines.append(f"  {name}: {value:,.1f}")
            else:
                lines.append(f"  {name}: {value:,}")
        return "\n".join(lines)

    # Multi-video report
    video_idx = headers.index("video") if "video" in headers else None
    for i, row in enumerate(rows[:10], 1):
        vid = row[video_idx] if video_idx is not None else "—"
        metrics = {h: v for h, v in zip(headers, row) if h != "video"}
        views = metrics.get("views", 0)
        watch_min = metrics.get("estimatedMinutesWatched", 0)
        avg_dur = metrics.get("averageViewDuration", 0)
        likes = metrics.get("likes", 0)
        lines.append(f"\n  #{i} Video: {vid}")
        lines.append(f"     👀 {views:,} views | ⏱️ {watch_min:,.0f} min | 📏 {avg_dur:.0f}s avg | 👍 {likes:,}")

    return "\n".join(lines)


def get_analytics(
    channel_id: str,
    video_id: str = "",
    days: int = 28,
    credentials_path: str = "credentials.json",
    token_path: str = "token.json",
) -> str:
    """Pull analytics and return formatted report.

    Requires YouTube Analytics API to be enabled in Google Cloud Console
    and the yt-analytics.readonly scope.
    """
    from src.upload import get_authenticated_service
    from googleapiclient.discovery import build as build_service
    from google.oauth2.credentials import Credentials
    from pathlib import Path

    # Load existing credentials
    token_file = Path(token_path)
    if not token_file.exists():
        return "❌ Not authenticated. Run pipeline with --upload first to set up OAuth."

    creds = Credentials.from_authorized_user_file(str(token_file))
    youtube_analytics = build_service("youtubeAnalytics", "v2", credentials=creds)

    response = build_analytics_request(youtube_analytics, channel_id, video_id, days)
    title = f"Video {video_id} Analytics" if video_id else f"Channel Analytics (last {days} days)"
    return format_analytics_report(response, title)
