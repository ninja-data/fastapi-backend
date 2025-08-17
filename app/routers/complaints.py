from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status, Form
from sqlalchemy.orm import Session
from .. import models, schemas, oauth2
from ..database import get_db
from ..utils import file_utils
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/complaints",
    tags=["Complaints"]
)

@router.post("/", status_code=status.HTTP_200_OK, response_model=schemas.ComplaintResponse)
async def complain(
    entity_type: str = Form(...),
    entity_id: int = Form(...),
    reason: str = Form(...),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    # Manually validate input with Pydantic model
    try:
        complaint_data = schemas.ComplaintCreate(
            entity_type=entity_type,
            entity_id=entity_id,
            reason=reason,
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid complaint data: {e}")

    if complaint_data.entity_type == "user" and complaint_data.entity_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot complain about yourself")

    entity_models = {
        "user": models.User,
        "pet": models.Pet,
        "post": models.Post,
        "story": models.Story
    }
    entity_model = entity_models.get(complaint_data.entity_type)
    if not entity_model:
        raise HTTPException(status_code=400, detail="Invalid entity type")

    if not db.query(entity_model).filter(entity_model.id == complaint_data.entity_id).first():
        raise HTTPException(status_code=404, detail=f"{complaint_data.entity_type.capitalize()} not found")

    if db.query(models.Complaint).filter(
        models.Complaint.complainer_id == current_user.id,
        models.Complaint.entity_type == complaint_data.entity_type,
        models.Complaint.entity_id == complaint_data.entity_id
    ).first():
        raise HTTPException(status_code=409, detail="You already complained about this entity")

    evidence_url = None
    if file is not None:
        try:
            # Assuming upload_complaint_file can be async, otherwise remove await
            evidence_url = await file_utils.upload_complaint_file(file)
        except Exception as e:
            logger.error(f"File upload failed: {e}")
            raise HTTPException(status_code=400, detail="Failed to upload evidence")

    complaint = models.Complaint(
        complainer_id=current_user.id,
        entity_type=complaint_data.entity_type,
        entity_id=complaint_data.entity_id,
        reason=complaint_data.reason,
        evidence_url=evidence_url
    )

    try:
        db.add(complaint)
        db.commit()
        db.refresh(complaint)
    except Exception as e:
        db.rollback()
        logger.error(f"Database error while creating complaint: {e}")
        raise HTTPException(status_code=500, detail="Failed to create complaint")

    return complaint
