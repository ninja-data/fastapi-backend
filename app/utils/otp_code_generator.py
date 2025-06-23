import hmac
import hashlib
import time
from app.config import settings

def get_time_window(minutes=20) -> int:
    return int(time.time() // (minutes * 60))

def generate_code(email: str, minutes_window: int = 20) -> str:
    """
    Generates a deterministic verification code for the given email and time window.
    
    - `email`: email address to generate code for
    - `minutes_window`: time window duration in minutes
    - `digits`: number of digits for the verification code
    - `time_provider`: optional function to override current time (for testing)
    """
    time_window = get_time_window(minutes_window)
    message = f"{email}:{time_window}".encode()
    secret = settings.secret_key.encode()

    digest = hmac.new(secret, message, hashlib.sha256).hexdigest()
    return str(int(digest[:6], 16) % 10000).zfill(4)
