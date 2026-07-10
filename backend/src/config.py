import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage" / "files"

DB_URL = (
    f"postgresql+asyncpg://{os.environ.get('POSTGRES_USER')}:"
    f"{os.environ.get('POSTGRES_PASSWORD')}@{os.environ.get('POSTGRES_HOST')}:"
    f"{os.environ.get('PGPORT')}/{os.environ.get('POSTGRES_DB')}"
)
