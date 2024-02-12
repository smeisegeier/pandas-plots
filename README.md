# pandas-plots

## quickstart

```bash
pip install pandas-plots -U
```

```python
import pandas_plots as pp
pp.pandas.describe_df()
```

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

## dependencies
