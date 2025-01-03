from azure.storage.blob import BlobServiceClient, ContainerSasPermissions, generate_container_sas
from datetime import datetime, timedelta, timezone
import uuid
import logging
from ..config import settings

logger = logging.getLogger(__name__)

blob_service_client = BlobServiceClient.from_connection_string(settings.azure_storage_connection_string)
container_client = blob_service_client.get_container_client(settings.azure_storage_container_name)

def upload_file_to_blob(file_data, file_name, content_type):
    blob_name = f"{uuid.uuid4()}_{file_name}"
    blob_client = container_client.get_blob_client(blob_name)
    blob_client.upload_blob(file_data, content_type=content_type)
    return blob_client.url    


def create_service_sas_container() -> str:
    # Create a SAS token that's valid for one day, as an example
    start_time = datetime.now(timezone.utc)
    expiry_time = start_time + timedelta(days=1)

    sas_token = generate_container_sas(
        account_name=container_client.account_name,
        container_name=container_client.container_name,
        account_key=settings.azure_storage_account_key,
        permission=ContainerSasPermissions(read=True),
        expiry=expiry_time,
        start=start_time
    )

    return sas_token

# TODO add this for all files
def add_sas_token(url: str) -> str:
    if url:
        url = f"{url}?{create_service_sas_container()}"
    return url
    