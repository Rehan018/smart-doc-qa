from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "smart-doc-qa"
    ENV: str = "dev"

    DATABASE_URL: str
    REDIS_URL: str
    # LLM config
    LLM_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "https://ollama.merai.app/"
    OLLAMA_MODEL: str = "llama3"

    UPLOAD_DIR: str = "storage/uploads"
    FAISS_INDEX_DIR: str = "storage/faiss"

    MAX_FILE_SIZE_MB: int = 10


settings = Settings()
