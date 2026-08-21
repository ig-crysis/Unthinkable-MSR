from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./app.db"
    upload_dir: str = "./uploads"
    groq_api_key: str = ""
    # Optional second Groq account's key, used only for the diarization
    # batch calls (the biggest source of LLM call volume for a long
    # meeting) — splits that load onto its own separate token budget so it
    # doesn't compete with summarization for the same account's rate limit.
    # Falls back to groq_api_key when unset.
    groq_api_key_diarize: str = ""
    max_upload_mb: int = 200

    # A meeting is routed through the chunked pipeline if it crosses either
    # threshold. Size is always known at upload time; duration is known only
    # when ffprobe succeeds, so size is the fallback signal.
    chunk_size_threshold_mb: int = 20
    chunk_duration_threshold_min: int = 15
    chunk_target_minutes: int = 12
    chunk_max_minutes: int = 15
    asr_model: str = "whisper-large-v3"
    llm_model: str = "openai/gpt-oss-120b"


settings = Settings()
