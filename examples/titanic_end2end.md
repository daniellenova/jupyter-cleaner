# Импорт необходимых библиотек

```python
import random
import warnings
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

# Импорт функции для разделения данных на обучающую и тестовую выборки
from sklearn.model_selection import train_test_split

# Импорт класса для выполнения сеточного поиска с кросс-валидацией
from sklearn.model_selection import GridSearchCV

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.ensemble import AdaBoostClassifier

from sklearn.metrics import f1_score

warnings.filterwarnings('ignore')

# Фиксация случайного seed для воспроизводимости результатов
random.seed(0)
```

# 13.1 Загрузка и исследование набора данных

Сначала используем pd для загрузки набора данных из CSV файла

```python
# Загрузка сырых данных из CSV файла
raw_data = pd.read_csv('data/titanic.csv')
raw_data
```

```text
     PassengerId  Survived  Pclass  \
0              1         0       3   
1              2         1       1   
2              3         1       3   
3              4         1       1   
4              5         0       3   
..           ...       ...     ...   
886          887         0       2   
887          888         1       1   
888          889         0       3   
889          890         1       1   
890          891         0       3   

                                                  Name     Sex   Age  SibSp  \
0                              Braund, Mr. Owen Harris    male  22.0      1   
1    Cumings, Mrs. John Bradley (Florence Briggs Th...  female  38.0      1   
2                               Heikkinen, Miss. Laina  female  26.0      0   
3         Futrelle, Mrs. Jacques Heath (Lily May Peel)  female  35.0      1   
4                             Allen, Mr. William Henry    male  35.0      0   
..                                                 ...     ...   ...    ...   
886                              Montvila, Rev. Juozas    male  27.0      0   
887                       Graham, Miss. Margaret Edith  female  19.0      0   
888           Johnston, Miss. Catherine Helen "Carrie"  female   NaN      1   
889                              Behr, Mr. Karl Howell    male  26.0      0   
890                                Dooley, Mr. Patrick    male  32.0      0   

     Parch            Ticket     Fare Cabin Embarked  
0        0         A/5 21171   7.2500   NaN        S  
1        0          PC 17599  71.2833   C85        C  
2        0  STON/O2. 3101282   7.9250   NaN        S  
3        0            113803  53.1000  C123        S  
4        0            373450   8.0500   NaN        S  
..     ...               ...      ...   ...      ...  
886      0            211536  13.0000   NaN        S  
887      0            112053  30.0000   B42        S  
888      2        W./C. 6607  23.4500   NaN        S  
889      0            111369  30.0000  C148        C  
890      0            370376   7.7500   NaN        Q  

[891 rows x 12 columns]
```

**Столбцы набора данных:**

 - **PassengerID** - номер, идентифицирующий каждого пассажира от 1 до 891
 - **Name** - полное имя пассажира
 - **Sex** - пол пассажира (мужчина или женщина)
 - **Age** - возраст пассажира в виде целого числа
 - **Pclass** - класс, в котором путешествовал пассажир, - первый, второй или третий
 - **SibSP** - количество братьев, сестер и супругов пассажира (0, если он путешествовал один)
 - **Parch** - количество родителей и детей пассажира (0, если он путешествовал один)
 - **Ticket** - номер билета
 - **Fare** - стоимость проезда в британских фунтах стерлингов
 - **Cabin** - каюта, в которой путешествовал пассажир
 - **Embarked** - порт, в котором пассажир взошел на борт: "C" для Шербура, "Q" для Квинстауна и "S" для Саутгемптона
 - **Survived** - информация о том, выжил пассажир (1) или нет (0)

Далее мы можем исследовать набор данных более подробно

```python
# Исследование длины набора данных (количество строк)
print("Набор данных содержит", len(raw_data), "строк")

# Исследование столбцов в наборе данных (признаки/features)
print("Столбцы (признаки набора данных)")
raw_data.columns.to_list()
```

```text
Набор данных содержит 891 строк
Столбцы (признаки набора данных)
```

