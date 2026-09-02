"""Преобразование результатов выполнения Jupyter в Markdown."""

import html


def normalize_output_text(value):
    """Приводит строку или список строк результата к одной строке."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "".join(value)
    return None


def extract_text_output(output):
    """Возвращает обычный текст поддерживаемого результата, если он есть."""
    output_type = output.get("output_type")
    if output_type == "stream":
        return normalize_output_text(output.get("text"))
    if output_type in ("execute_result", "display_data"):
        data = output.get("data", {})
        if isinstance(data, dict) and "text/plain" in data:
            return normalize_output_text(data["text/plain"])
    return None


def extract_html_output(output):
    """Возвращает HTML-представление поддерживаемого результата, если оно есть."""
    if output.get("output_type") not in ("execute_result", "display_data"):
        return None
    data = output.get("data", {})
    if not isinstance(data, dict):
        return None
    return normalize_output_text(data.get("text/html"))


def has_html_output(output):
    """Проверяет наличие MIME-представления text/html."""
    data = output.get("data", {})
    return isinstance(data, dict) and "text/html" in data


def _opening_tag_end(html_text, tag_name, start):
    prefix = f"<{tag_name}"
    if not html_text.startswith(prefix, start):
        return -1
    name_end = start + len(prefix)
    if name_end >= len(html_text) or html_text[name_end] not in " \t\r\n>":
        return -1
    return html_text.find(">", name_end)


def _extract_blocks(html_text, tag_name):
    blocks = []
    position = 0
    closing_tag = f"</{tag_name}>"
    while position < len(html_text):
        while position < len(html_text) and html_text[position].isspace():
            position += 1
        if position == len(html_text):
            break
        opening_end = _opening_tag_end(html_text, tag_name, position)
        if opening_end == -1:
            return None
        closing_start = html_text.find(closing_tag, opening_end + 1)
        if closing_start == -1:
            return None
        blocks.append(html_text[opening_end + 1:closing_start])
        position = closing_start + len(closing_tag)
    return blocks


def _extract_cells(row_html):
    cells = []
    position = 0
    while position < len(row_html):
        while position < len(row_html) and row_html[position].isspace():
            position += 1
        if position == len(row_html):
            break
        tag_name = next((name for name in ("th", "td")
                         if _opening_tag_end(row_html, name, position) != -1), None)
        if tag_name is None:
            return None
        opening_end = _opening_tag_end(row_html, tag_name, position)
        opening_tag = row_html[position:opening_end + 1].lower()
        if "rowspan" in opening_tag or "colspan" in opening_tag:
            return None
        closing_tag = f"</{tag_name}>"
        closing_start = row_html.find(closing_tag, opening_end + 1)
        if closing_start == -1:
            return None
        value = row_html[opening_end + 1:closing_start]
        if "<" in value or ">" in value:
            return None
        value = html.unescape(value)
        value = value.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
        cells.append((tag_name, value.strip().replace("|", "\\|")))
        position = closing_start + len(closing_tag)
    return cells


def _has_supported_table_wrapper(prefix, suffix):
    position = 0
    while position < len(prefix) and prefix[position].isspace():
        position += 1
    has_div = False
    div_end = _opening_tag_end(prefix, "div", position)
    if div_end != -1:
        has_div = True
        position = div_end + 1
        while position < len(prefix) and prefix[position].isspace():
            position += 1
    style_end = _opening_tag_end(prefix, "style", position)
    if style_end != -1:
        style_close = prefix.find("</style>", style_end + 1)
        if style_close == -1 or "<" in prefix[style_end + 1:style_close] or ">" in prefix[style_end + 1:style_close]:
            return False
        position = style_close + len("</style>")
    if prefix[position:].strip():
        return False
    return suffix.strip() == ("</div>" if has_div else "")


def _parse_pandas_table(html_text):
    if not isinstance(html_text, str):
        return None
    table_start = html_text.find("<table")
    if table_start == -1:
        return None
    table_open_end = _opening_tag_end(html_text, "table", table_start)
    if table_open_end == -1:
        return None
    opening_tag = html_text[table_start:table_open_end + 1]
    attributes = opening_tag[len("<table"):-1].replace("'", '"')
    class_marker = 'class="'
    class_start = attributes.find(class_marker)
    while class_start > 0 and not attributes[class_start - 1].isspace():
        class_start = attributes.find(class_marker, class_start + len(class_marker))
    if class_start == -1:
        return None
    class_end = attributes.find('"', class_start + len(class_marker))
    if class_end == -1 or "dataframe" not in attributes[class_start + len(class_marker):class_end].split():
        return None
    table_close = html_text.find("</table>", table_open_end + 1)
    if table_close == -1 or not _has_supported_table_wrapper(
            html_text[:table_start], html_text[table_close + len("</table>"):]):
        return None
    table_body = html_text[table_open_end + 1:table_close]
    if "<table" in table_body or "rowspan" in table_body.lower() or "colspan" in table_body.lower():
        return None
    sections = []
    position = 0
    for section_name in ("thead", "tbody"):
        while position < len(table_body) and table_body[position].isspace():
            position += 1
        section_open_end = _opening_tag_end(table_body, section_name, position)
        if section_open_end == -1:
            return None
        close_tag = f"</{section_name}>"
        section_close = table_body.find(close_tag, section_open_end + 1)
        if section_close == -1:
            return None
        sections.append(table_body[section_open_end + 1:section_close])
        position = section_close + len(close_tag)
    if table_body[position:].strip():
        return None
    header_rows = _extract_blocks(sections[0], "tr")
    data_rows = _extract_blocks(sections[1], "tr")
    if header_rows is None or len(header_rows) != 1 or not data_rows:
        return None
    parsed_rows = [_extract_cells(row) for row in header_rows + data_rows]
    if any(not row for row in parsed_rows):
        return None
    column_count = len(parsed_rows[0])
    if any(len(row) != column_count for row in parsed_rows):
        return None
    if any(tag != "th" for tag, _ in parsed_rows[0]):
        return None
    if any(row[0][0] != "th" or any(tag != "td" for tag, _ in row[1:])
           for row in parsed_rows[1:]):
        return None
    return [[value for _, value in row] for row in parsed_rows]


def is_pandas_table(html_text):
    return _parse_pandas_table(html_text) is not None


def convert_pandas_table(html_text):
    rows = _parse_pandas_table(html_text)
    if rows is None:
        return None
    markdown_rows = ["| " + " | ".join(row) + " |" for row in rows]
    markdown_rows.insert(1, "|" + "---|" * len(rows[0]))
    return "\n".join(markdown_rows)


def _format_text_output(output_text):
    closing_separator = "" if output_text.endswith("\n") else "\n"
    return f"```text\n{output_text}{closing_separator}```"


def convert_output(output, stats=None):
    """Преобразует один поддерживаемый результат выполнения в Markdown."""
    html_text = extract_html_output(output)
    if html_text is not None:
        table = convert_pandas_table(html_text)
        if table is not None:
            if stats is not None:
                stats.tables_converted += 1
            return table

    text = extract_text_output(output)
    if text is None:
        return ""
    if stats is not None:
        stats.text_outputs_kept += 1
    return _format_text_output(text)


class OutputProcessor:
    """Преобразует поддерживаемые результаты выполнения в Markdown."""

    def process(self, outputs, config, stats):
        """Обрабатывает список outputs и обновляет только связанную статистику."""
        stats.outputs_total += len(outputs)
        stats.html_outputs_skipped += sum(has_html_output(output) for output in outputs)
        if not config.keep_outputs:
            return ""

        converted = [convert_output(output, stats) for output in outputs]
        return "\n\n".join(part for part in converted if part)
