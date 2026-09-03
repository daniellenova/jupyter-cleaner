from jupyter_cleaner.tables import TableConverter


def dataframe_html(*, heading: str = "name", value: str = "Ada") -> str:
    return f"""
<table class="dataframe">
  <thead>
    <tr><th></th><th>{heading}</th><th>score</th></tr>
  </thead>
  <tbody>
    <tr><th>0</th><td>{value}</td><td>10</td></tr>
    <tr><th>1</th><td>Lin</td><td>20</td></tr>
  </tbody>
</table>
"""


def test_pandas_dataframe_table_is_supported() -> None:
    assert TableConverter().is_supported(dataframe_html())


def test_ordinary_html_is_not_supported() -> None:
    assert not TableConverter().is_supported("<p>not a dataframe</p>")


def test_conversion_preserves_headers() -> None:
    converted = TableConverter().convert(dataframe_html())

    assert converted is not None
    assert converted.splitlines()[0] == "|  | name | score |"


def test_conversion_preserves_data_rows() -> None:
    converted = TableConverter().convert(dataframe_html())

    assert converted is not None
    assert converted.splitlines()[2:] == ["| 0 | Ada | 10 |", "| 1 | Lin | 20 |"]


def test_conversion_preserves_index() -> None:
    converted = TableConverter().convert(dataframe_html())

    assert converted is not None
    assert converted.splitlines()[2].startswith("| 0 |")


def test_conversion_preserves_column_count() -> None:
    converted = TableConverter().convert(dataframe_html())

    assert converted is not None
    assert converted.splitlines()[1] == "|---|---|---|"


def test_conversion_preserves_values() -> None:
    converted = TableConverter().convert(dataframe_html(value="Grace"))

    assert converted is not None
    assert "| 0 | Grace | 10 |" in converted


def test_conversion_decodes_html_entities() -> None:
    converted = TableConverter().convert(dataframe_html(heading="&lt;tag&gt;", value="A &amp; B"))

    assert converted is not None
    assert "<tag>" in converted
    assert "A & B" in converted


def test_conversion_escapes_pipe_inside_cell() -> None:
    converted = TableConverter().convert(dataframe_html(value="left|right"))

    assert converted is not None
    assert "| 0 | left\\|right | 10 |" in converted