```text
['PassengerId',
 'Survived',
 'Pclass',
 'Name',
 'Sex',
 'Age',
 'SibSp',
 'Parch',
 'Ticket',
 'Fare',
 'Cabin',
 'Embarked']
```

```python
# Исследование меток (целевой переменной - выжил или нет)
print("Метки (целевая переменная)")
raw_data["Survived"]
```

```text
Метки (целевая переменная)
```

```text
0      0
1      1
2      1
3      1
4      0
      ..
886    0
887    1
888    0
889    1
890    0
Name: Survived, Length: 891, dtype: int64
```

```python
# Подсчет количества выживших пассажиров
print(sum(raw_data['Survived']), 'пассажиров выжило из', len(raw_data))

# Можно посмотреть на несколько столбцов вместе
# Выбор только столбцов с именем и возрастом для просмотра
raw_data[["Name", "Age"]]
```

```text
342 пассажиров выжило из 891
```

```text
                                                  Name   Age
0                              Braund, Mr. Owen Harris  22.0
1    Cumings, Mrs. John Bradley (Florence Briggs Th...  38.0
2                               Heikkinen, Miss. Laina  26.0
3         Futrelle, Mrs. Jacques Heath (Lily May Peel)  35.0
4                             Allen, Mr. William Henry  35.0
..                                                 ...   ...
886                              Montvila, Rev. Juozas  27.0
887                       Graham, Miss. Margaret Edith  19.0
888           Johnston, Miss. Catherine Helen "Carrie"   NaN
889                              Behr, Mr. Karl Howell  26.0
890                                Dooley, Mr. Patrick  32.0

[891 rows x 2 columns]
```

# 13.2 Очистка данных

Теперь посмотрим, сколько столбцов имеют пропущенные данные

```python
# Подсчет пропущенных значений (NaN) в каждом столбце
raw_data.isna().sum()
```

```text
PassengerId      0
Survived         0
Pclass           0
Name             0
Sex              0
Age            177
SibSp            0
Parch            0
Ticket           0
Fare             0
Cabin          687
Embarked         2
dtype: int64
```

Столбец Cabin пропускает слишком много значений, чтобы быть полезным. Удалим его полностью.

```python
# Подсчет точного количества пропущенных значений в столбце Cabin
print("В столбце Cabin пропущено", sum(raw_data['Cabin'].isna()), "значений из", len(raw_data['Cabin']))
```

```text
В столбце Cabin пропущено 687 значений из 891
```

```python
# Создание очищенной версии данных без столбца Cabin
# axis=1 указывает, что мы удаляем столбец (а не строку)
clean_data = raw_data.drop('Cabin', axis=1)
```

Другие столбцы, такие как Age или Embarked, пропускают некоторые значения, но они все еще могут быть полезны.  
Для столбца Age заполним пропущенные значения медианой всех возрастов.

```python
# Вычисление медианного возраста из исходных данных
median_age = raw_data["Age"].median()
print(median_age)

# Заполнение пропущенных значений в столбце Age медианным значением
clean_data["Age"] = clean_data["Age"].fillna(median_age)

# Для столбца Embarked создадим новую категорию 'U' (Unknown) для неизвестного порта посадки
clean_data["Embarked"] = clean_data["Embarked"].fillna('U')
```

```text
28.0
```

```python
# Проверка, что больше нет пропущенных значений
clean_data.isna().sum()
```

```text
PassengerId    0
Survived       0
Pclass         0
Name           0
Sex            0
Age            0
SibSp          0
Parch          0
Ticket         0
Fare           0
Embarked       0
dtype: int64
```

```python
clean_data
```

