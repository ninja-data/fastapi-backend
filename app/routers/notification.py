from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, Query
from sqlalchemy import literal, desc, cast, Integer, select, union_all
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


def build_follow_query(
    db: Session,
    notification_type: str,
    current_user_id: int,
    is_accepted: bool = False
) -> Query:
    """
    Builds a query for follow request or follow accepted notifications.
    """
    query = (
        db.query(
            models.UserRelationship.requester_id.label("user_id"),
            cast(None, Integer).label("post_id"),
            models.UserRelationship.created_at.label("created_at"),
            models.User.profile_picture_url.label("user_photo_url"),
            models.User.name.label("user_name"),
            literal(None).label("post_photo_url"),
            literal(notification_type).label("type"),
            literal(None).label("comment"),
        )
        .join(models.User, models.UserRelationship.requester_id == models.User.id)
        .filter(models.UserRelationship.receiver_id == current_user_id)
    )

    if is_accepted:
        query = query.filter(models.UserRelationship.status == 'accepted')
    else:
        query = query.filter(models.UserRelationship.status == 'pending')

    return query


@router.get("/", response_model=List[schemas.NotificationResponse])
async def get_notifications(
    db: Session = Depends(get_db),
    current_user: dict = Depends(oauth2.get_current_user),
    limit: int = 10, skip: int = 0,
):
    try:
        # Build individual queries and convert them into subqueries
        comments_query = build_query(
            db, 'comment', models.Comment, models.Comment.user_id,
            models.Comment.post_id, current_user.id, models.Comment.content
        ).subquery()

        likes_query = build_query(
            db, 'like', models.Like, models.Like.user_id,
            models.Like.post_id, current_user.id
        ).subquery()

        follow_requests_query = build_follow_query(
            db, 'follow', current_user.id, is_accepted=True
        ).subquery()

        # Combine all subqueries using UNION ALL
        combined_query = union_all(
            select(comments_query),
            select(likes_query),
            select(follow_requests_query)
        ).subquery()

        # Now order by combined_query.c.created_at
        final_query = (
            db.query(combined_query)
            .order_by(desc(combined_query.c.created_at))
            .offset(skip)
            .limit(limit)
        )

        results = final_query.all()

        return [schemas.NotificationResponse(**r._asdict()) for r in results]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while fetching notifications: {str(e)}")
