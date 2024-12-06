from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, EmailStr, conint, field_validator, Field
import phonenumbers
from .utils import validate_phone_number

# TODO separate models by files
# project/
# ├── models/
# │   ├── __init__.py       # Optional: Makes the folder a package
# │   ├── user.py           # Contains UserBase, UserCreate, UserOut
# │   ├── post.py           # Contains PostBase, PostCreate, PostOut
# │   ├── token.py          # Contains Token, TokenData, TokenWithUser
# │   ├── pet.py            # Contains PetCreate, PetOut
# │   ├── vote.py           # Contains Vote
# │   ├── enums.py          # Contains Gender and Role Enums
# ├── utils/
# │   ├── __init__.py       # Optional
# │   ├── validators.py     # Custom validators (e.g., validate_phone_number)
# ├── routers/
# │   ├── __init__.py       # Optional
# │   ├── auth.py           # Contains login and token generation logic
# │   ├── user.py           # Contains user CRUD operations
# │   ├── post.py           # Contains post CRUD operations
# ├── config.py             # Configuration settings
# ├── main.py               # Entry point



from enum import Enum

class Gender(str, Enum):
    MALE = "M"
    FEMALE = "F"
    OTHER = "O"

class Role(str, Enum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"


class UserBase(BaseModel):
    name: str = Field(..., title="First Name", min_length=1)
    surname: Optional[str] = Field(None, title="Last Name")
    email: EmailStr
    phone: str
    profile_picture_url: Optional[str] = None
    bio: Optional[str] = Field(None, title="Short Biography", max_length=500)
    location: Optional[str] = None
    date_of_birth: Optional[date] = Field(None, title="Date of Birth")
    gender: Optional[Gender] = None
    role: Optional[Role] = Role.USER
    is_active: bool = Field(True, title="Active Status")
    two_factor_enabled: bool = Field(False, title="Two Factor Authentication")
    is_premium: bool = Field(False, title="Premium User")

    @field_validator("phone")
    def validate_phone(cls, value: str) -> str:
        return validate_phone_number(value) 

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, title="Password")

class UserResponse(BaseModel):
    id: int
    name: str
    surname: Optional[str]
    email: EmailStr
    phone: str
    created_at: datetime
    profile_picture_url: Optional[str]
    bio: Optional[str]
    location: Optional[str]
    role: Role
    is_active: bool
    is_premium: bool

    class Config:
        # Allows automatic conversion from ORM models
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: Optional[int] = None

class TokenWithUser(Token):
    user: UserResponse

# TODO fix a wavy line
class Like(BaseModel):
    post_id: int
    dir: conint(ge=0, le=1)



class PetBase(BaseModel):
    name: str
    animal_type: str
    pet_type: str
    breed_1: str
    breed_2: Optional[str] = None
    gender: Optional[str] = None  # Expecting 'M', 'F', or 'O'
    profile_picture_url: Optional[str] = None
    bio: Optional[str] = None
    date_of_birth: Optional[date] = None
    is_active: Optional[bool] = True

class PetCreate(PetBase):
    pass

class PetResponse(PetBase):
    pass

    class Config:
        from_attributes = True


class PostBase(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    visibility: Optional[str] = "public"
    tags: Optional[str] = None
    location: Optional[str] = None
    parent_post_id: Optional[int] = None

class PostCreate(PostBase):
    # user_id: int
    pet_id: Optional[int] = None

class PostResponse(PostBase):
    id: int
    user_id: int
    pet_id: Optional[int] = None
    likes_count: int
    comments_count: int
    is_active: bool
    created_at: datetime
    edited_at: Optional[datetime] = None

    class Config:
        from_attributes = True
