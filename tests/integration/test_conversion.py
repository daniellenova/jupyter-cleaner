from pathlib import Path

from jupyter_cleaner.config import ConversionConfig
from jupyter_cleaner.converter import NotebookConverter, load_notebook
from jupyter_cleaner.models import ConversionResult

FIXTURES = Path(__file__).parents[1] / "fixtures"


def test_dataframe_notebook_is_converted_to_expected_markdown(tmp_path: Path) -> None:
    notebook = load_notebook(FIXTURES / "dataframe.ipynb")
    config = ConversionConfig(keep_outputs=True)

    result = NotebookConverter(config).convert(notebook)
    output_path = tmp_path / "dataframe.md"
    output_path.write_text(result.markdown_text, encoding="utf-8")

    assert isinstance(result, ConversionResult)
    assert output_path.exists()
    markdown = output_path.read_text(encoding="utf-8")
    expected = (FIXTURES / "dataframe.expected.md").read_text(encoding="utf-8")
    assert markdown == expected
    assert "# DataFrame example" in markdown
    assert "single_quote = 'kept as an apostrophe'" in markdown
    assert 'double_quote = "kept as quotation marks"' in markdown
    assert "mixed_quotes = \"It's important to keep 'both' styles\"" in markdown
    assert "| 0 | Ada | 10 |" in markdown
    assert "<table" not in markdown
    assert "<style" not in markdown
    assert "  name  score\n0  Ada     10\n1  Lin     20" not in markdown


def test_dataframe_notebook_omits_all_outputs_when_disabled(tmp_path: Path) -> None:
    notebook = load_notebook(FIXTURES / "dataframe.ipynb")
    config = ConversionConfig(keep_outputs=False)

    result = NotebookConverter(config).convert(notebook)
    output_path = tmp_path / "dataframe-without-outputs.md"
    output_path.write_text(result.markdown_text, encoding="utf-8")

    assert output_path.exists()
    markdown = output_path.read_text(encoding="utf-8")
    assert (
        markdown
        == """# DataFrame example

A small table rendered from a pandas output.

```python
import pandas as pd
single_quote = 'kept as an apostrophe'
double_quote = "kept as quotation marks"
mixed_quotes = "It's important to keep 'both' styles"
```

```python
pd.DataFrame({'name': ['Ada', 'Lin'], 'score': [10, 20]})
```"""
    )
    assert "|  | name | score |" not in markdown
    assert "Ada | 10" not in markdown
    assert "name  score" not in markdown
    assert "<table" not in markdown