```text
     PassengerId  Survived  Pclass  \
0              1         0       3   
1              2         1       1   
2              3         1       3   
3              4         1       1   
4              5         0       3   
..           ...       ...     ...   
886          887         0       2   
887          888         1       1   
888          889         0       3   
889          890         1       1   
890          891         0       3   

                                                  Name     Sex   Age  SibSp  \
0                              Braund, Mr. Owen Harris    male  22.0      1   
1    Cumings, Mrs. John Bradley (Florence Briggs Th...  female  38.0      1   
2                               Heikkinen, Miss. Laina  female  26.0      0   
3         Futrelle, Mrs. Jacques Heath (Lily May Peel)  female  35.0      1   
4                             Allen, Mr. William Henry    male  35.0      0   
..                                                 ...     ...   ...    ...   
886                              Montvila, Rev. Juozas    male  27.0      0   
887                       Graham, Miss. Margaret Edith  female  19.0      0   
888           Johnston, Miss. Catherine Helen "Carrie"  female  28.0      1   
889                              Behr, Mr. Karl Howell    male  26.0      0   
890                                Dooley, Mr. Patrick    male  32.0      0   

     Parch            Ticket     Fare Embarked  
0        0         A/5 21171   7.2500        S  
1        0          PC 17599  71.2833        C  
2        0  STON/O2. 3101282   7.9250        S  
3        0            113803  53.1000        S  
4        0            373450   8.0500        S  
..     ...               ...      ...      ...  
886      0            211536  13.0000        S  
887      0            112053  30.0000        S  
888      2        W./C. 6607  23.4500        S  
889      0            111369  30.0000        C  
890      0            370376   7.7500        Q  

[891 rows x 11 columns]
```

# 13.3 Сохранение наших данных для будущего использования

```python
# Сохранение очищенных данных в CSV файл без индекса (index=None)
# clean_data.to_csv('data/clean_titanic_data.csv', index=None)
```

## 13.3.1 One-hot encoding (Однократное кодирование)

```python
# Загрузка предварительно очищенных данных из CSV файла
# preprocessed_data = pd.read_csv('clean_titanic_data.csv')
preprocessed_data = clean_data
```

```python
# Однократное кодирование признака пола (столбец Sex)
gender_columns = pd.get_dummies(preprocessed_data['Sex'], prefix='Sex')

# Однократное кодирование признака порта посадки (Embarked)
embarked_columns = pd.get_dummies(preprocessed_data["Embarked"], prefix="Embarked")

# Вывод созданных столбцов
print(gender_columns)
```

```text
     Sex_female  Sex_male
0         False      True
1          True     False
2          True     False
3          True     False
4         False      True
..          ...       ...
886       False      True
887        True     False
888        True     False
889       False      True
890       False      True

[891 rows x 2 columns]
```

```python
# Добавление созданных столбцов к основному DataFrame (axis=1 это добавление по столбцам)
preprocessed_data = pd.concat([preprocessed_data, gender_columns], axis=1)
preprocessed_data = pd.concat([preprocessed_data, embarked_columns], axis=1)

# Удаление исходных категориальных столбцов, которые были преобразованы
preprocessed_data = preprocessed_data.drop(['Sex', 'Embarked'], axis=1)
```

## 13.3.2 Эмпирическое правило для принятия решения о необходимости one-hot encoding

```python
# Создание DataFrame только с классом билета и целевой переменной
class_survived = preprocessed_data[['Pclass', 'Survived']]

# Разделение данных по классам билета
first_class = class_survived[class_survived['Pclass'] == 1]  # Первый класс
second_class = class_survived[class_survived['Pclass'] == 2]  # Второй класс
third_class = class_survived[class_survived['Pclass'] == 3]  # Третий класс

# Расчет процента выживших в каждом классе
print(f"В первом классе {sum(first_class['Survived']) / len(first_class) * 100:.2f} % пассажиров выжило")
print(f"Во втором классе {sum(first_class['Survived']) / len(second_class) * 100:.2f} % пассажиров выжило")
print(f"В третьем классе {sum(first_class['Survived']) / len(third_class) * 100:.2f} % пассажиров выжило")
```

```text
В первом классе 62.96 % пассажиров выжило
Во втором классе 73.91 % пассажиров выжило
В третьем классе 27.70 % пассажиров выжило
```

```python
# Однократное кодирование признака класса билета (Pclass)
categorized_pclass_columns = pd.get_dummies(preprocessed_data['Pclass'], prefix='Pclass')

# Добавление новых столбцов к данным
preprocessed_data = pd.concat([preprocessed_data, categorized_pclass_columns], axis=1)

# Удаление исходного столбца Pclass
preprocessed_data = preprocessed_data.drop(['Pclass'], axis=1)
```

