from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, EmailStr, conint, field_validator
import phonenumbers


class PostBase(BaseModel):
    title: str
    content: str
    published: bool = True
    # rating: Optional[int] = None


class PostCreate(PostBase):
    pass


class UserOut(BaseModel):
    id: int
    email: EmailStr
    phone: str
    created_at: datetime

    class Config:
        from_attributes = True


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


class UserCreate(BaseModel):
    name: str
    surname: Optional[str] = None
    email: EmailStr
    phone: str
    password: str
    profile_picture: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None  # Expecting 'M', 'F', or 'O'
    role: Optional[str] = "user"
    is_active: Optional[bool] = True
    two_factor_enabled: Optional[bool] = False
    is_premium: Optional[bool] = False

    @field_validator("phone")
    def validate_phone(cls, value):
        try:
            parsed = phonenumbers.parse(value)
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError("Invalid phone number")
        except phonenumbers.NumberParseException:
            raise ValueError("Invalid phone number format")
        
        return value

    
class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[int] = None


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