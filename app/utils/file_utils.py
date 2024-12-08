from fastapi import UploadFile, HTTPException, status
from ..services import azure_storage_service

def upload_profile_picture(file: UploadFile) -> str:
    # if file.content_type not in ["image/jpeg", "image/png"]:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Invalid file type. Only JPEG and PNG are allowed."
    #     )
    
    return azure_storage_service.upload_file_to_blob(file.file, file.filename, file.content_type)
