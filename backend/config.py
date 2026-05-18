from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "video-use-backend"
    debug: bool = False
    database_url: str = f"sqlite:///{Path(__file__).parent / 'data' / 'videouse.db'}"
    upload_dir: str = str(Path(__file__).parent / "data" / "uploads")
    render_dir: str = str(Path(__file__).parent / "data" / "renders")
    project_dir: str = str(Path(__file__).parent / "data" / "projects")
    elevenlabs_api_key: str = ""
    max_upload_size_mb: int = 4096
    cors_origins: str = "http://localhost:3000,http://localhost:3002"
    auth_enabled: bool = True
    secret_key: str = "dev-secret-change-in-production"
    rate_limit_enabled: bool = True

    class Config:
        env_file = ".env"

    def __init__(self, **values):
        super().__init__(**values)
        if not self.debug and self.secret_key == "dev-secret-change-in-production":
            import secrets
            import logging
            logging.basicConfig(level=logging.INFO)
            logger = logging.getLogger(__name__)
            logger.warning("WARNING: Hardcoded secret key detected in production mode! Replaced dynamically with a cryptographically secure random key.")
            self.secret_key = secrets.token_hex(32)


settings = Settings()
