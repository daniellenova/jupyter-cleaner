# Конвертер Jupyter notebook в чистый и компактный Markdown.

`jupyter-cleaner` преобразует Jupyter notebook (`.ipynb`) в чистый и
компактный Markdown.

## Запуск

Установить зависимости и преобразовать notebook можно через `uv`:

```bash
uv sync
uv run jupyter-cleaner convert examples/basic.ipynb
```

По умолчанию результат записывается рядом с notebook с расширением `.md`, а
результаты выполнения ячеек не включаются.

## Параметры `convert`

```text
jupyter-cleaner convert FILE [--keep-outputs] [--no-tables] [--output PATH]
```

* `FILE` — путь к исходному `.ipynb`;
* `--keep-outputs` — сохранить поддерживаемые текстовые результаты выполнения;
* `--no-tables` — не преобразовывать HTML-таблицы Pandas в Markdown-таблицы;
* `--output PATH`, `-o PATH` — записать результат по указанному пути.

Примеры:

```bash
uv run jupyter-cleaner convert examples/table.ipynb --keep-outputs
uv run jupyter-cleaner convert examples/table.ipynb --keep-outputs --no-tables
uv run jupyter-cleaner convert examples/basic.ipynb -o examples/custom.md
uv run jupyter-cleaner convert --help
```

При ошибке (например, если входной файл отсутствует или содержит некорректный
JSON) команда выводит понятное сообщение и завершается с ненулевым кодом.