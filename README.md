# pandas-plots

![PyPI - Version](https://img.shields.io/pypi/v/pandas-plots) ![GitHub last commit](https://img.shields.io/github/last-commit/smeisegeier/pandas-plots?logo=github) ![GitHub License](https://img.shields.io/github/license/smeisegeier/pandas-plots?logo=github) ![py3.10](https://img.shields.io/badge/python-3.10-blue.svg?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTAwIj4KICA8ZGVmcz4KICAgIDxsaW5lYXJHcmFkaWVudCBpZD0icHlZZWxsb3ciIGdyYWRpZW50VHJhbnNmb3JtPSJyb3RhdGUoNDUpIj4KICAgICAgPHN0b3Agc3RvcC1jb2xvcj0iI2ZlNSIgb2Zmc2V0PSIwLjYiLz4KICAgICAgPHN0b3Agc3RvcC1jb2xvcj0iI2RhMSIgb2Zmc2V0PSIxIi8+CiAgICA8L2xpbmVhckdyYWRpZW50PgogICAgPGxpbmVhckdyYWRpZW50IGlkPSJweUJsdWUiIGdyYWRpZW50VHJhbnNmb3JtPSJyb3RhdGUoNDUpIj4KICAgICAgPHN0b3Agc3RvcC1jb2xvcj0iIzY5ZiIgb2Zmc2V0PSIwLjQiLz4KICAgICAgPHN0b3Agc3RvcC1jb2xvcj0iIzQ2OCIgb2Zmc2V0PSIxIi8+CiAgICA8L2xpbmVhckdyYWRpZW50PgogIDwvZGVmcz4KCiAgPHBhdGggZD0iTTI3LDE2YzAtNyw5LTEzLDI0LTEzYzE1LDAsMjMsNiwyMywxM2wwLDIyYzAsNy01LDEyLTExLDEybC0yNCwwYy04LDAtMTQsNi0xNCwxNWwwLDEwbC05LDBjLTgsMC0xMy05LTEzLTI0YzAtMTQsNS0yMywxMy0yM2wzNSwwbDAtM2wtMjQsMGwwLTlsMCwweiBNODgsNTB2MSIgZmlsbD0idXJsKCNweUJsdWUpIi8+CiAgPHBhdGggZD0iTTc0LDg3YzAsNy04LDEzLTIzLDEzYy0xNSwwLTI0LTYtMjQtMTNsMC0yMmMwLTcsNi0xMiwxMi0xMmwyNCwwYzgsMCwxNC03LDE0LTE1bDAtMTBsOSwwYzcsMCwxMyw5LDEzLDIzYzAsMTUtNiwyNC0xMywyNGwtMzUsMGwwLDNsMjMsMGwwLDlsMCwweiBNMTQwLDUwdjEiIGZpbGw9InVybCgjcHlZZWxsb3cpIi8+CgogIDxjaXJjbGUgcj0iNCIgY3g9IjY0IiBjeT0iODgiIGZpbGw9IiNGRkYiLz4KICA8Y2lyY2xlIHI9IjQiIGN4PSIzNyIgY3k9IjE1IiBmaWxsPSIjRkZGIi8+Cjwvc3ZnPgo=)

## usage

install / update package

```bash
pip install pandas-plots -U
```

include in python

```python
from pandas_plots import tbl, viz
```

## example

```python
# load sample dataset from seaborn
import seaborn as sb
df = sb.load_dataset('taxis')

viz.plot_box(df['fare'], height=400, violin=True)
```

![plot_box](https://github.com/smeisegeier/pandas-plots/blob/main/img/2024-02-13-00-40-27.png?raw=true)

## why use pandas-plots

`pandas-plots` is a package to help you examine and visualize data that are organized in a pandas DataFrame. It provides a high level api to pandas / plotly with some selected functions.

It is subdivided into:

- `tbl` utilities for table descriptions
  - `describe_df()` an alternative version of pandas `describe()` function
  - `pivot_df()` gets a pivot table of a 3 column dataframe

- `viz` utilities for plotly visualizations
  - `plot_box()` auto annotated boxplot w/ violin option
  - `plot_boxes()` multiple boxplots _(annotation is experimental)_
  - `plots_bars()` a standardized bar plot
  - `plot_stacked_bars()` shortcut to stacked bars 😄
  - `plot_quadrants()` quickly show a 2x2 heatmap

- `sql` is added as convienient wrapper for fetching data from sql databases
  - `connect_sql` get data from `['mssql', 'sqlite','postgres']` 

## dependencies
