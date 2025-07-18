from fastapi import Response, UploadFile, status, HTTPException, Depends, APIRouter, Form, File, Query
from sqlalchemy.sql import func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import func, outerjoin, or_
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


# Dropdown list
@router.get("/animal-types", 
            response_model=List[schemas.AnimalTypeResponse]
            )
async def get_animal_types(
    db: Session = Depends(get_db),
    # current_user: dict = Depends(oauth2.get_current_user)
    ):
    
    try:
        animal_types = (
            db.query(
                models.AnimalType, 
                func.count(models.Pet.id).label("count")
            )
            .outerjoin(models.Pet, models.Pet.animal_type_id == models.AnimalType.id)
            .group_by(models.AnimalType.id)
            .all()
        )

        result = []
        for animal_type, count in animal_types:
            
            result.append(
                schemas.AnimalTypeResponse(
                    id=animal_type.id,
                    name=animal_type.name,
                    image_url=animal_type.image_url,
                    count=count,
                )
            )

        return result
    except Exception as e:
        logger.error(f"Failed to fetch animal types: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@router.get("/pet-types", response_model=List[schemas.PetTypesResponse])
async def get_pet_types(
    animal_type_id: int = Query(None), # if sent 0, retrun all
    db: Session = Depends(get_db)
    # current_user: dict = Depends(oauth2.get_current_user),
):

    try:    
        query = (
            db.query(models.PetType, func.count(models.Pet.id).label("count"))
            .outerjoin(models.Pet, models.Pet.pet_type_id == models.PetType.id)
        )

        if animal_type_id:
            query = query.filter(models.PetType.animal_type_id == animal_type_id)

        pet_types = query.group_by(models.PetType.id).all()

        result = []
        for pet_type, count in pet_types:

            result.append(
                schemas.PetTypesResponse(
                    id=pet_type.id,
                    name=pet_type.name,
                    image_url=pet_type.image_url,
                    animal_type_id=pet_type.animal_type_id,
                    count=count,
                )
            )

        return result
    except Exception as e:
        logger.error(f"Failed to fetch pet types: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/breeds", response_model=List[schemas.BreedResponse])
async def get_breeds(
    pet_type_id: int = Query(None),
    db: Session = Depends(get_db)
    # current_user: dict = Depends(oauth2.get_current_user),
):
    
    try:
        query = (
            db.query(models.Breed, func.count(models.Pet.id).label("count"))
            .outerjoin(
                models.Pet, 
                or_(
                    models.Pet.breed_1_id == models.Breed.id,
                    models.Pet.breed_2_id == models.Breed.id,
                )
            )
        )

        if pet_type_id:
            query = query.filter(models.Breed.pet_type_id == pet_type_id)
        breeds = query.group_by(models.Breed.id).all()


        result = []
        for breed, count in breeds:

            result.append(
                schemas.BreedResponse(
                    id=breed.id,
                    name=breed.name,
                    image_url=breed.image_url,
                    pet_type_id=breed.pet_type_id,
                    count=count,
                )
            )

        return result
    except Exception as e:
        logger.error(f"Failed to fetch breeds: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@router.get("/by-breed", response_model=List[schemas.PetResponse])
async def get_pets_by_breed(
    breed_id: int = Query(...),  # Required breed ID
    db: Session = Depends(get_db),
    current_user: dict = Depends(oauth2.get_current_user),
    limit: int = Query(default=30, ge=1, le=100), 
    skip: int = Query(default=0, ge=0),
):
    """
    Fetch pets by breed ID.
    """
    try:
        pets_with_follow_status = db.query(
            models.Pet,
            models.UserRelationship.status.label("follow_status")
        ).outerjoin(
            models.UserRelationship,
            (models.UserRelationship.requester_id == current_user.id) & (models.UserRelationship.receiver_id == models.Pet.user_id)
        ).filter(
            or_(
                models.Pet.breed_1_id == breed_id,
                models.Pet.breed_2_id == breed_id
            )
        ).limit(limit).offset(skip).all()

        pets = []
        for pet, follow_status in pets_with_follow_status:
            setattr(pet.user, "follow_status", follow_status)
            pets.append(pet)
    except Exception as e:
        logger.error(f"Failed to fetch pets by breed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch pets by breed")

    return pets


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.PetResponse)
async def create_pet(
    # pet: schemas.PetCreate, 
    pet: str = Form(...),
    file: UploadFile = File(None),
    db: Session = Depends(get_db), 
    current_user: dict = Depends(oauth2.get_current_user)
    ):

    try:
        pet_data = json.loads(pet.replace("\\", ""))
        pet = schemas.PetCreate(**pet_data)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e.errors()),
        )

    new_pet = models.Pet(user_id=current_user.id, **pet.model_dump())

    if file and file.size :
        try:
            picture_url = file_utils.upload_profile_picture(file)
            new_pet.profile_picture_url = picture_url
        except IntegrityError as e:
            logger.error(f"Integrity error during file upload: {e}")

    db.add(new_pet)
    db.commit()
    db.refresh(new_pet)

    return new_pet


