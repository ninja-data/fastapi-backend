import json
import logging
from sqlite3 import IntegrityError
from fastapi import Response, UploadFile, status, HTTPException, Depends, APIRouter, Form, File
from pydantic import ValidationError
from sqlalchemy.sql import func
from sqlalchemy.orm import Session
from typing import List, Optional

from ..utils import file_utils
from ..services import azure_storage_service

from .. import models, schemas, oauth2
from ..database import engine, get_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger  = logging.getLogger(__name__)

router = APIRouter(
    prefix="/posts",
    tags=['Posts']
)

# TODO add post picture

@router.get("/", response_model=List[schemas.PostResponse])
async def get_posts(
    db: Session = Depends(get_db), 
    current_user: dict = Depends(oauth2.get_current_user),
    limit: int = 10, skip: int = 0, search: Optional[str] = ""):
    # Show own posts only
    # posts = db.query(models.Post).filter(models.Post.user_id == current_user.id).all()

    # posts = db.query(models.Post, func.count(models.Vote.post_id).label("votes")).join(
    #     models.Vote, models.Vote.post_id == models.Post.id, isouter=True).group_by(models.Post.id).filter(models.Post.title.contains(search)).limit(limit).offset(skip).all()


    try:
        posts = db.query(models.Post).filter(models.Post.content.contains(search)).limit(limit).offset(skip).all()

        for post in posts:
            if post.media_url:
                sas_token = azure_storage_service.create_service_sas_container()
                post.media_url = f"{post.media_url}?{sas_token}"
    except Exception as e:
        logger.error(f"Failed to fetch pets: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch pets")
    
    return posts



@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.PostResponse)
async def create_posts(
    # post: schemas.PostCreate, 
    post: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db), 
    current_user: dict = Depends(oauth2.get_current_user)):
    
    try:
        # TODO add user data from current_user
        post_data = json.loads(post.replace("\\", ""))
        post = schemas.PostCreate(user_id = current_user.id, **post_data)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=str(e.errors()),)
    
    new_post = models.Post(user_id=current_user.id, **post.model_dump())
    
    if file and file.size:
        try:
            media_url = file_utils.upload_profile_picture(file)
            new_post.media_url = media_url
        except IntegrityError as e:
            logger.error(f"Integrity error during file upload: {e}")

    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    if new_post.media_url:
        sas_token = azure_storage_service.create_service_sas_container()
        new_post.media_url = f"{new_post.media_url}?{sas_token}"

    return new_post


@router.get("/{id}", response_model=schemas.PostResponse)
async def get_post(id: int, db: Session = Depends(get_db), current_user: dict = Depends(oauth2.get_current_user)):

    # post = db.query(models.Post, func.count(models.Vote.post_id).label("votes")).join(
    #         models.Vote, models.Vote.post_id == models.Post.id, isouter=True).group_by(models.Post.id).filter(models.Post.id == id).first()

    post = db.query(models.Post).filter(models.Post.id == id).first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {id} was not found")
        # response.status_code = status.HTTP_404_NOT_FOUND
        # return {'message': f"post with id: {id} was not found"}

    if post.media_url:
        sas_token = azure_storage_service.create_service_sas_container()
        post.media_url = f"{post.media_url}?{sas_token}"

    return post


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(id: int, db: Session = Depends(get_db), current_user: dict = Depends(oauth2.get_current_user)):
    # TODO add removing photo from storage account
    post_query = db.query(models.Post).filter(models.Post.id == id)

    post = post_query.first()

    if post == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {id} does not exist")
    
    if post.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to perform requested action")
    
    post_query.delete(synchronize_session=False)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{id}", response_model=schemas.PostResponse)
async def update_post(id: int, updated_post: schemas.PostCreate, db: Session = Depends(get_db), current_user: dict = Depends(oauth2.get_current_user)):
    
    post = db.query(models.Post).filter(models.Post.id == id).first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Post with id {id} does not exist")
    
    if post.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to perform requested action")

    # Dynamically update fields from the request payload
    for field, value in updated_post.model_dump(exclude_unset=True).items():
        setattr(post, field, value)

    # Commit changes to the database
    db.commit()

    # Return the updated post
    return post
