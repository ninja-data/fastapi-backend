from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .. import models, schemas, utils, oauth2
from ..database import get_db

router = APIRouter(
    prefix="/users",
    tags=['Users']
)

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.UserResponse)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):

    # hash the password  - user.password
    user.password = utils.hash(user.password)

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

    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise ValueError("Failed to create user due to a unique constraint violation")

    return new_user


@router.get("/{id}", response_model=schemas.UserResponse)
def get_user(id: int, db: Session = Depends(get_db),  current_user: dict = Depends(oauth2.get_current_user),):

    user = db.query(models.User).filter(models.User.id == id).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=f"User with id: {id} does not exist")
    
    return user
 