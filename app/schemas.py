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
    profile_picture: Optional[str] = None
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

class UserOut(BaseModel):
    id: int
    name: str
    surname: Optional[str]
    email: EmailStr
    phone: str
    created_at: datetime
    profile_picture: Optional[str]
    bio: Optional[str]
    location: Optional[str]
    role: Role
    is_active: bool
    is_premium: bool

    class Config:
        # Allows automatic conversion from ORM models
        from_attributes = True


class PostBase(BaseModel):
    title: str
    content: str
    published: bool = True
    # rating: Optional[int] = None


class PostCreate(PostBase):
    pass


# class UserOut(BaseModel):
#     id: int
#     email: EmailStr
#     phone: str
#     created_at: datetime

#     class Config:
#         from_attributes = True


class Post(PostBase):
    id: int
    created_at: datetime
    owner_id: int
    owner: UserOut

    class Config:
        from_attributes = True


class PostOut(BaseModel):
    Post: Post
    votes: int

    class Config:
        from_attributes = True

# class UserCreate(BaseModel):
#     name: str
#     surname: Optional[str] = None
#     email: EmailStr
#     phone: str
#     password: str
#     profile_picture: Optional[str] = None
#     bio: Optional[str] = None
#     location: Optional[str] = None
#     date_of_birth: Optional[date] = None
#     gender: Optional[str] = None  # Expecting 'M', 'F', or 'O'
#     role: Optional[str] = "user"
#     is_active: Optional[bool] = True
#     two_factor_enabled: Optional[bool] = False
#     is_premium: Optional[bool] = False

#     @field_validator("phone")
#     def validate_phone(cls, value):
#         try:
#             parsed = phonenumbers.parse(value)
#             if not phonenumbers.is_valid_number(parsed):
#                 raise ValueError("Invalid phone number")
#         except phonenumbers.NumberParseException:
#             raise ValueError("Invalid phone number format")
        
#         return value

    
# class UserLogin(BaseModel):
#     email: EmailStr
#     password: str


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: Optional[int] = None

class TokenWithUser(Token):
    user: UserOut


class Vote(BaseModel):
    post_id: int
    dir: conint(ge=0, le=1)

# TODO Separate the Pet class by logic (Post)
class PetCreate(BaseModel):
    name: str
    animal_type: str
    pet_type: str
    breed_1: str
    breed_2: Optional[str] = None
    gender: Optional[str] = None  # Expecting 'M', 'F', or 'O'
    profile_picture: Optional[str] = None
    bio: Optional[str] = None
    date_of_birth: Optional[date] = None
    is_active: Optional[bool] = True


class PetOut(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True
