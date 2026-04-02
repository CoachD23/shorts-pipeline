"""Content calendar generation module for YouTube Shorts pipeline."""

from datetime import datetime, timedelta
from pathlib import Path


OPTIMAL_TIMES = [7, 12, 17, 20]  # EST posting hours

WEEKLY_TEMPLATE = {
    1: {"content_type": "Quick Tip", "funnel": "DISC"},
    2: {"content_type": "Drill Demo", "funnel": "DISC"},
    3: {"content_type": "Play Breakdown", "funnel": "MID"},
    4: {"content_type": "Game Film Review", "funnel": "MID"},
    5: {"content_type": "Motivation", "funnel": "$"},
}


def generate_calendar(num_weeks=4, start_date=None, titles=None):
    """Generate content calendar with optimal posting schedule.
    
    Args:
        num_weeks: Number of weeks to generate (default 4)
        start_date: Starting date (defaults to next Monday)
        titles: List of content titles (optional)
    
    Returns:
        Formatted calendar string with posting schedule
    """
    if start_date is None:
        start_date = _get_next_monday()
    elif isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    
    lines = []
    lines.append("=" * 60)
    lines.append("YOUTUBE SHORTS CONTENT CALENDAR")
    lines.append("=" * 60)
    lines.append("")
    
    current_date = start_date
    title_index = 0
    
    for week_num in range(1, num_weeks + 1):
        lines.append(f"WEEK {week_num}")
        lines.append("-" * 40)
        
        for day_offset in range(5):
            day_num = day_offset + 1
            post_date = current_date + timedelta(days=day_offset)
            template = WEEKLY_TEMPLATE[day_num]
            content_type = template["content_type"]
            funnel_tag = template["funnel"]
            
            title = titles[title_index] if titles and title_index < len(titles) else f"Video {title_index + 1}"
            title_index += 1
            
            lines.append(f"  {post_date.strftime('%A, %b %d')}")
            lines.append(f"    Type: {content_type} [{funnel_tag}]")
            lines.append(f"    Title: {title}")
            
            for hour in OPTIMAL_TIMES:
                lines.append(f"      - {hour:02d}:00 EST")
            
            lines.append("")
        
        current_date = current_date + timedelta(days=7)
    
    lines.append("POSTING TIPS")
    lines.append("-" * 40)
    lines.append("• DISC (Discovery): 60% of content")
    lines.append("  - Quick Tip: Short actionable advice")
    lines.append("  - Drill Demo: Technique demonstration")
    lines.append("• MID (Middle Funnel): 30% of content")
    lines.append("  - Play Breakdown: Strategy analysis")
    lines.append("  - Game Film Review: Game footage analysis")
    lines.append("• $ (Monetization): 10% of content")
    lines.append("  - Motivation: Inspirational content")
    lines.append("")
    lines.append("Optimal posting times (EST): 7am, 12pm, 5pm, 8pm")
    lines.append("=" * 60)
    
    return "\n".join(lines)


def save_calendar(output_dir, num_weeks=4, titles=None):
    """Save generated calendar to file.
    
    Args:
        output_dir: Directory to save calendar
        num_weeks: Number of weeks to generate
        titles: List of content titles (optional)
    
    Returns:
        Path to saved file
    """
    output_path = Path(output_dir) / "calendar.txt"
    calendar_text = generate_calendar(num_weeks, titles=titles)
    
    output_path.write_text(calendar_text)
    return output_path


def _get_next_monday():
    """Get next Monday from today.
    
    Returns:
        datetime.date object for next Monday
    """
    today = datetime.now().date()
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    return today + timedelta(days=days_until_monday)
