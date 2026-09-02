class NotebookError(Exception):
    """Базовое исключение для ошибок обработки notebook'ов."""


class NotebookNotFoundError(NotebookError):
    """Входной файл notebook'а не найден."""


class InvalidNotebookError(NotebookError):
    """Файл notebook'а содержит некорректный JSON."""
