from dataclasses import dataclass, field


@dataclass(frozen=True)
class ConversionConfig:
    """Настройки одного преобразования notebook в Markdown."""

    keep_outputs: bool = False


@dataclass
class ConversionStats:
    """Статистика одного преобразования notebook в Markdown."""

    cells_total: int = 0
    code_cells: int = 0
    markdown_cells: int = 0
    empty_cells_removed: int = 0
    outputs_total: int = 0
    text_outputs_kept: int = 0
    html_outputs_skipped: int = 0
    tables_converted: int = 0
    input_size_bytes: int = 0
    output_size_bytes: int = 0
    size_reduction_percent: float = 0.0


@dataclass
class ConversionResult:
    """Текст и статистика завершённого преобразования."""

    markdown_text: str
    stats: ConversionStats = field(default_factory=ConversionStats)
