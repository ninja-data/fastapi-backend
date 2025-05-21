from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, EmailStr, conint, field_serializer, field_validator, Field, HttpUrl
import phonenumbers
from .utils.security_utils import validate_phone_number
from .services.azure_storage_service import add_sas_token

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

class UserRelationshipStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    BLOCKED = "blocked"


class StoryBase(BaseModel):
    pet_id: int
    media_url: Optional[HttpUrl] = None
    media_type: Optional[str] = None
    content: Optional[str] = None
    expires_at: Optional[datetime] = None

class StoryCreate(StoryBase):
    pass

class StoryResponse(StoryBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attribute = True


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
    private_account: Optional[bool] = Field(False, title="Private Account")
    is_premium: bool = Field(False, title="Premium User")

    @field_validator("phone")
    def validate_phone(cls, value: str) -> str:
        return validate_phone_number(value) 
    
    @field_serializer("profile_picture_url")
    def serialize_profile_picture_url(self, value: str) -> Optional[str]:
        return add_sas_token(value)
    
    class Config:
        from_attribures = True

class UserRelationshipBase(BaseModel):
    receiver_id: int

class UserRealationshipCreate(UserRelationshipBase):
    pass

class UserRelationshipResponse(UserRelationshipBase):
    requester_id: int
    status: UserRelationshipStatus
    updated_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, title="Password")

# TODO remove stories from user and add it to pet
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
    stories: List[StoryResponse] = []
    follow_status: Optional[UserRelationshipStatus] = None

    class Config:
        # Allows automatic conversion from ORM models
        from_attributes = True

    # TODO Add for all URLs
    @field_serializer("profile_picture_url")
    def serialize_profile_picture_url(self, value: str) -> Optional[str]:
        return add_sas_token(value)

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, title="First Name", min_length=1)
    surname: Optional[str] = Field(None, title="Last Name")
    # email: Optional[EmailStr] = None
    # phone: Optional[str] = None
    # profile_picture_url: Optional[str] = None
    bio: Optional[str] = Field(None, title="Short Biography", max_length=500)
    location: Optional[str] = None
    date_of_birth: Optional[date] = Field(None, title="Date of Birth")
    gender: Optional[Gender] = None
    role: Optional[Role] = None
    is_active: Optional[bool] = None
    private_account: Optional[bool] = None
    is_premium: Optional[bool] = None

    class Config:
        orm_mode = True
        

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


class BreedBase(BaseModel):
    id: int
    name: str
    image_url: Optional[str] = None
    pet_type_id: int

    class Config:
        from_attribures = True


class BreedResponse(BreedBase):
    count: int

    class Config:
        from_attribures = True


class PetBase(BaseModel):
    name: str
    animal_type_id: int
    pet_type_id: int
    breed_1_id: int
    breed_2_id: Optional[int] = None
    gender: Optional[str] = None  # Expecting 'M', 'F', or 'O'
    profile_picture_url: Optional[str] = None
    bio: Optional[str] = None
    date_of_birth: Optional[date] = None
    is_active: Optional[bool] = True

    class Config:
        from_attributes = True


class PetCreate(PetBase):
    pass

class PetResponse(PetBase):
    id: int
    user_id: int
    # user: UserBase
    user: UserResponse
    breed_1: BreedBase
    breed_2: Optional[BreedBase] = None
    is_following: Optional[bool] = False

    class Config:
        from_attributes = True


class PetUpdate(BaseModel):
    name: Optional[str] = None
    animal_type_id: Optional[int] = None
    pet_type_id: Optional[int] = None
    breed_1_id: Optional[int] = None
    breed_2_id: Optional[int] = None
    gender: Optional[str] = None  # 'M', 'F', or 'O'
    # profile_picture_url: Optional[str] = None
    bio: Optional[str] = None
    date_of_birth: Optional[date] = None
    is_active: Optional[bool] = None

    class Config:
        from_attributes = True



# TODO improve it 
class UserPetsResponse(UserResponse):
    pets: List[PetBase]

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
    user: UserBase
    pet: PetBase

    class Config:
        from_attributes = True


class AnimalTypeResponse(BaseModel):
    id: int
    name: str
    image_url: Optional[str] = None
    count: int

    class Config:
        from_attribute = True

    
class PetTypesResponse(BaseModel):
    id: int
    name:str
    image_url: Optional[str] = None
    animal_type_id: int
    count: int

    class Config:
        from_attribure = True


class CommentBase(BaseModel):
    post_id: int
    # user_id: Optional[int] = None
    content: str

class CommentCreate(CommentBase):
    pass

class CommentResponse(CommentBase):
    id: int
    user_id: int
    created_at: datetime
    user: UserBase

    class Config:
        from_attribure = True


class NotificationResponse(BaseModel):
    user_id: int
    post_id: int
    created_at: datetime
    user_photo_url: Optional[str]  # URL of the user's profile picture
    user_name: str
    post_photo_url: Optional[str]  # URL of the post's media
    type: str  # Type of notification: comment, like, etc.
    comment: Optional[str]  # The content of the comment, if it's a comment notification

    class Config:
        from_attribure = True