@router.get("/", response_model=List[schemas.PetResponse], summary="Get list of pets")
async def get_pets(
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(oauth2.get_current_user),
    limit: int = Query(10, ge=1, le=100, description="Number of pets to return (1-100)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    search: Optional[str] = Query("", description="Search pets by name"),
    only_my_pets: bool = Query(False, description="Return only the current user's pets"),
    user_id: Optional[int] = Query(None, description="Filter pets by specific user ID")
):
    """
    Retrieve a list of pets with optional filters.

    - **limit**: Limit the number of results returned (max 100)
    - **skip**: Skip a number of results (for pagination)
    - **search**: Filter pets by name (partial, case-insensitive match)
    - **only_my_pets**: If true, only return pets belonging to the current user
    - **user_id**: Optional user ID to filter pets by owner

    If both `only_my_pets` and `user_id` are set, `only_my_pets` takes priority.
    """
    try:
        query = db.query(models.Pet)

        if search:
            query = query.filter(models.Pet.name.ilike(f"%{search}%"))

        if only_my_pets:
            query = query.filter(models.Pet.user_id == current_user.id)
        elif user_id is not None:
            query = query.filter(models.Pet.user_id == user_id)

        pets = query.limit(limit).offset(skip).all()
        return pets

    except SQLAlchemyError as e:
        logger.error(
            f"Database error while fetching pets: {str(e)} | Params: "
            f"search='{search}', limit={limit}, skip={skip}, "
            f"user_id={user_id}, only_my_pets={only_my_pets}, user={current_user.id}"
        )
        raise HTTPException(status_code=500, detail="Failed to fetch pets")


@router.get("/{id}", response_model=schemas.PetResponse)
async def get_pet(id: int, db: Session = Depends(get_db), current_user: dict = Depends(oauth2.get_current_user),):

    pet = db.query(models.Pet).filter(models.Pet.id == id).first()

    if not pet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"pet with id: {id} was not found")
    
    return pet


# TODO delete also image from azure storage
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


# TODO separate folder for pet's imagie
@router.post("/{id}/upload-profile-picture", response_model=schemas.PetResponse)
async def upload_profile_picture(
    id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(oauth2.get_current_user),
):
    pet = db.query(models.Pet).filter(models.Pet.id == id).first()
    if not pet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Not authorized to perform requested action")
    
    if pet.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to perform request action")
    
    try:
        picture_url = file_utils.upload_profile_picture(file)
        pet.profile_picture_url = picture_url
        db.commit()
        db.refresh(pet)
    except Exception as e:
        logger.error(f"File upload error for ise {id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to upload profile picture"
        )

    return pet

# TODO and put

@router.put("/{id}", response_model=schemas.PetResponse)
async def update_pet(
    id: int,
    pet_update: schemas.PetUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(oauth2.get_current_user),
):
    pet_query = db.query(models.Pet).filter(models.Pet.id == id)
    pet = pet_query.first()

    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")

    if pet.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this pet")

    try:
        update_data = pet_update.model_dump(exclude_unset=True)
        pet_query.update(update_data, synchronize_session=False)
        db.commit()
        db.refresh(pet)

        return pet

    except Exception as e:
        logger.error(f"Update failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to update pet")


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pet(id: int, db: Session = Depends(get_db), current_user: dict = Depends(oauth2.get_current_user)):
    pet_query = db.query(models.Pet).filter(models.Pet.id == id)
    pet = pet_query.first()

    if pet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Pet with id {id} does not exist")

    if pet.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to perform requested action")

    # Delete image from Azure Storage
    if pet.profile_picture_url:
        try:
            file_utils.delete_blob(pet.profile_picture_url)
        except Exception as e:
            logger.warning(f"Failed to delete image from Azure: {e}")

    pet_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
