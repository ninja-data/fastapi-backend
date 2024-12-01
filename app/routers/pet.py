from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy.sql import func
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import models, schemas, utils, oauth2
from ..database import get_db

router =APIRouter(
    prefix="/pets",
    tags=['Pets']
)

@router.get("/", response_model=List[schemas.PetOut])
async def get_posts(db:Session = Depends(get_db), current_user: dict = Depends(oauth2.get_current_user),
                    limit: int = 10, skip: int = 0, search: Optional[str] = ""):
    # TODO Show own posts only
    # posts = db.query(models.Post).filter(models.Post.owner_id == current_user.id).all()

    pets = db.query(models.Pet).filter(models.Pet.name.contains(search)).limit(limit).offset(skip).all()
    print(pets)
    return pets


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.PetOut)
async def create_pet(pet: schemas.PetCreate, db: Session = Depends(get_db), current_user: dict = Depends(oauth2.get_current_user)):

    new_pet = models.Pet(owner_id=current_user.id, **pet.model_dump())
    db.add(new_pet)
    db.commit()
    db.refresh(new_pet)
    return new_pet
