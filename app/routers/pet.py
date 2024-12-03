from fastapi import Response, status, HTTPException, Depends, APIRouter
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
async def get_pets(db:Session = Depends(get_db), # current_user: dict = Depends(oauth2.get_current_user),
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


@router.get("/{id}", response_model=schemas.PetOut)
async def get_pet(id: int, db: Session = Depends(get_db)):

    pet = db.query(models.Pet).filter(models.Pet.id == id).first()

    if not pet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"pet with id: {id} was not found")
    
    return pet


@router.delete("/id", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pet(id: int, db: Session = Depends(get_db), current_user: dict = Depends(oauth2.get_current_user)):
    pet_query = db.query(models.Pet).filter(models.Pet.id == id)

    pet = pet_query.first()

    if pet == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"pet with id {id} does not exist")
    
    if pet.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to perform requested action")
    
    pet_query.delete(synchronize_session=False)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)

# TODO add put