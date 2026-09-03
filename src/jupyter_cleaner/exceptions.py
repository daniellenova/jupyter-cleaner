from pathlib import Path


class NotebookError(Exception):
    """Базовое исключение для ошибок обработки notebook'ов."""

    def __init__(self, file_path: Path) -> None:
        self.file_path: Path = file_path
        super().__init__(str(file_path))


class NotebookNotFoundError(NotebookError):
    """Входной файл notebook'а не найден."""


class InvalidNotebookError(NotebookError):
    """Файл notebook'а содержит некорректный JSON."""
