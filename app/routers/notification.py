from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, Query
from sqlalchemy import literal, desc
from typing import List

from .. import models, schemas, oauth2
from ..database import get_db
from ..utils.file_utils import add_sas_token_to_url


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)


def build_query(
    db: Session, 
    notification_type: str, 
    model, 
    user_id_field, 
    post_id_field, 
    current_user_id: int, 
    content_field=None
) -> Query:
    """
    Builds a query for the given notification type (comment or like).
    """
    query = (
        db.query(
            user_id_field.label("user_id"),
            post_id_field.label("post_id"),
            model.created_at.label("created_at"),
            models.User.profile_picture_url.label("user_photo_url"),
            models.User.name.label("user_name"),
            models.Post.media_url.label("post_photo_url"),
            literal(notification_type).label("type"),
            content_field.label("comment") if content_field else literal(None).label("comment")
        )
        .join(models.Post, model.post_id == models.Post.id)
        .join(models.User, model.user_id == models.User.id)
        .filter(models.Post.user_id == current_user_id)
    )
    return query


@router.get("/", response_model=List[schemas.NotificationResponse])
async def get_notifications(
    db: Session = Depends(get_db),
    current_user: dict = Depends(oauth2.get_current_user),
    limit: int = 10, skip: int = 0,
):
    try:
        # Build queries for comments and likes
        comments_query = build_query(db, 'comment', models.Comment, models.Comment.user_id, models.Comment.post_id, current_user.id, models.Comment.content)
        likes_query = build_query(db, 'like', models.Like, models.Like.user_id, models.Like.post_id, current_user.id)

        # Combine both queries
        notifications = comments_query.union_all(likes_query).order_by(desc('created_at')).offset(skip).limit(limit).all()

        notifications_list = [
            schemas.NotificationResponse(
                **{**notification._asdict(), 
                    'user_photo_url': add_sas_token_to_url(notification.user_photo_url), 
                    'post_photo_url': add_sas_token_to_url(notification.post_photo_url)}
            )
            for notification in notifications
        ]  

        return notifications_list
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while fetching notifications: {str(e)}")
