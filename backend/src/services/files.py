import mimetypes
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from src.database import async_session_maker
from src.exceptions import EmptyFileError, FileNotFound, StoredFileMissing
from src.models import StoredFile
from src.repositories import alerts as alert_repository
from src.repositories import files as file_repository
from src.storage import delete_stored_file, get_stored_path, save_upload_file


async def list_files() -> list[StoredFile]:
    async with async_session_maker() as session:
        return await file_repository.list_files(session)


async def get_file(file_id: str) -> StoredFile:
    async with async_session_maker() as session:
        file_item = await file_repository.get_file(session, file_id)
        if not file_item:
            raise FileNotFound()
        return file_item


async def create_file(title: str, upload_file: UploadFile) -> StoredFile:
    file_id = str(uuid4())
    suffix = Path(upload_file.filename or "").suffix
    stored_name = f"{file_id}{suffix}"
    size = await save_upload_file(upload_file, stored_name)
    if size == 0:
        raise EmptyFileError()

    file_item = StoredFile(
        id=file_id,
        title=title,
        original_name=upload_file.filename or stored_name,
        stored_name=stored_name,
        mime_type=upload_file.content_type or mimetypes.guess_type(stored_name)[0] or "application/octet-stream",
        size=size,
        processing_status="uploaded",
    )
    async with async_session_maker() as session:
        file_repository.add_file(session, file_item)
        await session.commit()
        await session.refresh(file_item)
    return file_item


async def update_file(file_id: str, title: str) -> StoredFile:
    async with async_session_maker() as session:
        file_item = await file_repository.get_file(session, file_id)
        if not file_item:
            raise FileNotFound()
        file_item.title = title
        await session.commit()
        await session.refresh(file_item)
        return file_item


async def delete_file(file_id: str) -> None:
    async with async_session_maker() as session:
        file_item = await file_repository.get_file(session, file_id)
        if not file_item:
            raise FileNotFound()
        stored_name = file_item.stored_name
        await alert_repository.delete_alerts_by_file_id(session, file_id)
        await file_repository.delete_file(session, file_item)
        await session.commit()
        delete_stored_file(stored_name)


async def get_file_path(file_id: str) -> tuple[StoredFile, Path]:
    file_item = await get_file(file_id)
    stored_path = get_stored_path(file_item.stored_name)
    if not stored_path.exists():
        raise StoredFileMissing()
    return file_item, stored_path
