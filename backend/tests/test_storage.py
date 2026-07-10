import tempfile
import unittest
from pathlib import Path

from src import storage


class FakeUploadFile:
    def __init__(self, chunks: list[bytes]) -> None:
        self._chunks = chunks

    async def read(self, size: int = -1) -> bytes:
        return self._chunks.pop(0) if self._chunks else b""


class StorageTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self._original_storage_dir = storage.STORAGE_DIR
        self._temp_dir = tempfile.TemporaryDirectory()
        storage.STORAGE_DIR = Path(self._temp_dir.name)

    async def asyncTearDown(self) -> None:
        storage.STORAGE_DIR = self._original_storage_dir
        self._temp_dir.cleanup()

    async def test_save_upload_file_writes_chunks_and_returns_size(self) -> None:
        upload_file = FakeUploadFile([b"hello ", b"world"])

        size = await storage.save_upload_file(upload_file, "stored.txt")

        stored_path = storage.get_stored_path("stored.txt")
        self.assertEqual(size, 11)
        self.assertEqual(stored_path.read_bytes(), b"hello world")

    async def test_save_upload_file_removes_empty_file(self) -> None:
        upload_file = FakeUploadFile([])

        size = await storage.save_upload_file(upload_file, "empty.txt")

        self.assertEqual(size, 0)
        self.assertFalse(storage.get_stored_path("empty.txt").exists())

    async def test_delete_stored_file_is_idempotent(self) -> None:
        stored_path = storage.get_stored_path("stored.txt")
        stored_path.write_bytes(b"data")

        storage.delete_stored_file("stored.txt")
        storage.delete_stored_file("stored.txt")

        self.assertFalse(stored_path.exists())


if __name__ == "__main__":
    unittest.main()
