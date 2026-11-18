from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Study Prep Tool"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Security
    SECRET_KEY: str = "studybuddy-super-secret-key-2024"

    # Database
    DATABASE_URL: str = "sqlite:///./studybuddy.db"

    # LLM
    LLM_PROVIDER: str = "groq"
    GROQ_API_KEY: str = ""
    GROQ_MODEL_CHAT: str = "openai/gpt-oss-120b"
    GROQ_MODEL_FAST: str = "openai/gpt-oss-20b"

    # Embeddings / Vector DB
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    CHROMA_DB_PATH: str = "./chroma_db"

    # File storage
    UPLOAD_DIR: str = "./storage"
    MAX_FILE_SIZE_MB: int = 10

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
