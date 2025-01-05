from typing import List
from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from .. import schemas, database, models, oauth2


router = APIRouter(
    prefix="/comment",
    tags=["Comment"]
)

@router.post("/", response_model=schemas.CommentResponse, status_code=status.HTTP_201_CREATED)
async def comment(comment: schemas.CommentCreate, 
                  db: Session = Depends(database.get_db), 
                  current_user: dict = Depends(oauth2.get_current_user)):
    

    new_comment = models.Comment(user_id=current_user.id, **comment.model_dump())

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    return new_comment


@router.get("/{post_id}", response_model=List[schemas.CommentResponse])
def read_comments(
    post_id: int, 
    db: Session = Depends(database.get_db), 
    current_user: dict = Depends(oauth2.get_current_user)
) -> List[schemas.CommentResponse]:
    """
    Fetch all comments for a specific post.

    Args:
        post_id (int): ID of the post to fetch comments for.
        db (Session): Database session dependency.
        current_user (dict): Authenticated user dependency.

    Returns:
        List[schemas.CommentResponse]: List of comments for the specified post.
    """
    # Validate post existence
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Post with id {post_id} not found"
        )
    
    # Fetch comments for the post
    comments = (
        db.query(models.Comment)
        .filter(models.Comment.post_id == post_id)
        .order_by(models.Comment.created_at.desc())
        .all())
    

    return comments  # Return an empty list if no comments exist


# Add additional endpoints for updating and deleting comments as needed.
