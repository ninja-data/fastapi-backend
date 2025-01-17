import json
import logging
from typing import List
from datetime import datetime, timezone, timedelta
from datetime import datetime
from fastapi import Body, File, Form, Query, UploadFile, status, HTTPException, Depends, APIRouter, Response
from pydantic import ValidationError
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from ..utils import security_utils, file_utils, story_utils
from ..services import azure_storage_service
from ..database import get_db

from .. import models, schemas, oauth2


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger  = logging.getLogger(__name__)


router = APIRouter(
    prefix="/follows",
    tags=['Follows']
)

@router.post("/", response_model=schemas.UserRelationshipResponse)
def follow_user(
    user_relationship: schemas.UserRealationshipCreate, # send only receiver_id
    db: Session = Depends(get_db), 
    current_user: dict = Depends(oauth2.get_current_user)
) -> schemas.UserRelationshipResponse:
    """
    This endpoint allows a user to follow another user. 
    The relationship status is determined based on whether the receiver’s account is private or public. 
    If the receiver’s account is private, the follow request will be set to PENDING until accepted by the receiver. 
    If the receiver’s account is public, the follow request is automatically set to ACCEPTED.
    """
    logger.info(f"User {current_user.id} is attempting to follow user {user_relationship.receiver_id}")

    user_receiver = db.query(models.User).filter(models.User.id == user_relationship.receiver_id).first()

    if not user_receiver:
        logger.warning(f"User {user_relationship.receiver_id} not found")
        raise HTTPException(status_code=404, detail=f"User with ID {user_relationship.receiver_id} not found")
    
    existing_relationship = db.query(models.UserRelationship).filter(
        models.UserRelationship.requester_id == current_user.id,
        models.UserRelationship.receiver_id == user_relationship.receiver_id
    ).scalar()

    if existing_relationship:
        logger.warning(f"User {current_user.id} already follows user {user_relationship.receiver_id}")
        raise HTTPException(status_code=400, detail="Already in a relationship with this user")

    status = schemas.UserRelationshipStatus.PENDING if user_receiver.private_account else schemas.UserRelationshipStatus.ACCEPTED
    new_relationship = models.UserRelationship(
        requester_id=current_user.id, 
        status=status,
        **user_relationship.model_dump()
    )

    try:
        db.add(new_relationship)
        db.commit()
        db.refresh(new_relationship)
        logger.info(f"User {current_user.id} successfully followed user {user_relationship.receiver_id}")
        return new_relationship
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected database error: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
        

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def unfollow_user(
    receiver_id: int = Query(..., description="ID of the user to unfollow"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(oauth2.get_current_user)
) -> Response:
    """
    This endpoint allows a user to unfollow another user.
    If no relationship exists, it raises a 404 error.
    """
    logger.info(f"User {current_user.id} attempting to unfollow user {receiver_id}")

    # Check if the relationship exists
    relationship = db.query(models.UserRelationship).filter(
        models.UserRelationship.requester_id == current_user.id,
        models.UserRelationship.receiver_id == receiver_id
    ).first()

    if not relationship:
        logger.warning(f"User {current_user.id} has no existing relationship with user {receiver_id}")
        raise HTTPException(status_code=404, detail=f"No existing relationship with user ID {receiver_id}")

    try:
        db.delete(relationship)
        db.commit()
        logger.info(f"User {current_user.id} successfully unfollowed user {receiver_id}")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error while deleting relationship: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error while deleting relationship: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")


@router.get("/followers/{user_id}", response_model=List[schemas.UserResponse])
def get_followers(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(oauth2.get_current_user)
) -> List[schemas.UserResponse]:
    """
    This endpoint retrieves a list of followers for a given user ID.
    """
    logger.info(f"Fetching followers for user {user_id}")

    # Retrieve followers of the user
    followers = db.query(models.User).join(
        models.UserRelationship, models.UserRelationship.requester_id == models.User.id
    ).filter(
        models.UserRelationship.receiver_id == user_id,
        models.UserRelationship.status == schemas.UserRelationshipStatus.ACCEPTED
    ).all()

    if not followers:
        logger.warning(f"User {user_id} has no followers")
        raise HTTPException(status_code=404, detail=f"No followers found for user ID {user_id}")

    logger.info(f"Retrieved {len(followers)} followers for user {user_id}")
    return followers


@router.get("/following/{user_id}", response_model=List[schemas.UserResponse])
def get_following(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(oauth2.get_current_user)
) -> List[schemas.UserResponse]:
    """
    This endpoint retrieves a list of users that a given user is following.
    """
    logger.info(f"Fetching following users for user {user_id}")

    # Retrieve users that the user is following
    following = db.query(models.User).join(
        models.UserRelationship, models.UserRelationship.receiver_id == models.User.id
    ).filter(
        models.UserRelationship.requester_id == user_id,
        models.UserRelationship.status == schemas.UserRelationshipStatus.ACCEPTED
    ).all()

    if not following:
        logger.warning(f"User {user_id} is not following anyone")
        raise HTTPException(status_code=404, detail=f"User ID {user_id} is not following anyone")

    logger.info(f"Retrieved {len(following)} users that user {user_id} is following")
    return following
