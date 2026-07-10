from pathlib import Path

from fastapi import UploadFile

from src.config import STORAGE_DIR


CHUNK_SIZE = 1024 * 1024

STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def get_stored_path(stored_name: str) -> Path:
    return STORAGE_DIR / stored_name


async def save_upload_file(upload_file: UploadFile, stored_name: str) -> int:
    stored_path = get_stored_path(stored_name)
    size = 0

    with stored_path.open("wb") as destination:
        while chunk := await upload_file.read(CHUNK_SIZE):
            size += len(chunk)
            destination.write(chunk)

    if size == 0:
        stored_path.unlink(missing_ok=True)

    return size


def delete_stored_file(stored_name: str) -> None:
    get_stored_path(stored_name).unlink(missing_ok=True)
