import json
import logging
from typing import List
from datetime import datetime, timezone, timedelta
from datetime import datetime
from fastapi import Body, File, Form, Query, UploadFile, status, HTTPException, Depends, APIRouter
from pydantic import ValidationError, EmailStr
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from ..utils import security_utils, file_utils, story_utils, otp_code_generator
from ..services import azure_storage_service, email_service
from ..database import get_db

from .. import models, schemas, oauth2

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger  = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=['Users']
)

def is_user_following(db: Session, current_user_id: int, target_user_id: int) -> bool:
    """
    Check if the current user is following the target user.

    :param db: Database session
    :param current_user_id: ID of the current user
    :param target_user_id: ID of the target user
    :return: True if following, False otherwise
    """
    return db.query(models.Follow).filter(
        models.Follow.follower_id == current_user_id,
        models.Follow.following_id == target_user_id
    ).first() is not None

# TODO Do PREDICATE PUSHDOWN & renove adding sas token explicitly
def process_user_stories(users, include_expired):
    """
    Process and filter expired stories, then add SAS token to each story's media URL.
    """
    for user in users:
        if not include_expired:
            user.stories = story_utils.filter_expired_stories(user.stories)
        for story in user.stories:
            story.media_url = azure_storage_service.add_sas_token(story.media_url)
    return users


@router.post("/send-verification-email", status_code=status.HTTP_200_OK)
async def send_verification_email(email: EmailStr = Form(...)):
    try:
        otp_code = otp_code_generator.generate_code(email)
        email_service.send_verification_email(email, otp_code)
        return {"message": f"Verification email sent successfully {otp_code}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to send verification email")


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.UserResponse)
async def create_user(
    user: str = Form(...), # Receive user data as a JSON string
    file: UploadFile = File(None), # Allow profile picture upload as part of the request
    db: Session = Depends(get_db)
    ):

    try:
    # TODO for all 
        user_data = json.loads(user.replace("\\", ""))
        user = schemas.UserCreate(**user_data)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e.errors()),
        )

    otp_code = otp_code_generator.generate_code(user.email)
    if user.otp_code != otp_code:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"Invalid or expired OTP code {user.otp_code}")
    
    # hash the password  - user.password
    user.password = security_utils.hash(user.password)

    # Check if the phone already exists
    existing_user_phone = db.query(models.User).filter(models.User.phone == user.phone).first()
    if user.phone and existing_user_phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Phone number {user.phone} already exists")
    
    # Check if the email already exists
    existing_user_email = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Email {user.email} already exists")

    new_user = models.User(**user.model_dump(exclude={"otp_code"}))

    if file and file.size:
        try:
            picture_url = file_utils.upload_profile_picture(file)
            new_user.profile_picture_url = picture_url
        except IntegrityError as e:
            logger.error(f"Integrity error during file upload: {e}")

    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User creation failed due to a database integrity issue"
        )

    # new_user.profile_picture_url = azure_storage_service.add_sas_token(new_user.profile_picture_url)

    return new_user


@router.get("/", response_model=List[schemas.UserResponse])
def get_users(
    has_stories: bool = Query(None, description="Filter users who have stories"),
    include_expired: bool = Query(False, description="Include expired stories"),
    limit: int = Query(100, description="Limit the number of users returned"),
    offset: int = Query(0, description="Offset for pagination"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(oauth2.get_current_user)
) -> List[schemas.UserResponse]:
    """
    Fetch all users, optionally filtering by criteria and processing their data.
    """
    def get_filtered_users(query, has_stories, include_expired, baku_tz):
        if has_stories:
            query = query.join(models.Story).options(joinedload(models.User.stories)).distinct()
        if not include_expired:
            query = query.filter(models.Story.expires_at > datetime.now(timezone.utc).astimezone(baku_tz))
        return query.offset(offset).limit(limit).all()

    baku_tz = timezone(timedelta(hours=4))
    query = (
        db.query(
            models.User, 
            models.UserRelationship.status.label("follow_status")
        )
        .outerjoin(
            models.UserRelationship,
            (models.UserRelationship.requester_id == current_user.id) & (models.UserRelationship.receiver_id == models.User.id)
        )
    )
    users_and_follow_status = get_filtered_users(query, has_stories, include_expired, baku_tz)

    users_with_follow_status = []
    for user, follow_status in users_and_follow_status:
        user.follow_status = follow_status
        users_with_follow_status.append(user)


    return process_user_stories(users_with_follow_status, include_expired)


@router.get("/{id}", response_model=schemas.UserResponse)
def get_user(id: int, db: Session = Depends(get_db),  current_user: dict = Depends(oauth2.get_current_user),):

    # Query user with follow status in one query
    user_and_follow_status = (
        db.query(
            models.User,
            models.UserRelationship.status.label("follow_status")
        )
        .outerjoin(
            models.UserRelationship, 
            (models.UserRelationship.requester_id == current_user.id) & (models.UserRelationship.receiver_id == id)
        )
        .filter(models.User.id == id)
        .first()
    )

    if not user_and_follow_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id: {id} does not exist"
        )
    
    user, user.follow_status = user_and_follow_status  # Unpacking query result

    # Remove expired stories from the list
    user.stories = story_utils.filter_expired_stories(user.stories)

    # Append SAS token to each story's media_url
    for story in user.stories:
        story.media_url = azure_storage_service.add_sas_token(story.media_url)

    return user
 
# TODO separate folder for user's imagie
@router.post("/{id}/upload-profile-picture", response_model=schemas.UserResponse)
async def uplaod_profile_picture(id: int, 
                                 file: UploadFile = File(...), 
                                 db: Session = Depends(get_db), 
                                 current_user: dict = Depends(oauth2.get_current_user),):
    
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=f"User with id: {id} does not exist")
    
    if user.id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to perform requested action")
    
    try:
        picture_url = file_utils.upload_profile_picture(file)
        user.profile_picture_url = picture_url
        db.commit()
        db.refresh(user)
    except Exception as e:
        logger.error(f"File upload error for user {id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to upload profile picture"
        ) 
    
    # user.profile_picture_url = azure_storage_service.add_sas_token(user.profile_picture_url)

    # Remove expired stories from the list
    user.stories = story_utils.filter_expired_stories(user.stories)

    # Append SAS token to each story's media_url
    for story in user.stories:
        story.media_url = azure_storage_service.add_sas_token(story.media_url)

    return user


@router.put("/{id}", response_model=schemas.UserResponse)
async def update_user(
    id: int,
    user_update: schemas.UserUpdate,  
    db: Session = Depends(get_db),
    current_user: dict = Depends(oauth2.get_current_user),
):
    user = db.query(models.User).filter(models.User.id == id).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id {id} not found")

    if user.id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to update this user")

    for field, value in user_update.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Update failed due to integrity constraint")

    return user


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(oauth2.get_current_user),
):
    user = db.query(models.User).filter(models.User.id == id).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id {id} not found")

    if user.id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to delete this user")

    db.delete(user)
    db.commit()

    return None
