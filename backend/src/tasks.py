import asyncio
import os
from celery import Celery
from src.database import async_session_maker
from src.repositories import alerts as alert_repository
from src.repositories import files as file_repository
from src.services.scanning import build_alert, extract_metadata, find_threats
from src.storage import get_stored_path

REDIS_URL = os.environ.get("REDIS_URL", "redis://backend-redis:6379/0")
_worker_loop: asyncio.AbstractEventLoop | None = None


def run_in_worker_loop(coroutine):
    global _worker_loop
    if _worker_loop is None or _worker_loop.is_closed():
        _worker_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_worker_loop)
    return _worker_loop.run_until_complete(coroutine)


celery_app = Celery("file_tasks", broker=REDIS_URL, backend=REDIS_URL)


async def _scan_file_for_threats(file_id: str) -> None:
    async with async_session_maker() as session:
        file_item = await file_repository.get_file(session, file_id)
        if not file_item:
            return

        file_item.processing_status = "processing"
        reasons = find_threats(file_item.original_name, file_item.size, file_item.mime_type)
        file_item.scan_status = "suspicious" if reasons else "clean"
        file_item.scan_details = ", ".join(reasons) if reasons else "no threats found"
        file_item.requires_attention = bool(reasons)
        await session.commit()

    extract_file_metadata.delay(file_id)


async def _extract_file_metadata(file_id: str) -> None:
    async with async_session_maker() as session:
        file_item = await file_repository.get_file(session, file_id)
        if not file_item:
            return

        stored_path = get_stored_path(file_item.stored_name)
        if not stored_path.exists():
            file_item.processing_status = "failed"
            file_item.scan_status = file_item.scan_status or "failed"
            file_item.scan_details = "stored file not found during metadata extraction"
            await session.commit()
            send_file_alert.delay(file_id)
            return

        file_item.metadata_json = extract_metadata(
            stored_path,
            file_item.original_name,
            file_item.mime_type,
            file_item.size,
        )
        file_item.processing_status = "processed"
        await session.commit()

    send_file_alert.delay(file_id)


async def _send_file_alert(file_id: str) -> None:
    async with async_session_maker() as session:
        file_item = await file_repository.get_file(session, file_id)
        if not file_item:
            return

        alert_repository.add_alert(session, build_alert(file_item))
        await session.commit()


@celery_app.task
def scan_file_for_threats(file_id: str) -> None:
    run_in_worker_loop(_scan_file_for_threats(file_id))


@celery_app.task
def extract_file_metadata(file_id: str) -> None:
    run_in_worker_loop(_extract_file_metadata(file_id))


@celery_app.task
def send_file_alert(file_id: str) -> None:
    run_in_worker_loop(_send_file_alert(file_id))