## 13.3.3 Binning (Дискретизация/биннинг)

```python
# Определение границ интервалов для возраста
bins = [0, 10, 20, 30, 40, 50, 60, 70, 80]

# Разделение возраста на категории (бинны)
categorized_age = pd.cut(preprocessed_data['Age'], bins)

# Добавление новой колонки с категоризированным возрастом
preprocessed_data['Categorized_age'] = categorized_age

# Удаление исходного столбца с непрерывным возрастом
preprocessed_data = preprocessed_data.drop(["Age"], axis=1)
```

```python
# Однократное кодирование категоризированного возраста
cagegorized_age_columns = pd.get_dummies(preprocessed_data['Categorized_age'], prefix='Categorized_age')

# Добавление новых столбцов к данным
preprocessed_data = pd.concat([preprocessed_data, cagegorized_age_columns], axis=1)

# Удаление промежуточного столбца с категориями
preprocessed_data = preprocessed_data.drop(['Categorized_age'], axis=1)
```

## 13.3.4 Feature selection (Отбор признаков)

Удаление столбцов, которые не несут полезной информации для моделирования

```python
# Name - имена пассажиров (уникальные значения)
# Ticket - номер билета (часто уникальные значения)
# PassengerId - идентификатор пассажира (уникальные значения)
preprocessed_data = preprocessed_data.drop(['Name', 'Ticket', 'PassengerId'], axis=1)
preprocessed_data
```

```text
     Survived  SibSp  Parch     Fare  Sex_female  Sex_male  Embarked_C  \
0           0      1      0   7.2500       False      True       False   
1           1      1      0  71.2833        True     False        True   
2           1      0      0   7.9250        True     False       False   
3           1      1      0  53.1000        True     False       False   
4           0      0      0   8.0500       False      True       False   
..        ...    ...    ...      ...         ...       ...         ...   
886         0      0      0  13.0000       False      True       False   
887         1      0      0  30.0000        True     False       False   
888         0      1      2  23.4500        True     False       False   
889         1      0      0  30.0000       False      True        True   
890         0      0      0   7.7500       False      True       False   

     Embarked_Q  Embarked_S  Embarked_U  ...  Pclass_2  Pclass_3  \
0         False        True       False  ...     False      True   
1         False       False       False  ...     False     False   
2         False        True       False  ...     False      True   
3         False        True       False  ...     False     False   
4         False        True       False  ...     False      True   
..          ...         ...         ...  ...       ...       ...   
886       False        True       False  ...      True     False   
887       False        True       False  ...     False     False   
888       False        True       False  ...     False      True   
889       False       False       False  ...     False     False   
890        True       False       False  ...     False      True   

     Categorized_age_(0, 10]  Categorized_age_(10, 20]  \
0                      False                     False   
1                      False                     False   
2                      False                     False   
3                      False                     False   
4                      False                     False   
..                       ...                       ...   
886                    False                     False   
887                    False                      True   
888                    False                     False   
889                    False                     False   
890                    False                     False   

     Categorized_age_(20, 30]  Categorized_age_(30, 40]  \
0                        True                     False   
1                       False                      True   
2                        True                     False   
3                       False                      True   
4                       False                      True   
..                        ...                       ...   
886                      True                     False   
887                     False                     False   
888                      True                     False   
889                      True                     False   
890                     False                      True   

     Categorized_age_(40, 50]  Categorized_age_(50, 60]  \
0                       False                     False   
1                       False                     False   
2                       False                     False   
3                       False                     False   
4                       False                     False   
..                        ...                       ...   
886                     False                     False   
887                     False                     False   
888                     False                     False   
889                     False                     False   
890                     False                     False   

     Categorized_age_(60, 70]  Categorized_age_(70, 80]  
0                       False                     False  
1                       False                     False  
2                       False                     False  
3                       False                     False  
4                       False                     False  
..                        ...                       ...  
886                     False                     False  
887                     False                     False  
888                     False                     False  
889                     False                     False  
890                     False                     False  

[891 rows x 21 columns]
```

