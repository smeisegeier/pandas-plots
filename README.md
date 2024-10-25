# pandas-plots

![PyPI - Version](https://img.shields.io/pypi/v/pandas-plots) ![GitHub last commit](https://img.shields.io/github/last-commit/smeisegeier/pandas-plots?logo=github) ![GitHub License](https://img.shields.io/github/license/smeisegeier/pandas-plots?logo=github) ![py3.10](https://img.shields.io/badge/python-3.10_|_3.11_|_3.12-blue.svg?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTAwIj4KICA8ZGVmcz4KICAgIDxsaW5lYXJHcmFkaWVudCBpZD0icHlZZWxsb3ciIGdyYWRpZW50VHJhbnNmb3JtPSJyb3RhdGUoNDUpIj4KICAgICAgPHN0b3Agc3RvcC1jb2xvcj0iI2ZlNSIgb2Zmc2V0PSIwLjYiLz4KICAgICAgPHN0b3Agc3RvcC1jb2xvcj0iI2RhMSIgb2Zmc2V0PSIxIi8+CiAgICA8L2xpbmVhckdyYWRpZW50PgogICAgPGxpbmVhckdyYWRpZW50IGlkPSJweUJsdWUiIGdyYWRpZW50VHJhbnNmb3JtPSJyb3RhdGUoNDUpIj4KICAgICAgPHN0b3Agc3RvcC1jb2xvcj0iIzY5ZiIgb2Zmc2V0PSIwLjQiLz4KICAgICAgPHN0b3Agc3RvcC1jb2xvcj0iIzQ2OCIgb2Zmc2V0PSIxIi8+CiAgICA8L2xpbmVhckdyYWRpZW50PgogIDwvZGVmcz4KCiAgPHBhdGggZD0iTTI3LDE2YzAtNyw5LTEzLDI0LTEzYzE1LDAsMjMsNiwyMywxM2wwLDIyYzAsNy01LDEyLTExLDEybC0yNCwwYy04LDAtMTQsNi0xNCwxNWwwLDEwbC05LDBjLTgsMC0xMy05LTEzLTI0YzAtMTQsNS0yMywxMy0yM2wzNSwwbDAtM2wtMjQsMGwwLTlsMCwweiBNODgsNTB2MSIgZmlsbD0idXJsKCNweUJsdWUpIi8+CiAgPHBhdGggZD0iTTc0LDg3YzAsNy04LDEzLTIzLDEzYy0xNSwwLTI0LTYtMjQtMTNsMC0yMmMwLTcsNi0xMiwxMi0xMmwyNCwwYzgsMCwxNC03LDE0LTE1bDAtMTBsOSwwYzcsMCwxMyw5LDEzLDIzYzAsMTUtNiwyNC0xMywyNGwtMzUsMGwwLDNsMjMsMGwwLDlsMCwweiBNMTQwLDUwdjEiIGZpbGw9InVybCgjcHlZZWxsb3cpIi8+CgogIDxjaXJjbGUgcj0iNCIgY3g9IjY0IiBjeT0iODgiIGZpbGw9IiNGRkYiLz4KICA8Y2lyY2xlIHI9IjQiIGN4PSIzNyIgY3k9IjE1IiBmaWxsPSIjRkZGIi8+Cjwvc3ZnPgo=)

## usage

install / update package

```bash
pip install pandas-plots -U
```

include in python

```python
from pandas_plots import tbl, pls, ven, hlp, pii
```

## example

```python
# load sample dataset from seaborn
import seaborn as sb
df = sb.load_dataset('taxis')
```

```python
_df = df[["passengers", "distance", "fare"]][:5]
tbl.show_num_df(
    _df,
    total_axis="xy",
    total_mode="mean",
    data_bar_axis="xy",
    pct_axis="xy",
    precision=0,
    kpi_mode="max_min_x",
    kpi_rag_list=(1,7),
)
```

![show_num](https://github.com/smeisegeier/pandas-plots/blob/main/img/2024-03-02-17-33-43.png?raw=true)

## why use pandas-plots

`pandas-plots` is a package to help you examine and visualize data that are organized in a pandas DataFrame. It provides a high level api to pandas / plotly with some selected functions and predefined options:

- `tbl` utilities for table descriptions
  - 🌟`show_num_df()` displays a table as styled version with additional information
  - `describe_df()` an alternative version of pandas `describe()` function
  - `descr_db()` a very short descr for a `duckdb` relation
  - `pivot_df()` gets a pivot table of a 3 column dataframe (or 2 columns if no weights are given)
  - `print_summary()` shows statistics for a pandas DataFrame or Series

- `pls` for plotly visualizations
  - `plot_box()` auto annotated boxplot w/ violin option
  - `plot_boxes()` multiple boxplots _(annotation is experimental)_
  - `plot_stacked_bars()` shortcut to stacked bars 😄
  - `plots_bars()` a standardized bar plot for a **categorical** column
    - features confidence intervals via `use_ci` option
  - `plot_histogram()` histogram for one or more **numerical** columns
  - `plot_joints()` a joint plot for **exactly two numerical** columns
  - `plot_quadrants()` quickly shows a 2x2 heatmap

- `ven` offers functions for _venn diagrams_
  - `show_venn2()` displays a venn diagram for 2 sets
  - `show_venn3()` displays a venn diagram for 3 sets

- `hlp` contains some (variety) helper functions
  - `df_to_series()` converts a dataframe to a series
  - `mean_confidence_interval()` calculates mean and confidence interval for a series
  - `wrap_text()` formats strings or lists to a given width to fit nicely on the screen
  - `replace_delimiter_outside_quotes()` when manual import of csv files is needed: replaces delimiters only outside of quotes
  - `create_barcode_from_url()` creates a barcode from a given URL
  - `add_datetime_col()` adds a datetime columns to a dataframe
  - `show_package_version` prints version of a list of packages
  - `get_os` helps to identify and ensure operating system at runtime

- `pii` has routines for handling of personally identifiable information
  - `remove_pii()` logs and deletes pii from a series

> note: theme setting can be controlled through all functions by setting the environment variable `THEME` to either light or dark

## more examples

```python
pls.plot_box(df['fare'], height=400, violin=True)
```

![plot_box](https://github.com/smeisegeier/pandas-plots/blob/main/img/2024-02-13-00-40-27.png?raw=true)

```python
# quick and exhaustive description of any table
tbl.describe_df(df, 'taxis', top_n_uniques=5)
```

![describe_df](https://github.com/smeisegeier/pandas-plots/blob/main/img/2024-02-14-20-49-00.png?raw=true)

```python
# show bars with confidence intervals
_df = df[["payment", "fare"]]
pls.plot_bars(
    _df,
    dropna=False,
    use_ci=True,
    height=600,
    width=800,
    precision=1,
)
```

![bars_with_ci](https://github.com/smeisegeier/pandas-plots/blob/main/img/2024-03-24-09-59-32.png?raw=true)

```python
# show venn diagram for 3 sets
from pandas_plots import ven

set_a = {'ford','ferrari','mercedes', 'bmw'}
set_b = {'opel','bmw','bentley','audi'}
set_c = {'ferrari','bmw','chrysler','renault','peugeot','fiat'}
_df, _details = ven.show_venn3(
    title="taxis",
    a_set=set_a,
    a_label="cars1",
    b_set=set_b,
    b_label="cars2",
    c_set=set_c,
    c_label="cars3",
    verbose=0,
    size=8,
)
```

![venn](https://github.com/smeisegeier/pandas-plots/blob/main/img/2024-02-19-20-49-52.png?raw=true)

## tags

#pandas, #plotly, #visualizations, #statistics