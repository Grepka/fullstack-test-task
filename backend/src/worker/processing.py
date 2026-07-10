from src.database import async_session_maker
from src.repositories import alerts as alert_repository
from src.repositories import files as file_repository
from src.services.scanning import build_alert, extract_metadata, find_threats
from src.storage import get_stored_path


async def scan_file(file_id: str) -> bool:
    async with async_session_maker() as session:
        file_item = await file_repository.get_file(session, file_id)
        if not file_item:
            return False

        file_item.processing_status = "processing"
        reasons = find_threats(file_item.original_name, file_item.size, file_item.mime_type)
        file_item.scan_status = "suspicious" if reasons else "clean"
        file_item.scan_details = ", ".join(reasons) if reasons else "no threats found"
        file_item.requires_attention = bool(reasons)
        await session.commit()
        return True


async def extract_file_metadata(file_id: str) -> bool:
    async with async_session_maker() as session:
        file_item = await file_repository.get_file(session, file_id)
        if not file_item:
            return False

        stored_path = get_stored_path(file_item.stored_name)
        if not stored_path.exists():
            file_item.processing_status = "failed"
            file_item.scan_status = file_item.scan_status or "failed"
            file_item.scan_details = "stored file not found during metadata extraction"
            await session.commit()
            return True

        file_item.metadata_json = extract_metadata(
            stored_path,
            file_item.original_name,
            file_item.mime_type,
            file_item.size,
        )
        file_item.processing_status = "processed"
        await session.commit()
        return True


async def send_file_alert(file_id: str) -> None:
    async with async_session_maker() as session:
        file_item = await file_repository.get_file(session, file_id)
        if not file_item:
            return

        await alert_repository.add_alert_once(session, build_alert(file_item))
        await session.commit()
