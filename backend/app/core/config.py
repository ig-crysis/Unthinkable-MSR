from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./app.db"
    upload_dir: str = "./uploads"
    groq_api_key: str = ""
    max_upload_mb: int = 200


settings = Settings()
