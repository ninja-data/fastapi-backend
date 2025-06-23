from pydantic_settings import BaseSettings

class Setting(BaseSettings):
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    azure_storage_connection_string: str
    azure_storage_account_key: str
    azure_storage_container_name: str

    email_sender: str
    email_password: str


    class  Config:
        env_file = ".env"


settings = Setting()