## 13.3.5 Сохранение для будущего использования

```python
# Сохранение полностью предобработанных данных в CSV файл
# preprocessed_data.to_csv('preprocessed_titanic_data.csv', index=None)
```

# 13.4 Обучение моделей

```python
# Загрузка предобработанных данных для обучения моделей
# data = pd.read_csv('./preprocessed_titanic_data.csv')
data = preprocessed_data
```

## 13.4.1 Разделение на признаки-метки и train-validation-test разделение

```python
# Разделение данных на признаки (X) и целевую переменную (y)
# Удаляем столбец "Survived" из признаков - это будет наша целевая переменная
features = data.drop(["Survived"], axis=1)

# Выделяем целевую переменную (метки) - столбец "Survived"
labels = data["Survived"]
```

```python
# Примечание: фиксируем random_state для воспроизводимости результатов
# Первое разделение: 60% train, 40% validation+test
features_train, features_validation_test, labels_train, labels_validation_test = train_test_split(features, 
                                                                                                  labels, 
                                                                                                  test_size=0.4, 
                                                                                                  random_state=100)

# Второе разделение: делим validation+test пополам (50/50) на validation и test
# В результате: 60% train, 20% validation, 20% test
features_validation, features_test, labels_validation, labels_test = train_test_split(features_validation_test, 
                                                                                      labels_validation_test, 
                                                                                      test_size=0.5, 
                                                                                      random_state=100)

# Вывод размеров полученных выборок
print(f"| {'Выборка':^30} | {'Features':^10} | {'Labels':^10}  |")
print('|' + "-" * 59 + '|')
print(f"| {'Обучающая (Train)':<30} | {len(features_train):>10} | {len(labels_train):>10}  |")
print(f"| {'Валидационная (Validation)':<30} | {len(features_validation):>10} | {len(labels_validation):>10}  |")
print(f"| {'Тестовая (Test)':<30} | {len(features_test):>10} | {len(labels_test):>10}  |")
```

```text
|            Выборка             |  Features  |   Labels    |
|-----------------------------------------------------------|
| Обучающая (Train)              |        534 |        534  |
| Валидационная (Validation)     |        178 |        178  |
| Тестовая (Test)                |        179 |        179  |
```

## 13.4.2 Обучение различных моделей на нашем наборе данных

Мы обучим семь моделей машинного обучения:

```python
# 1. Логистическая регрессия (линейная модель)
# Создание и обучение модели логистической регрессии
lr_model = LogisticRegression()
lr_model.fit(features_train, labels_train)  # Обучение на тренировочных данных
```

```text
LogisticRegression()
```

```python
# 2. Дерево решений (нелинейная модель)
# Создание и обучение модели дерева решений
dt_model = DecisionTreeClassifier()
dt_model.fit(features_train, labels_train)
```

```text
DecisionTreeClassifier()
```

```python
# 3. Наивный Байес (вероятностная модель)
# Создание и обучение модели наивного Байеса
nb_model = GaussianNB()
nb_model.fit(features_train, labels_train)
```

```text
GaussianNB()
```

```python
# 4. Метод опорных векторов (SVM) 
# Создание и обучение SVM модели
svm_model = SVC()
svm_model.fit(features_train, labels_train)
```

```text
SVC()
```

```python
# 5. Случайный лес (ансамблевая модель)
# Создание и обучение модели случайного леса
rf_model = RandomForestClassifier()
rf_model.fit(features_train, labels_train)
```

```text
RandomForestClassifier()
```

```python
# 6. Градиентный бустинг (ансамблевая модель)
# Создание и обучение модели градиентного бустинга
gb_model = GradientBoostingClassifier()
gb_model.fit(features_train, labels_train)
```

```text
GradientBoostingClassifier()
```

```python
# 7. AdaBoost (адаптивный бустинг, ансамблевая модель)
# Создание и обучение модели AdaBoost
ab_model = AdaBoostClassifier()
ab_model.fit(features_train, labels_train)
```

```text
AdaBoostClassifier()
```

