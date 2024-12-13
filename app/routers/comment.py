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
def read_comments(post_id: int, 
                  db: Session = Depends(database.get_db),
                  current_user: dict = Depends(oauth2.get_current_user)):
    
    comments = db.query(models.Comment).filter(models.Comment.post_id == post_id).all()
    if not comments:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    return comments

# Add additional endpoints for updating and deleting comments as needed.
