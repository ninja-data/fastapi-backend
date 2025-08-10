from fastapi import APIRouter, Depends, status, HTTPException, Response
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..utils import security_utils, story_utils
from ..services import azure_storage_service

from .. import database , schemas, models, oauth2

router = APIRouter(
    prefix="/login",
    tags=['Authentication']
)

@router.post('/', response_model=schemas.TokenWithUser)
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    # username == email

    user = db.query(models.User).filter(models.User.email == user_credentials.username).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")
    
    if not security_utils.verify(user_credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")
    
    access_token = oauth2.create_access_token(data = {"user_id": user.id})

    user.profile_picture_url = azure_storage_service.add_sas_token(user.profile_picture_url)

    # Remove expired stories from the list
    user.stories = story_utils.filter_expired_stories(user.stories)

    # Append SAS token to each story's media_url
    for story in user.stories:
        story.media_url = azure_storage_service.add_sas_token(story.media_url)


    return {"access_token": access_token, 
            "token_type": "bearer",
            "user":  user
    }
