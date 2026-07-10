import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from src.services.scanning import (
    MAX_SAFE_FILE_SIZE,
    build_alert,
    count_pdf_pages,
    extract_metadata,
    find_threats,
)


class ScanningTestCase(unittest.TestCase):
    def test_find_threats_returns_empty_list_for_safe_text_file(self) -> None:
        threats = find_threats("notes.txt", 512, "text/plain")

        self.assertEqual(threats, [])

    def test_find_threats_detects_suspicious_extension_and_large_file(self) -> None:
        threats = find_threats(
            "run.EXE",
            MAX_SAFE_FILE_SIZE + 1,
            "application/octet-stream",
        )

        self.assertEqual(
            threats,
            ["suspicious extension .exe", "file is larger than 10 MB"],
        )

    def test_find_threats_detects_pdf_mime_mismatch(self) -> None:
        threats = find_threats("report.pdf", 2048, "text/plain")

        self.assertEqual(threats, ["pdf extension does not match mime type"])

    def test_count_pdf_pages_ignores_pages_node(self) -> None:
        content = b"%PDF-1.7 /Type /Pages /Count 2 /Type /Page /Type /Page"

        self.assertEqual(count_pdf_pages(content), 2)

    def test_count_pdf_pages_returns_at_least_one_page(self) -> None:
        self.assertEqual(count_pdf_pages(b"%PDF-1.7"), 1)

    def test_extract_metadata_for_text_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            stored_path = Path(temp_dir) / "notes.txt"
            stored_path.write_text("first line\nsecond line\n", encoding="utf-8")

            metadata = extract_metadata(
                stored_path,
                "notes.txt",
                "text/plain",
                stored_path.stat().st_size,
            )

        self.assertEqual(
            metadata,
            {
                "extension": ".txt",
                "size_bytes": 23,
                "mime_type": "text/plain",
                "line_count": 2,
                "char_count": 23,
            },
        )

    def test_build_alert_for_successful_file(self) -> None:
        file_item = SimpleNamespace(
            id=12,
            processing_status="completed",
            requires_attention=False,
            scan_details=None,
        )

        alert = build_alert(file_item)

        self.assertEqual(alert.file_id, 12)
        self.assertEqual(alert.level, "info")
        self.assertEqual(alert.message, "File processed successfully")

    def test_build_alert_for_attention_file(self) -> None:
        file_item = SimpleNamespace(
            id=13,
            processing_status="completed",
            requires_attention=True,
            scan_details="suspicious extension .sh",
        )

        alert = build_alert(file_item)

        self.assertEqual(alert.file_id, 13)
        self.assertEqual(alert.level, "warning")
        self.assertEqual(alert.message, "File requires attention: suspicious extension .sh")

    def test_build_alert_for_failed_file(self) -> None:
        file_item = SimpleNamespace(
            id=14,
            processing_status="failed",
            requires_attention=False,
            scan_details=None,
        )

        alert = build_alert(file_item)

        self.assertEqual(alert.file_id, 14)
        self.assertEqual(alert.level, "critical")
        self.assertEqual(alert.message, "File processing failed")


if __name__ == "__main__":
    unittest.main()
