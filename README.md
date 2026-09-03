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
jupyter-cleaner convert PATH [--keep-outputs] [--no-tables] [--output PATH]
```

* `PATH` — путь к исходному `.ipynb` или каталогу с notebook-файлами;
* `--keep-outputs` — сохранить поддерживаемые текстовые результаты выполнения;
* `--no-tables` — не преобразовывать HTML-таблицы Pandas в Markdown-таблицы;
* `--output PATH`, `-o PATH` — записать результат по указанному пути.

Если указан каталог, команда преобразует все файлы `*.ipynb`, находящиеся
непосредственно в нём, в алфавитном порядке. Вложенные каталоги не
просматриваются. Для каждого notebook файл `.md` создаётся рядом с исходником,
поэтому `--output` в каталоговом режиме использовать нельзя. Ошибка в одном
файле не останавливает обработку остальных; итоговая сводка показывает число
успешных и неуспешных преобразований.


Примеры:

```bash
uv run jupyter-cleaner convert examples/table.ipynb --keep-outputs
uv run jupyter-cleaner convert examples/table.ipynb --keep-outputs --no-tables
uv run jupyter-cleaner convert examples/basic.ipynb -o examples/custom.md
uv run jupyter-cleaner convert examples/
uv run jupyter-cleaner convert --help
```

При ошибке (например, если входной файл отсутствует или содержит некорректный
JSON) команда выводит понятное сообщение и завершается с ненулевым кодом.