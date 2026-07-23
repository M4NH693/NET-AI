from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )    

    database_url: str 
    
    secret_key: SecretStr

    max_upload_size_bytes: int = 5 * 1024 *1024

settings = Settings() 
