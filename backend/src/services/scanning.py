from pathlib import Path

from src.models import Alert, StoredFile


SUSPICIOUS_EXTENSIONS = {".exe", ".bat", ".cmd", ".sh", ".js"}
MAX_SAFE_FILE_SIZE = 10 * 1024 * 1024


def find_threats(original_name: str, size: int, mime_type: str) -> list[str]:
    reasons: list[str] = []
    extension = Path(original_name).suffix.lower()

    if extension in SUSPICIOUS_EXTENSIONS:
        reasons.append(f"suspicious extension {extension}")

    if size > MAX_SAFE_FILE_SIZE:
        reasons.append("file is larger than 10 MB")

    if extension == ".pdf" and mime_type not in {"application/pdf", "application/octet-stream"}:
        reasons.append("pdf extension does not match mime type")

    return reasons


def extract_metadata(stored_path: Path, original_name: str, mime_type: str, size: int) -> dict:
    metadata = {
        "extension": Path(original_name).suffix.lower(),
        "size_bytes": size,
        "mime_type": mime_type,
    }

    if mime_type.startswith("text/"):
        content = stored_path.read_text(encoding="utf-8", errors="ignore")
        metadata["line_count"] = len(content.splitlines())
        metadata["char_count"] = len(content)
    elif mime_type == "application/pdf":
        content = stored_path.read_bytes()
        metadata["approx_page_count"] = max(content.count(b"/Type /Page"), 1)

    return metadata


def build_alert(file_item: StoredFile) -> Alert:
    if file_item.processing_status == "failed":
        return Alert(file_id=file_item.id, level="critical", message="File processing failed")

    if file_item.requires_attention:
        return Alert(
            file_id=file_item.id,
            level="warning",
            message=f"File requires attention: {file_item.scan_details}",
        )

    return Alert(file_id=file_item.id, level="info", message="File processed successfully")
