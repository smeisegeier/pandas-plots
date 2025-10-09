import os
from pathlib import Path
from typing import Literal

import pandas as pd
import plotly.express as px

from ..hlp import *
from ..helper import set_caption

def plot_bars(
    df_in: pd.Series | pd.DataFrame,
    caption: str = None,
    top_n_index: int = 0,
    top_n_minvalue: int = 0,
    dropna: bool = False,
    orientation: Literal["h", "v"] = "v",
    sort_values: bool = False,
    normalize: bool = True,
    height: int = 500,
    width: int = 1600,
    title: str = None,
    use_ci: bool = False,
    ci_agg: Literal["mean", "median"] = "mean",
    precision: int = 0,
    renderer: Literal["png", "svg", None] = None,
    png_path: Path | str = None,
) -> None:
    """
    A function to plot a bar chart based on a *categorical* column (must be string or bool) and a numerical value.
    Accepts:
        - a dataframe w/ exactly 2 columns: string and numerical OR
        - a series, then value_counts() is applied upon to form the numercal, and use_ci is set to false

    Parameters:
    - df_in: df or series.
    - caption: An optional string indicating the caption for the chart.
    - top_n_index: An optional integer indicating the number of top indexes to include in the chart. Default is 0, which includes all indexes.
    - top_n_minvalue: An optional integer indicating the minimum value to be included in the chart. Default is 0, which includes all values.
    - dropna: A boolean indicating whether to drop NaN values from the chart. Default is False.
    - orientation: A string indicating the orientation of the chart. It can be either "h" for horizontal or "v" for vertical. Default is "v".
    - sort_values: A boolean indicating whether to sort the values in the chart. Default is False.
    - normalize: A boolean indicating whether to show pct values in the chart. Default is False.
    - height: An optional integer indicating the height of the chart. Default is 500.
    - width: An optional integer indicating the width of the chart. Default is 2000.
    - title: An optional string indicating the title of the chart. If not provided, the title will be the name of the index column.
    - use_ci: A boolean indicating whether to use confidence intervals (95%) on mean values for the chart. Default is False.
        - if True, the function will add the lower and upper bounds of the confidence interval to the chart.
        - enforces vertical orientation.
        - enforces nomalize=False
        - enforces dropna=True
    - precision: An integer indicating the number of decimal places to round the values to. Default is 0.
    - renderer: A string indicating the renderer to use for displaying the chart. It can be "png", "svg", or None. Default is None.
    - png_path (Path | str, optional): The path to save the image as a png file. Defaults to None.

    Returns: None
    """
    # * if series, apply value_counts, deselect use_ci
    if isinstance(df_in, pd.Series):
        if df_in.dtype.kind not in ["O", "b"]:
            print("❌ for numeric series use plot_histogram().")
            return
        else:
            df_in = df_in.value_counts(dropna=dropna).to_frame().reset_index()
            use_ci = False

    # * if df, check if valid
    if isinstance(df_in, pd.DataFrame):
        if len(df_in.columns) == 1:
            if not (df_in.iloc[:, 0].dtype.kind in ["O", "b"]):
                print("❌ df must have 1 column of object or bool type.")
                return
            else:
                df_in = df_in.value_counts(dropna=dropna).to_frame().reset_index()
                use_ci = False
        elif len(df_in.columns) == 2:
            if not (df_in.iloc[:, 0].dtype.kind in ["O", "b"]) or not (df_in.iloc[:, 1].dtype.kind in ["i", "f"]):
                print("❌ df must have string and numeric columns (in that order).")
                return
        else:
            print("❌ df must have exactly 1 or 2 columns")
            return
    else:
        print("❌ input must be series or dataframe.")
        return

    col_index = df_in.columns[0]
    col_name = df_in.columns[1]

    # * ensure df is grouped to prevent false aggregations, reset index to return df
    if use_ci:
        # * grouping is smoother on df than on series
        df = (
            df_in
            # ? dont dropna() here, this biases the input data
            .groupby(
                col_index,
                dropna=False,
            )
            .agg(
                mean=(col_name, ci_agg),
                # * retrieve margin from custom func
                margin=(
                    col_name,
                    lambda x: mean_confidence_interval(x, use_median=(ci_agg == "median"))[1],
                ),
            )
            .reset_index()
        )
        # * enforce vertical bars **when using ci**, normalize=False, dropna=True, set empty margin to 0 to avoid dropping the bar
        orientation = "v"
        normalize = False
        dropna = True
        df['margin'] = df['margin'].fillna(0)
    else:
        df = df_in.groupby(col_index, dropna=dropna)[col_name].sum().reset_index()

    # return df

    # * nulls are hidden by default in plotly etc, so give them a proper category
    if dropna:
        df = df.dropna()
    else:
        df = df.fillna("<NA>")

    # * get n, col1 now is always numeric
    n = df[df.columns[1]].sum()
    n_len = len(df_in)

    # * after grouping add cols for pct and formatting
    df["pct"] = df[df.columns[1]] / n

    # * format output
    df["cnt_str"] = df[df.columns[1]].apply(lambda x: f"{x:_.{precision}f}")

    divider = "<br>" if orientation == "v" else " "
    df["cnt_pct_str"] = df.apply(lambda row: f"{row['cnt_str']}{divider}({row['pct']:.1%})", axis=1)
    # * format output for ci
    df["ci_str"] = (
        None
        if not use_ci
        else df.apply(
            lambda row: f"{row['cnt_str']}{divider}[{row['mean'] - row['margin']:_.{precision}f};{row['mean'] + row['margin']:_.{precision}f}]",
            axis=1,
        )
    )

    # * set col vars according to config
    col_value = "pct" if not use_ci else df.columns[1]
    col_value_str = "ci_str" if use_ci else "cnt_pct_str" if normalize else "cnt_str"
    # return df

    # * if top n selected
    if top_n_index > 0:
        # * get top n -> series
        # * on pivot tables (all cells are values) you can also use sum for each column[df.sum(axis=1) > n]
        ser_top_n = df.groupby(col_index, dropna=False)[col_value].sum().sort_values(ascending=False)[:top_n_index]
        # * only process top n indexes. this does not change pct values
        df = df[df[col_index].isin(ser_top_n.index)]

    # * if top n min value: filter out below threshold
    if top_n_minvalue > 0:
        df = df[df.iloc[:, 1] >= top_n_minvalue]

    # * get longest bar
    bar_length_multiplier = 1.1 if normalize else 1.05
    bar_max = (
        df.groupby(col_index, dropna=False)[col_value].sum().sort_values(ascending=False).iloc[0]
        * bar_length_multiplier
    )

    # * are TOP n selected? include in default title
    _title_str_top = f"TOP {top_n_index} " if top_n_index > 0 else ""

    # * are TOP n selected? include in default title
    _title_str_minval = f"ALL >{top_n_minvalue}, " if top_n_minvalue > 0 else ""

    # * title str n
    _title_str_n = f", n={n_len:_} ({n:_})" if not use_ci else f", n={n_len:_})<br><sub>ci(95) on {ci_agg}s<sub>"

    # * title str na
    _title_str_null = f", NULL excluded" if dropna else ""

    # * layot caption if provided
    caption = set_caption(caption)
    # ! plot
    _fig = px.bar(
        df.sort_values(
            col_value if sort_values else col_index,
            ascending=False if sort_values else True,
        ),
        x=col_index if orientation == "v" else col_value,
        y=col_value if orientation == "v" else col_index,
        text=col_value_str,
        orientation=orientation,
        # * retrieve the original columns from series
        title=title
        or f"{caption}{_title_str_minval}{_title_str_top}[{col_name}] by [{col_index}]{_title_str_null}{_title_str_n}",
        # * retrieve theme from env (intro.set_theme) or default
        template="plotly_dark" if os.getenv("THEME") == "dark" else "plotly",
        error_y=None if not use_ci else df["margin"],
        color_discrete_sequence=px.colors.qualitative.D3,
        color=col_index,
    )

    # * ci errorbars should be auto-handled
    if not use_ci:
        # * leave room for labelpositions outside
        if orientation == "v":
            _fig.update_yaxes(range=[0, bar_max * 1.05])  # let extra space if vertical
        else:
            _fig.update_xaxes(range=[0, bar_max])

    # * show grids
    _fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        dtick=0.05 if orientation == "h" else None,
    )
    _fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        dtick=None if use_ci else 0.05 if orientation == "v" else None,
    )

    # * set title properties
    _fig.update_layout(
        title={
            # 'x': 0.1,
            "y": 0.95,
            "xanchor": "left",
            "yanchor": "top",
            "font": {
                "size": 24,
            },
        },
        showlegend=False,
        # uniformtext_minsize=14, uniformtext_mode='hide'
    )
    # * sorting
    if orientation == "v":
        if sort_values:
            _fig.update_layout(xaxis={"categoryorder": "total descending"})
        else:
            _fig.update_layout(xaxis={"categoryorder": "category ascending"})
    else:
        if sort_values:
            _fig.update_layout(yaxis={"categoryorder": "total ascending"})
        else:
            _fig.update_layout(yaxis={"categoryorder": "category descending"})

    # * looks better on single bars
    _fig.update_traces(error_y=dict(thickness=5))
    if use_ci:
        _fig.update_traces(
            textposition="inside",  # Put labels inside bars
            insidetextanchor="start",  # Align labels at the bottom
            textfont=dict(size=14, color="white"),  # Adjust text color for visibility
        )
    else:
        _fig.update_traces(
            textposition="outside",
            # error_y=dict(thickness=0)
        )

    _fig.update_layout(
        width=width,
        height=height,
    )

    # hack for #79
    if ci_agg == "median":
        _fig.update_layout(
            yaxis_title="median",
        )

    # * set axis title
    _fig.show(
        renderer=renderer or os.getenv("RENDERER"),
        width=width,
        height=height,
    )

    # * save to png if path is provided
    if png_path is not None:
        _fig.write_image(Path(png_path).as_posix())

    return
