from fastapi import UploadFile, HTTPException, status
from ..services import azure_storage_service

# TODO Structure Storage Account

def upload_profile_picture(file: UploadFile) -> str:
    # if file.content_type not in ["image/jpeg", "image/png"]:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Invalid file type. Only JPEG and PNG are allowed."
    #     )
    
    return azure_storage_service.upload_file_to_blob(file.file, file.filename, file.content_type)


def add_sas_token_to_url(url: str) -> str:
    if url:
        sas_token = azure_storage_service.create_service_sas_container()
        return f"{url}?{sas_token}"
    return url
