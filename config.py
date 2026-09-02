"""Настройки преобразования Jupyter notebook в Markdown."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ConversionConfig:
    """Неизменяемые настройки одного запуска преобразования."""

    keep_outputs: bool = False
    remove_empty_cells: bool = True
    convert_tables: bool = True
