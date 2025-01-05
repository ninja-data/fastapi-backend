import json
import logging
from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status, Form
from pydantic import ValidationError
from sqlalchemy.orm import Session
from sqlite3 import IntegrityError
from typing import List

from ..database import get_db

from .. import schemas, models, oauth2
from ..utils import file_utils
from ..services import azure_storage_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger  = logging.getLogger(__name__)

router = APIRouter(
    prefix="/stories",
    tags=['Story']
)

# TODO add Stories list to user also

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.StoryResponse)
async def create_story(
    story: str = Form(...),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(oauth2.get_current_user)
):
    try:
        story_data = json.loads(story.replace("\\", ""))
        story = schemas.StoryCreate(**story_data)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e.errors())
        )

    new_story = models.Story(user_id=current_user.id, **story.model_dump())

    if file and file.size:
        try:
            media_url = file_utils.upload_profile_picture(file)
            new_story.media_url = media_url
        except IntegrityError as e:
            logger.error(f"Integrity error during file upload: {e}")

    db.add(new_story)
    db.commit()
    db.refresh(new_story)

    if new_story.media_url:
        sas_token = azure_storage_service.create_service_sas_container()
        new_story.media_url = f"{new_story.media_url}?{sas_token}"

    return new_story


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_story(
    id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(oauth2.get_current_user),
):
    story_query = db.query(models.Story).filter(models.Story.id == id)
    story = story_query.one_or_none()

    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Story with id: {id} does not exist"
        )
    
    if story.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform this action"
        )
    
    story_query.delete(synchronize_session=False)
    db.commit()

    return None

# TODO add get status
