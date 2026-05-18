import shutil
from pathlib import Path
from config import settings


def delete_project_assets(project_id: int) -> bool:
    project_dir = Path(settings.project_dir) / str(project_id)
    if not project_dir.exists():
        return False
    try:
        shutil.rmtree(project_dir)
        return True
    except Exception:
        return False
