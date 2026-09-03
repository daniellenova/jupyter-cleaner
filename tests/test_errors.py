import json
from pathlib import Path

import pytest

from jupyter_cleaner.converter import load_notebook
from jupyter_cleaner.exceptions import InvalidNotebookError, NotebookNotFoundError

FIXTURES = Path(__file__).parent / "fixtures"


def test_load_notebook_raises_domain_error_for_missing_file(tmp_path: Path) -> None:
    missing_notebook = tmp_path / "missing.ipynb"

    with pytest.raises(NotebookNotFoundError) as exc_info:
        load_notebook(missing_notebook)

    assert exc_info.value.file_path == missing_notebook
    assert isinstance(exc_info.value.__cause__, FileNotFoundError)


def test_load_notebook_raises_domain_error_for_broken_json() -> None:
    broken_notebook = FIXTURES / "broken.ipynb"

    with pytest.raises(InvalidNotebookError) as exc_info:
        load_notebook(broken_notebook)

    assert exc_info.value.file_path == broken_notebook
    assert isinstance(exc_info.value.__cause__, json.JSONDecodeError)


def test_load_notebook_rejects_valid_json_with_invalid_structure(tmp_path: Path) -> None:
    invalid_notebook = tmp_path / "invalid-structure.ipynb"
    invalid_notebook.write_text('{"cells": "not a list"}', encoding="utf-8")

    with pytest.raises(InvalidNotebookError) as exc_info:
        load_notebook(invalid_notebook)

    assert exc_info.value.file_path == invalid_notebook
