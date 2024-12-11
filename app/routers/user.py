import json
import logging
from fastapi import Body, File, Form, UploadFile, status, HTTPException, Depends, APIRouter
from pydantic import ValidationError
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..utils import security_utils, file_utils
from ..services import azure_storage_service
from ..database import get_db

from .. import models, schemas, oauth2


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger  = logging.getLogger(__name__)


router = APIRouter(
    prefix="/users",
    tags=['Users']
)

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

    # hash the password  - user.password
    user.password = security_utils.hash(user.password)

    # Check if the phone already exists
    existing_user_phone = db.query(models.User).filter(models.User.phone == user.phone).first()
    if existing_user_phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Phone number {user.phone} already exists")
    
    # Check if the email already exists
    existing_user_email = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Email {user.email} already exists")

    new_user = models.User(**user.model_dump())

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
    
    if new_user.profile_picture_url:
        sas_token = azure_storage_service.create_service_sas_container()
        new_user.profile_picture_url += "?" + sas_token

    return new_user


@router.get("/{id}", response_model=schemas.UserResponse)
def get_user(id: int, db: Session = Depends(get_db),  current_user: dict = Depends(oauth2.get_current_user),):

    user = db.query(models.User).filter(models.User.id == id).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=f"User with id: {id} does not exist")
    
    if user.profile_picture_url:
        sas_token = azure_storage_service.create_service_sas_container()
        user.profile_picture_url += "?" + sas_token

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
    
    sas_token = azure_storage_service.create_service_sas_container()
    user.profile_picture_url += "?" + sas_token

    return user

# TODO add delete and put 