## 13.4.3 Оценка моделей

- Оценка точности (Accuracy) - доля правильных прогнозов
- Оценка F1-меры - гармоническое среднее точности и полноты

```python
# Сбор результатов в список словарей
results = []

# Логистическая регрессия
results.append({
    "Модель": "Логистическая регрессия",
    "Accuracy": lr_model.score(features_validation, labels_validation),
    "F1-score": f1_score(labels_validation, lr_model.predict(features_validation))
})

# Дерево решений
results.append({
    "Модель": "Дерево решений",
    "Accuracy": dt_model.score(features_validation, labels_validation),
    "F1-score": f1_score(labels_validation, dt_model.predict(features_validation))
})

# Наивный Байес
results.append({
    "Модель": "Наивный Байес",
    "Accuracy": nb_model.score(features_validation, labels_validation),
    "F1-score": f1_score(labels_validation, nb_model.predict(features_validation))
})

# SVM
results.append({
    "Модель": "Метод опорных векторов",
    "Accuracy": svm_model.score(features_validation, labels_validation),
    "F1-score": f1_score(labels_validation, svm_model.predict(features_validation))
})

# Случайный лес
results.append({
    "Модель": "Случайный лес",
    "Accuracy": rf_model.score(features_validation, labels_validation),
    "F1-score": f1_score(labels_validation, rf_model.predict(features_validation))
})

# Градиентный бустинг
results.append({
    "Модель": "Градиентный бустинг",
    "Accuracy": gb_model.score(features_validation, labels_validation),
    "F1-score": f1_score(labels_validation, gb_model.predict(features_validation))
})

# AdaBoost
results.append({
    "Модель": "AdaBoost",
    "Accuracy": ab_model.score(features_validation, labels_validation),
    "F1-score": f1_score(labels_validation, ab_model.predict(features_validation))
})

# Создаем DataFrame
df_results = pd.DataFrame(results)

# Сортировка по Accuracy
df_sorted_acc = df_results.sort_values(by="Accuracy", ascending=False).reset_index(drop=True)

# Сортировка по Accuracy и F1-score
df_sorted_f1 = df_sorted_acc.sort_values(by="F1-score", ascending=False).reset_index(drop=True)
df_sorted_f1
```

|  | Модель | Accuracy | F1-score |
|---|---|---|---|
| 0 | Градиентный бустинг | 0.814607 | 0.744186 |
| 1 | Дерево решений | 0.780899 | 0.706767 |
| 2 | Случайный лес | 0.769663 | 0.691729 |
| 3 | Логистическая регрессия | 0.769663 | 0.687023 |
| 4 | Наивный Байес | 0.747191 | 0.680851 |
| 5 | AdaBoost | 0.735955 | 0.646617 |
| 6 | Метод опорных векторов | 0.679775 | 0.400000 |

## 13.4.4 Тестирование лучшей модели

Выбираем модель градиентного бустинга как лучшую (предположительно) и тестируем ее на тестовой выборке, которая не использовалась при обучении и валидации

```python
# Оценка точности на тестовой выборке
test_accuracy = gb_model.score(features_test, labels_test)
print(f"Точность градиентного бустинга на тестовой выборке: {test_accuracy:.3f}")

# Предсказание меток для тестовой выборки
gb_predicted_test_labels = gb_model.predict(features_test)

# Расчет F1-меры на тестовой выборке
test_f1_score = f1_score(labels_test, gb_predicted_test_labels)
print(f"F1-мера градиентного бустинга на тестовой выборке: {test_f1_score:.3f}")
```

```text
Точность градиентного бустинга на тестовой выборке: 0.832
F1-мера градиентного бустинга на тестовой выборке: 0.803
```

# 13.5 Grid search (Сеточный поиск)

**Сеточный поиск с ядром radial basis function (RBF)**

Создание и обучение SVM модели с различными гиперпараметрами:

 - C - параметр регуляризации
 - gamma - коэффициент ядра RBF

