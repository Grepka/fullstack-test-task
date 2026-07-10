class DomainError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    pass


class FileNotFound(NotFoundError):
    def __init__(self) -> None:
        super().__init__("File not found")


class StoredFileMissing(NotFoundError):
    def __init__(self) -> None:
        super().__init__("Stored file not found")


class EmptyFileError(DomainError):
    def __init__(self) -> None:
        super().__init__("File is empty")
