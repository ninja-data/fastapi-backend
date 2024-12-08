from passlib.context import CryptContext
import phonenumbers


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash(password: str):
    return pwd_context.hash(password)


def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def validate_phone_number(phone: str) -> str:
    """
    Validates a phone number using the phonenumbers library.
    Raises ValueError if the number is invalid.
    """
    try:
        parsed = phonenumbers.parse(phone)
        if not phonenumbers.is_valid_number(parsed):
            raise ValueError("Invalid phone number")
    except phonenumbers.NumberParseException:
        raise ValueError("Invalid phone number format")
    return phone