```python
results = []

# Список комбинаций параметров
params = [
    (1, 0.1),
    (1, 1),
    (1, 10),
    (10, 0.1),
    (10, 1),
    (10, 10),
]

# Перебор моделей
for C, gamma in params:
    model = SVC(kernel='rbf', C=C, gamma=gamma)
    
    model.fit(features_train, labels_train)
    
    acc = model.score(features_validation, labels_validation)
    results.append({"C": C, "gamma": gamma, "Accuracy": acc})

# Создаем DataFrame
df_svm = pd.DataFrame(results).sort_values(by="Accuracy", ascending=False).reset_index(drop=True)
df_svm
```

|  | C | gamma | Accuracy |
|---|---|---|---|
| 0 | 10 | 0.1 | 0.724719 |
| 1 | 1 | 0.1 | 0.702247 |
| 2 | 1 | 1.0 | 0.696629 |
| 3 | 10 | 1.0 | 0.691011 |
| 4 | 1 | 10.0 | 0.668539 |
| 5 | 10 | 10.0 | 0.651685 |

## Автоматизированный сеточный поиск с использованием GridSearchCV

```python
# Определение сетки гиперпараметров для поиска
svm_parameters = {
    'kernel': ['rbf'],  # Используем только RBF ядро
    'C': [0.01, 0.1, 1, 10, 100],  # Значения параметра регуляризации
    'gamma': [0.01, 0.1, 1, 10, 100]  # Значения параметра gamma для RBF ядра
}

# Создание базовой SVM модели
svm = SVC()
```

```python
# Создание объекта GridSearchCV для поиска лучших гиперпараметров
# estimator - модель для оптимизации
# param_grid - сетка гиперпараметров для поиска
# по умолчанию используется 5-кратная кросс-валидация
svm_gs = GridSearchCV(estimator=svm, param_grid=svm_parameters)

# Выполнение сеточного поиска на обучающих данных
svm_gs.fit(features_train, labels_train)
```

```text
GridSearchCV(estimator=SVC(),
             param_grid={'C': [0.01, 0.1, 1, 10, 100],
                         'gamma': [0.01, 0.1, 1, 10, 100], 'kernel': ['rbf']})
```

```python
# Получение лучшей модели с оптимальными гиперпараметрами
svm_winner = svm_gs.best_estimator_

# Вывод информации о лучшей модели
svm_winner
```

```text
SVC(C=10, gamma=0.01)
```

```python
# Оценка производительности лучшей модели на валидационной выборке
validation_score = svm_winner.score(features_validation, labels_validation)
print(f"Точность лучшей SVM модели на валидационной выборке: {validation_score:.4f}")
```

```text
Точность лучшей SVM модели на валидационной выборке: 0.7191
```

# 13.6 Cross validation (Кросс-валидация)

```python
# Просмотр подробных результатов кросс-валидации для всех комбинаций параметров
# cv_results_ содержит информацию о производительности каждой комбинации гиперпараметров
cv_results = svm_gs.cv_results_

# Вывод доступных ключей для просмотра результатов
print("Доступные метрики в cv_results_:")
for key in cv_results.keys():
    print(f"  - {key}")

# Пример просмотра некоторых результатов:
print("\nЛучшие параметры:")
for param, value in svm_gs.best_params_.items():
    print(f"  {param}: {value}")

print(f"\nЛучшая точность при кросс-валидации: {svm_gs.best_score_:.4f}")
```

```text
Доступные метрики в cv_results_:
  - mean_fit_time
  - std_fit_time
  - mean_score_time
  - std_score_time
  - param_C
  - param_gamma
  - param_kernel
  - params
  - split0_test_score
  - split1_test_score
  - split2_test_score
  - split3_test_score
  - split4_test_score
  - mean_test_score
  - std_test_score
  - rank_test_score

Лучшие параметры:
  C: 10
  gamma: 0.01
  kernel: rbf

Лучшая точность при кросс-валидации: 0.8072
```

