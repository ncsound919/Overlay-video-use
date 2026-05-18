from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "video-use-backend"
    debug: bool = True
    database_url: str = f"sqlite:///{Path(__file__).parent / 'data' / 'videouse.db'}"
    upload_dir: str = str(Path(__file__).parent / "data" / "uploads")
    render_dir: str = str(Path(__file__).parent / "data" / "renders")
    project_dir: str = str(Path(__file__).parent / "data" / "projects")
    elevenlabs_api_key: str = ""
    max_upload_size_mb: int = 4096
    cors_origins: str = "http://localhost:3000,http://localhost:3002"
    auth_enabled: bool = False
    secret_key: str = "dev-secret-change-in-production"

    class Config:
        env_file = ".env"


settings = Settings()
