"""Распознавание и преобразование поддерживаемых HTML-таблиц Pandas."""

import html


class TableConverter:
    """Преобразует зафиксированный формат HTML-таблицы Pandas в Markdown."""

    def is_supported(self, html_text: str) -> bool:
        """Проверяет, соответствует ли HTML поддерживаемому формату Pandas."""
        return self._parse(html_text) is not None

    def convert(self, html_text: str) -> str | None:
        """Возвращает Markdown-таблицу либо ``None`` для неподдерживаемого HTML."""
        rows = self._parse(html_text)
        if rows is None:
            return None
        markdown_rows = ["| " + " | ".join(row) + " |" for row in rows]
        markdown_rows.insert(1, "|" + "---|" * len(rows[0]))
        return "\n".join(markdown_rows)

    @staticmethod
    def _opening_tag_end(html_text: str, tag_name: str, start: int) -> int:
        prefix = f"<{tag_name}"
        if not html_text.startswith(prefix, start):
            return -1
        name_end = start + len(prefix)
        if name_end >= len(html_text) or html_text[name_end] not in " \t\r\n>":
            return -1
        return html_text.find(">", name_end)

    def _extract_blocks(self, html_text: str, tag_name: str) -> list[str] | None:
        blocks: list[str] = []
        position = 0
        closing_tag = f"</{tag_name}>"
        while position < len(html_text):
            while position < len(html_text) and html_text[position].isspace():
                position += 1
            if position == len(html_text):
                break
            opening_end = self._opening_tag_end(html_text, tag_name, position)
            if opening_end == -1:
                return None
            closing_start = html_text.find(closing_tag, opening_end + 1)
            if closing_start == -1:
                return None
            blocks.append(html_text[opening_end + 1 : closing_start])
            position = closing_start + len(closing_tag)
        return blocks

    def _extract_cells(self, row_html: str) -> list[tuple[str, str]] | None:
        cells: list[tuple[str, str]] = []
        position = 0
        while position < len(row_html):
            while position < len(row_html) and row_html[position].isspace():
                position += 1
            if position == len(row_html):
                break
            tag_name = next(
                (
                    name
                    for name in ("th", "td")
                    if self._opening_tag_end(row_html, name, position) != -1
                ),
                None,
            )
            if tag_name is None:
                return None
            opening_end = self._opening_tag_end(row_html, tag_name, position)
            opening_tag = row_html[position : opening_end + 1].lower()
            if "rowspan" in opening_tag or "colspan" in opening_tag:
                return None
            closing_tag = f"</{tag_name}>"
            closing_start = row_html.find(closing_tag, opening_end + 1)
            if closing_start == -1:
                return None
            value = row_html[opening_end + 1 : closing_start]
            if "<" in value or ">" in value:
                return None
            value = html.unescape(value)
            value = value.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
            cells.append((tag_name, value.strip().replace("|", "\\|")))
            position = closing_start + len(closing_tag)
        return cells

    def _has_supported_wrapper(self, prefix: str, suffix: str) -> bool:
        position = 0
        while position < len(prefix) and prefix[position].isspace():
            position += 1
        has_div = False
        div_end = self._opening_tag_end(prefix, "div", position)
        if div_end != -1:
            has_div = True
            position = div_end + 1
            while position < len(prefix) and prefix[position].isspace():
                position += 1
        style_end = self._opening_tag_end(prefix, "style", position)
        if style_end != -1:
            style_close = prefix.find("</style>", style_end + 1)
            style_body = prefix[style_end + 1 : style_close]
            if style_close == -1 or "<" in style_body or ">" in style_body:
                return False
            position = style_close + len("</style>")
        if prefix[position:].strip():
            return False
        return suffix.strip() == ("</div>" if has_div else "")

    def _parse(self, html_text: str) -> list[list[str]] | None:
        table_start = html_text.find("<table")
        if table_start == -1:
            return None
        table_open_end = self._opening_tag_end(html_text, "table", table_start)
        if table_open_end == -1:
            return None
        opening_tag = html_text[table_start : table_open_end + 1]
        attributes = opening_tag[len("<table") : -1].replace("'", '"')
        class_marker = 'class="'
        class_start = attributes.find(class_marker)
        while class_start > 0 and not attributes[class_start - 1].isspace():
            class_start = attributes.find(class_marker, class_start + len(class_marker))
        if class_start == -1:
            return None
        class_end = attributes.find('"', class_start + len(class_marker))
        classes = attributes[class_start + len(class_marker) : class_end].split()
        if class_end == -1 or "dataframe" not in classes:
            return None
        table_close = html_text.find("</table>", table_open_end + 1)
        if table_close == -1 or not self._has_supported_wrapper(
            html_text[:table_start], html_text[table_close + len("</table>") :]
        ):
            return None
        table_body = html_text[table_open_end + 1 : table_close]
        if (
            "<table" in table_body
            or "rowspan" in table_body.lower()
            or "colspan" in table_body.lower()
        ):
            return None
        sections: list[str] = []
        position = 0
        for section_name in ("thead", "tbody"):
            while position < len(table_body) and table_body[position].isspace():
                position += 1
            section_open_end = self._opening_tag_end(table_body, section_name, position)
            if section_open_end == -1:
                return None
            close_tag = f"</{section_name}>"
            section_close = table_body.find(close_tag, section_open_end + 1)
            if section_close == -1:
                return None
            sections.append(table_body[section_open_end + 1 : section_close])
            position = section_close + len(close_tag)
        if table_body[position:].strip():
            return None
        header_rows = self._extract_blocks(sections[0], "tr")
        data_rows = self._extract_blocks(sections[1], "tr")
        if header_rows is None or len(header_rows) != 1 or not data_rows:
            return None
        optional_rows = [self._extract_cells(row) for row in header_rows + data_rows]
        if any(not row for row in optional_rows):
            return None
        parsed_rows = [row for row in optional_rows if row is not None]
        column_count = len(parsed_rows[0])
        if any(len(row) != column_count for row in parsed_rows):
            return None
        if any(tag != "th" for tag, _ in parsed_rows[0]):
            return None
        if any(
            row[0][0] != "th" or any(tag != "td" for tag, _ in row[1:]) for row in parsed_rows[1:]
        ):
            return None
        return [[value for _, value in row] for row in parsed_rows]
