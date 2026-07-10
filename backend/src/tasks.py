from celery import Celery

from src.config import CELERY_BROKER_URL
from src.worker import processing
from src.worker.loop import run_in_worker_loop

celery_app = Celery("file_tasks", broker=CELERY_BROKER_URL, backend=CELERY_BROKER_URL)


@celery_app.task
def scan_file_for_threats(file_id: str) -> None:
    if run_in_worker_loop(processing.scan_file(file_id)):
        extract_file_metadata.delay(file_id)


@celery_app.task
def extract_file_metadata(file_id: str) -> None:
    if run_in_worker_loop(processing.extract_file_metadata(file_id)):
        send_file_alert.delay(file_id)


@celery_app.task
def send_file_alert(file_id: str) -> None:
    run_in_worker_loop(processing.send_file_alert(file_id))
