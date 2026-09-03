# DataFrame example

A small table rendered from a pandas output.

```python
import pandas as pd
single_quote = 'kept as an apostrophe'
double_quote = "kept as quotation marks"
mixed_quotes = "It's important to keep 'both' styles"
```

```python
pd.DataFrame({'name': ['Ada', 'Lin'], 'score': [10, 20]})
```

|  | name | score |
|---|---|---|
| 0 | Ada | 10 |
| 1 | Lin | 20 |