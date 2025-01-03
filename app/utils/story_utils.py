import pytz
from datetime import datetime
from typing import List

# Function to get the current time in Baku time zone
def get_baku_time() -> datetime:
    baku_tz = pytz.timezone("Asia/Baku")
    return datetime.now(baku_tz)

# Function to remove expired stories
def filter_expired_stories(stories: List) -> List:
    current_time_baku = get_baku_time()
    return [story for story in stories if story.expires_at > current_time_baku]
