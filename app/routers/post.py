import json
import logging
from sqlite3 import IntegrityError
from fastapi import Response, UploadFile, status, HTTPException, Depends, APIRouter, Form, File, Query
from pydantic import ValidationError
from sqlalchemy.sql import func
from sqlalchemy import func, desc, asc
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


@router.get("/", response_model=List[schemas.PostResponse])
async def get_posts(
    db: Session = Depends(get_db), 
    current_user: dict = Depends(oauth2.get_current_user),
    user_id: Optional[int] = None,
    pet_id: Optional[int] = None,
    limit: int = Query(10, ge=1, le=100),
    skip: int = 0,
    search: Optional[str] = "",
    order_by: Optional[str] = "created_at",
    order_direction: Optional[str] = "desc"
):
    """
    Retrieve a list of posts with flexible querying, filtering, searching, and pagination options.

    ## Query Parameters:
    - **user_id** (Optional[int]): If provided, fetch posts created by the specified user. If omitted, fetch all users' posts.
    - **pet_id** (Optional[int]): If provided, filter posts related to a specific pet.
    - **limit** (int): The number of posts to return (default: 10). Must be between 1 and 100.
    - **skip** (int): The number of records to skip for pagination (default: 0).
    - **search** (Optional[str]): A case-insensitive search term to filter posts by content.
    - **order_by** (Optional[str]): Column name to order by (default: "created_at"). Must match a valid `Post` model attribute.
    - **order_direction** (Optional[str]): Direction of sorting, either `"asc"` or `"desc"` (default: `"desc"`).

    ## Behavior:
    - Filters can be applied for user ID and pet ID independently or together.
    - If `user_id` is not provided, posts from all users are returned.
    - Posts can be searched by partial matches in content.
    - Supports dynamic ordering by any valid column in the `Post` model.
    - Pagination is controlled by `limit` and `skip`.
    - Secure access tokens are appended to any media URLs using Azure Blob SAS.

    ## Returns:
    - A list of `PostResponse` objects that match the query parameters.
    - Raises an HTTP 500 error if the query fails.
    """
    try:
        # Start query from Post table
        query = db.query(models.Post)

        # Filter by user_id if provided
        if user_id:
            query = query.filter(models.Post.user_id == user_id)

        # Filter by pet_id if provided
        if pet_id:
            query = query.filter(models.Post.pet_id == pet_id)

        # Apply full-text search on post content
        if search:
            query = query.filter(models.Post.content.ilike(f"%{search}%"))

        # Dynamic ordering
        if hasattr(models.Post, order_by):
            order_column = getattr(models.Post, order_by)
            if order_direction.lower() == "asc":
                query = query.order_by(asc(order_column))
            else:
                query = query.order_by(desc(order_column))
        else:
            # Fallback to default ordering by created_at
            query = query.order_by(desc(models.Post.created_at))

        # Apply pagination
        posts = query.offset(skip).limit(limit).all()

        # Append SAS token to media URLs for secure access
        for post in posts:
            if post.media_url:
                sas_token = azure_storage_service.create_service_sas_container()
                post.media_url = f"{post.media_url}?{sas_token}"
        return posts

    except Exception as e:
        logger.error(f"Failed to fetch posts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch posts")