```python
# Можно посмотреть результаты для всех комбинаций параметров:
print("\nРезультаты для всех комбинаций гиперпараметров:")

# Формируем DataFrame с параметрами и метриками
df_cv = pd.DataFrame({
    "Параметры": cv_results['params'],
    "Средняя точность": cv_results['mean_test_score'],
    "Стд. отклонение": cv_results['std_test_score']
})

# Добавляем колонку с "рангом" (место модели по точности)
df_cv["Ранг"] = cv_results["rank_test_score"]

# Сортируем по средней точности
df_cv = df_cv.sort_values(by="Средняя точность", ascending=False).reset_index(drop=True)
df_cv
```

```text

Результаты для всех комбинаций гиперпараметров:
```

|  | Параметры | Средняя точность | Стд. отклонение | Ранг |
|---|---|---|---|---|
| 0 | {'C': 10, 'gamma': 0.01, 'kernel': 'rbf'} | 0.807194 | 0.036873 | 1 |
| 1 | {'C': 100, 'gamma': 0.01, 'kernel': 'rbf'} | 0.803403 | 0.020179 | 2 |
| 2 | {'C': 1, 'gamma': 0.1, 'kernel': 'rbf'} | 0.764116 | 0.034760 | 3 |
| 3 | {'C': 10, 'gamma': 0.1, 'kernel': 'rbf'} | 0.754699 | 0.025174 | 4 |
| 4 | {'C': 100, 'gamma': 0.1, 'kernel': 'rbf'} | 0.749074 | 0.002821 | 5 |
| 5 | {'C': 10, 'gamma': 1, 'kernel': 'rbf'} | 0.722941 | 0.042357 | 6 |
| 6 | {'C': 1, 'gamma': 1, 'kernel': 'rbf'} | 0.722941 | 0.038918 | 6 |
| 7 | {'C': 100, 'gamma': 1, 'kernel': 'rbf'} | 0.713595 | 0.050199 | 8 |
| 8 | {'C': 1, 'gamma': 0.01, 'kernel': 'rbf'} | 0.698519 | 0.027777 | 9 |
| 9 | {'C': 1, 'gamma': 100, 'kernel': 'rbf'} | 0.696650 | 0.016952 | 10 |
| 10 | {'C': 100, 'gamma': 10, 'kernel': 'rbf'} | 0.694780 | 0.020617 | 11 |
| 11 | {'C': 100, 'gamma': 100, 'kernel': 'rbf'} | 0.694763 | 0.016139 | 12 |
| 12 | {'C': 10, 'gamma': 100, 'kernel': 'rbf'} | 0.694763 | 0.016139 | 12 |
| 13 | {'C': 10, 'gamma': 10, 'kernel': 'rbf'} | 0.692911 | 0.019522 | 14 |
| 14 | {'C': 1, 'gamma': 10, 'kernel': 'rbf'} | 0.692894 | 0.014712 | 15 |
| 15 | {'C': 0.1, 'gamma': 0.01, 'kernel': 'rbf'} | 0.657309 | 0.009237 | 16 |
| 16 | {'C': 0.01, 'gamma': 0.01, 'kernel': 'rbf'} | 0.646077 | 0.002433 | 17 |
| 17 | {'C': 0.1, 'gamma': 10, 'kernel': 'rbf'} | 0.646077 | 0.002433 | 17 |
| 18 | {'C': 0.1, 'gamma': 1, 'kernel': 'rbf'} | 0.646077 | 0.002433 | 17 |
| 19 | {'C': 0.1, 'gamma': 0.1, 'kernel': 'rbf'} | 0.646077 | 0.002433 | 17 |
| 20 | {'C': 0.01, 'gamma': 100, 'kernel': 'rbf'} | 0.646077 | 0.002433 | 17 |
| 21 | {'C': 0.01, 'gamma': 1, 'kernel': 'rbf'} | 0.646077 | 0.002433 | 17 |
| 22 | {'C': 0.01, 'gamma': 10, 'kernel': 'rbf'} | 0.646077 | 0.002433 | 17 |
| 23 | {'C': 0.01, 'gamma': 0.1, 'kernel': 'rbf'} | 0.646077 | 0.002433 | 17 |
| 24 | {'C': 0.1, 'gamma': 100, 'kernel': 'rbf'} | 0.646077 | 0.002433 | 17 |