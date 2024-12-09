from fastapi import Response, UploadFile, status, HTTPException, Depends, APIRouter, Form, File, Query
from sqlalchemy.sql import func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import ValidationError
from typing import List, Optional
import json
import logging

from ..utils import security_utils, file_utils
from ..services import azure_storage_service
from ..database import get_db

from .. import models, schemas, oauth2


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger  = logging.getLogger(__name__)


router =APIRouter(
    prefix="/pets",
    tags=['Pets']
)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.PetResponse)
async def create_pet(
    # pet: schemas.PetCreate, 
    pet: str = Form(...),
    file: UploadFile = File(None),
    db: Session = Depends(get_db), 
    current_user: dict = Depends(oauth2.get_current_user)
    ):

    try:
        pet_data = json.loads(pet)
        pet = schemas.PetCreate(**pet_data)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=str(e.error()),
        )

    new_pet = models.Pet(user_id=current_user.id, **pet.model_dump())

    if file:
        try:
            picture_url = file_utils.upload_profile_picture(file)
            new_pet.profile_picture_url = picture_url
        except IntegrityError as e:
            logger.error(f"Integrity error during file upload: {e}")

    db.add(new_pet)
    db.commit()
    db.refresh(new_pet)

    if new_pet.profile_picture_url:
        sas_token = azure_storage_service.create_service_sas_container()
        new_pet.profile_picture_url += "?" + sas_token

    return new_pet

# TODO Set fastapi limit for all endpoints Query
@router.get("/", response_model=List[schemas.PetResponse])
async def get_pets(
    db:Session = Depends(get_db), 
    current_user: dict = Depends(oauth2.get_current_user),
    limit: int = Query(default=10, ge=1, le=100), 
    skip: int = Query(default=0, ge=0), 
    search: Optional[str] = ""
    ):
    # TODO Show own posts only
    # posts = db.query(models.Post).filter(models.Post.owner_id == current_user.id).all()

    try:
        pets = db.query(models.Pet).filter(models.Pet.name.contains(search)).limit(limit).offset(skip).all()

        for pet in pets:
            if pet.profile_picture_url:
                sas_token = azure_storage_service.create_service_sas_container()
                pet.profile_picture_url = f"{pet.profile_picture_url}?{sas_token}"
    except Exception as e:
        logger.error(f"Failed to fetch pets: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch pets")

    return pets


@router.get("/{id}", response_model=schemas.PetResponse)
async def get_pet(id: int, db: Session = Depends(get_db), current_user: dict = Depends(oauth2.get_current_user),):

    pet = db.query(models.Pet).filter(models.Pet.id == id).first()

    if not pet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"pet with id: {id} was not found")
    
    try:
        if pet.profile_picture_url:
            sas_token = azure_storage_service.create_service_sas_container()
            pet.profile_picture_url = f"{pet.profile_picture_url}?{sas_token}"
    except Exception as e:
        logger.error(f"Failed to fetch pets: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch pets")  
    
    return pet


@router.delete("/id", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pet(id: int, db: Session = Depends(get_db), current_user: dict = Depends(oauth2.get_current_user)):
    pet_query = db.query(models.Pet).filter(models.Pet.id == id)

    pet = pet_query.first()

    if pet == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"pet with id {id} does not exist")
    
    if pet.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to perform requested action")
    
    pet_query.delete(synchronize_session=False)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# TODO add put