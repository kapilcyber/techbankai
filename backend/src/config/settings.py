"""Centralized settings management using Pydantic Settings."""
from pydantic_settings import BaseSettings
from typing import Optional, Any
from urllib.parse import quote_plus

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # PostgreSQL Configuration
    postgres_host: str = "localhost"
    postgres_port: str = "5432"
    postgres_db: str = "techbank"
    postgres_user: str = "postgres"
    postgres_password: str = ""
    
    # Unified Database URL (Optional override)
    database_url: Optional[str] = None
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # JWT Configuration
    jwt_secret_key: str = "your-secret-key-change-this"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"
    openai_max_tokens: int = 4096
    
    # Google Drive Configuration
    google_drive_credentials_path: Optional[str] = None
    google_drive_folder_id: Optional[str] = None
    use_google_drive: bool = False
    
    # Celery Configuration
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # File Upload Configuration
    upload_dir: str = "uploads"
    max_file_size_mb: int = 10
    
    # CORS Configuration
    cors_origins: str = "*"  # Comma-separated origins or "*" for all

    # Google OAuth Configuration
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    
    @property
    def _clean_postgres_host(self) -> str:
        return self.postgres_host.strip()

    @property
    def _clean_postgres_port(self) -> str:
        return str(self.postgres_port).strip()

    @property
    def _clean_postgres_db(self) -> str:
        return self.postgres_db.strip()

    @property
    def _clean_postgres_user(self) -> str:
        return self.postgres_user.strip()

    @property
    def _clean_postgres_password(self) -> str:
        return self.postgres_password

    @property
    def async_database_url(self) -> str:
        """Constructs the async PostgreSQL URL (postgresql+asyncpg)."""
        if self.database_url:
            # If a custom URL is provided, ensure it uses the async driver
            url = self.database_url.strip()
            if url.startswith("postgresql://"):
                return url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url
            
        # Otherwise construct from components with proper encoding
        user = quote_plus(self._clean_postgres_user)
        # Handle empty password case
        password = quote_plus(self._clean_postgres_password) if self._clean_postgres_password else ""
        host = self._clean_postgres_host
        port = self._clean_postgres_port
        db = self._clean_postgres_db
        
        # If password is provided, include it
        auth = f"{user}:{password}" if password else user
        
        return f"postgresql+asyncpg://{auth}@{host}:{port}/{db}"

    @property
    def sync_database_url(self) -> str:
        """Constructs the sync PostgreSQL URL (postgresql) or DSN."""
        if self.database_url:
            return self.database_url.strip()
            
        user = quote_plus(self._clean_postgres_user)
        password = quote_plus(self._clean_postgres_password) if self._clean_postgres_password else ""
        host = self._clean_postgres_host
        port = self._clean_postgres_port
        db = self._clean_postgres_db
        
        auth = f"{user}:{password}" if password else user
        
        return f"postgresql://{auth}@{host}:{port}/{db}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env file


# Global settings instance
settings = Settings()
