from pathlib import Path
import warnings

warnings.filterwarnings("ignore")

import os
from typing import Optional, Literal

import pandas as pd
import seaborn as sb
from matplotlib import pyplot as plt
from plotly import express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .hlp import *
from .tbl import print_summary


def _set_caption(caption: str) -> str:
    return f"#️⃣{'-'.join(caption.split())}, " if caption else ""


def plot_quadrants(
    df: pd.DataFrame,
    title: str = None,
    caption: str = None,
    png_path: Path | str = None,
) -> object:
    """
    Plot a heatmap for the given dataframe, with options for title and caption.

    Args:
        df (pd.DataFrame): The input dataframe with 2 or 3 columns.
            df must have 3 columns, first 2 must be present
                index axis
                columns axis
                values (can be derived as cnt=1)
            df columns must contain 2 values
        title (str, optional): The title for the heatmap to override the default.
        caption (str, optional): The caption for the heatmap. Defaults to None.
        png_path (Path | str, optional): The path to save the image as a png file. Defaults to None.

    Returns:
        q1, q2, q3, q4, n: The values for each quadrant and the total count.
    """
    if len(df.columns) < 2 or len(df.columns) > 3:
        print("❌ df must have 2 or 3 columns")
        return

    if len(df.iloc[:, 0].unique()) != 2 or len(df.iloc[:, 0].unique()) != 2:
        print("❌ both columns must have 2 values")
        return

    if len(df.columns) == 2:
        df["cnt"] = 1

    heat = (
        df.groupby(
            by=[df.columns[0], df.columns[1]],
            as_index=True,  # * use index to keep track of all columns
        )[df.columns[2]]
        .sum()
        .reset_index()  # * then reset index to get a dataframe with all columns
    )
    # * create pivot table in wide format for heatmap
    heat_wide = heat.pivot(
        index=df.columns[0],
        columns=df.columns[1],
        values=df.columns[2],
    )

    # * derive label for heatmap
    n = heat_wide.sum().sum()
    heat_label = heat_wide.map(lambda x: f"{x:_}\n({x/n*100:.1f}%)")

    # * seaborn. use less fancy stuff :)
    caption = f"#{caption.lower()}, " if caption else "heatmap, "

    # * plot
    theme = "dark_background" if os.getenv("THEME") == "dark" else "ggplot"

    plt.style.use(theme)
    _ = sb.heatmap(
        # data=_heat_wide,
        data=heat_wide.map(lambda x: x / n),
        annot=heat_label,
        fmt="",
        cmap="BuPu",
        vmin=0,  # * to have relative values in colorbar
        vmax=1,
    ).set_title(f"{caption}n = {n:_.0f}" if not title else title)

    # * dont output na values
    heat_wide_out = heat_wide.fillna(0)
    q1 = heat_wide_out.iloc[1, 1]
    q2 = heat_wide_out.iloc[1, 0]
    q3 = heat_wide_out.iloc[0, 0]
    q4 = heat_wide_out.iloc[0, 1]

    # * save to png if path is provided
    if png_path is not None:
        plt.savefig(Path(png_path).as_posix(), format='png')

    return q1, q2, q3, q4, n
    # * plotly express is not used for the heatmap, although it does not need the derived wide format.
    # * but theres no option to alter inner values in the heatmap


def plot_stacked_bars(
    df: pd.DataFrame,
    top_n_index: int = 0,
    top_n_color: int = 0,
    dropna: bool = False,
    swap: bool = False,
    normalize: bool = False,
    relative: bool = False,
    orientation: Literal["h", "v"] = "v",
    height: int = 500,
    width: int = 2000,
    title: str = None,
    renderer: Literal["png", "svg", None] = "png",
    caption: str = None,
    sort_values: bool = False,
    show_total: bool = False,
    precision: int = 0,
    png_path: Path | str = None,
) -> object:
    """
    Generates a stacked bar plot using the provided DataFrame.
    df *must* comprise the columns (order matters):
    - index axis
    - color axis (legend)
    - values (optional, if absent a simple count is applied)

    Parameters:
    - df: pd.DataFrame - The DataFrame containing the data to plot.
    - top_n_index: int = 0 - The number of top indexes to include in the plot.
    - top_n_color: int = 0 - The number of top colors to include in the plot. WARNING: this forces distribution to 100% on a subset
    - dropna: bool = False - Whether to include NULL values in the plot.
    - swap: bool = False - Whether to swap the x-axis and y-axis.
    - normalize: bool = False - Whether to normalize the values.
    - relative: bool = False - Whether to show relative values as bars instead of absolute.
    - orientation: Literal["h", "v"] = "v" - The orientation of the plot.
    - height: int = 500 - The height of the plot.
    - width: An optional integer indicating the width of the chart. Default is 2000.
    - title: str = None - The title of the plot.
    - renderer: Literal["png", "svg",None] = "png" - The renderer for the plot.
    - caption: An optional string indicating the caption for the chart.
    - sort_values: bool = False - Sort axis by index (default) or values
    - show_total: bool = False - Whether to show the total value
    - precision: int = 0 - The number of decimal places to round to
    - png_path (Path | str, optional): The path to save the image as a png file. Defaults to None.

    Returns:
    plot object
    """
    BAR_LENGTH_MULTIPLIER = 1.05

    # * 2 axis means at least 2 columns
    if len(df.columns) < 2 or len(df.columns) > 3:
        print("❌ df must have exactly 2 or 3 columns")
        return

    # * check if first 2 columns are str
    if list(set((df.iloc[:, [0, 1]].dtypes)))[0].kind not in ["O", "b"]:
        print("❌ first 2 columns must be str")
        return

    # * add count column[2] as a service if none is present
    if len(df.columns) == 2:
        df["cnt"] = 1

    # * create seperate section for na values if selected
    if not dropna:
        df = df.fillna("<NA>")
    else:
        df.dropna(inplace=True)

    # * strip whitespaces if columns are str
    if df.iloc[:, 0].dtype.kind == "O":
        df.iloc[:, 0] = df.iloc[:, 0].str.strip()
    if df.iloc[:, 1].dtype.kind == "O":
        df.iloc[:, 1] = df.iloc[:, 1].str.strip()

    # * apply precision
    df.iloc[:, 2] = df.iloc[:, 2].round(precision)

    # * set index + color col
    col_index = df.columns[0] if not swap else df.columns[1]
    col_color = df.columns[1] if not swap else df.columns[0]

    # * add total as aggregation of df
    if show_total:
        df_total = df.copy()
        df_total[col_index] = " TOTAL"  # add space to make this item first
        df = pd.concat([df, df_total])

    # * ensure df is grouped to prevent false aggregations
    df = (
        df.groupby(
            [
                df.columns[0],
                df.columns[1],
            ]
        )[df.columns[2]]
        .sum()
        .reset_index()
    )

    # * calculate n
    divider = 2 if show_total else 1
    n = int(df[df.columns[2]].sum() / divider)

    # * after grouping add cols for pct and formatting
    df["cnt_pct"] = df[df.columns[2]] / n  # * col[3]
    df["cnt_str"] = df[df.columns[2]].apply(lambda x: f"{x:_}")  # * col[4]
    df["cnt_pct_str"] = df["cnt_pct"].apply(lambda x: f"{x:.2%}")  # * col[5]

    # * now set calculated col
    col_value = df.columns[2] if not normalize else df.columns[3]
    col_value_str = df.columns[4] if not normalize else df.columns[5]

    if top_n_index > 0:
        # * get top n -> series
        # * on pivot tables (all cells are values) you can also use sum for each column[df.sum(axis=1) > n]
        ser_top_n = (
            df.groupby(col_index)[col_value]
            .sum()
            .sort_values(ascending=False)[:top_n_index]
        )
        # * only process top n indexes. this does not change pct values
        df = df[df[col_index].isin(ser_top_n.index)]

    if top_n_color > 0:
        # * get top n -> series
        # * on pivot tables (all cells are values) you can also use sum for each column[df.sum(axis=1) > n]
        ser_top_n_col = (
            df.groupby(col_color)[col_value]
            .sum()
            .sort_values(ascending=False)[:top_n_color]
        )
        # * only process top n colors. this does not change pct values
        df = df[df[col_color].isin(ser_top_n_col.index)]

    # * get longest bar
    bar_max = (
        df.groupby(col_index)[col_value].sum().sort_values(ascending=False).iloc[0]
        * BAR_LENGTH_MULTIPLIER
    )

    # * are TOP n selected? include in default title
    _title_str_top_index = f"TOP{top_n_index} " if top_n_index > 0 else ""
    _title_str_top_color = f"TOP{top_n_color} " if top_n_color > 0 else ""

    # * title str na
    _title_str_null = f", NULL excluded" if dropna else ""

    # * title str n
    _title_str_n = f", n={n:_}"

    caption = _set_caption(caption)

    # * plot
    _fig = px.bar(
        df,
        x=col_index if orientation == "v" else col_value,
        y=col_value if orientation == "v" else col_index,
        color=col_color,
        text=col_value_str,
        # barmode="stack",
        orientation=orientation,
        title=title
        or f"{caption}{_title_str_top_index}[{col_index}] by {_title_str_top_color}[{col_color}]{_title_str_null}{_title_str_n}",
        # * retrieve theme from env (intro.set_theme) or default
        template="plotly_dark" if os.getenv("THEME") == "dark" else "plotly",
        width=width,
        height=height,
    )

    # * ignore if bar mode is on
    if not relative:
        if orientation == "v":
            _fig.update_yaxes(range=[0, bar_max])
        else:
            _fig.update_xaxes(range=[0, bar_max])
    else:
        _fig.update_layout(barnorm="percent")

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
    )

    # * show grids, set to smaller distance on pct scale
    _fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
    )
    _fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
    )

    # * set dtick
    if orientation == "h":
        if relative:
            _fig.update_xaxes(dtick=5)
        elif normalize:
            _fig.update_xaxes(dtick=0.05)
    else:
        if relative:
            _fig.update_yaxes(dtick=5)
        elif normalize:
            _fig.update_yaxes(dtick=0.05)

    # * sorting is in a weird spot, do a 1:1 matrix
    if orientation == "v" and sort_values:
        _fig.update_layout(xaxis={"categoryorder": "total descending"})
    elif orientation == "v" and not sort_values:
        _fig.update_layout(xaxis={"categoryorder": "category ascending"})
    elif orientation == "h" and sort_values:
        _fig.update_layout(yaxis={"categoryorder": "total ascending"})
    elif orientation == "h" and not sort_values:
        _fig.update_layout(yaxis={"categoryorder": "category descending"})

    _fig.show(renderer)

    # * save to png if path is provided
    if png_path is not None:
        _fig.write_image(Path(png_path).as_posix())

    return _fig


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
    precision: int = 0,
    renderer: Literal["png", "svg", None] = "png",
    png_path: Path | str = None,
) -> object:
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
    - renderer: A string indicating the renderer to use for displaying the chart. It can be "png", "svg", or None. Default is "png".
    - png_path (Path | str, optional): The path to save the image as a png file. Defaults to None.

    Returns:
    - plot object
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
        if len(df_in.columns) != 2:
            print("❌ df must have exactly 2 columns")
            return
        elif not (df_in.iloc[:, 0].dtype.kind in ["O", "b"]) or not (
            df_in.iloc[:, 1].dtype.kind in ["i", "f"]
        ):
            print("❌ df must have string and numeric columns (in that order).")
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
            df_in.groupby(
                col_index,
                dropna=False,
            )
            .agg(
                mean=(col_name, "mean"),
                # * retrieve margin from custom func
                margin=(col_name, lambda x: mean_confidence_interval(x)[1]),
            )
            .reset_index()
        )
        # * enforce vertical bars when using ci
        orientation = "v"
        normalize = False
        dropna = True
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
    df["cnt_str"] = df[df.columns[1]].apply(lambda x: f"{x:_.{precision}f}")
    divider = "<br>" if orientation == "v" else " "
    df["cnt_pct_str"] = df.apply(
        lambda row: f"{row['cnt_str']}{divider}({row['pct']:.1%})", axis=1
    )
    # * format output for ci
    df["ci_str"] = (
        None
        if not use_ci
        else df.apply(
            lambda row: f"{row['cnt_str']}{divider}[{row['mean']-row['margin']:_.{precision}f};{row['mean']+row['margin']:_.{precision}f}]",
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
        ser_top_n = (
            df.groupby(col_index, dropna=False)[col_value]
            .sum()
            .sort_values(ascending=False)[:top_n_index]
        )
        # * only process top n indexes. this does not change pct values
        df = df[df[col_index].isin(ser_top_n.index)]

    # * if top n min value: filter out below threshold
    if top_n_minvalue > 0:
        df = df[df.iloc[:, 1] >= top_n_minvalue]

    # * get longest bar
    bar_length_multiplier = 1.1 if normalize else 1.05
    bar_max = (
        df.groupby(col_index, dropna=False)[col_value]
        .sum()
        .sort_values(ascending=False)
        .iloc[0]
        * bar_length_multiplier
    )

    # * are TOP n selected? include in default title
    _title_str_top = f"TOP {top_n_index} " if top_n_index > 0 else ""

    # * are TOP n selected? include in default title
    _title_str_minval = f"ALL >{top_n_minvalue}, " if top_n_minvalue > 0 else ""

    # * title str n
    _title_str_n = (
        f", n={n:_}" if not use_ci else f", n={n_len:_}<br><sub>ci(95) on means<sub>"
    )

    # * title str na
    _title_str_null = f", NULL excluded" if dropna else ""

    # * layot caption if provided
    caption = _set_caption(caption)

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
        or f"{caption}{_title_str_minval}{_title_str_top}[{df.columns[1]}] by [{col_index}]{_title_str_null}{_title_str_n}",
        # * retrieve theme from env (intro.set_theme) or default
        template="plotly_dark" if os.getenv("THEME") == "dark" else "plotly",
        width=width,
        height=height,
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
    _fig.update_traces(
        textposition="outside" if not use_ci else "auto", error_y=dict(thickness=5)
    )
    _fig.show(renderer)

    # * save to png if path is provided
    if png_path is not None:
        _fig.write_image(Path(png_path).as_posix())

    return _fig


def plot_histogram(
    df_ser: pd.DataFrame | pd.Series,
    histnorm: Literal[
        "probability", "probability density", "density", "percent", None
    ] = None,
    nbins: int = 0,
    orientation: Literal["h", "v"] = "v",
    precision: int = 2,
    height: int = 500,
    width: int = 1600,
    text_auto: bool = True,
    barmode: Literal["group", "overlay", "relative"] = "relative",
    renderer: Literal["png", "svg", None] = "png",
    caption: str = None,
    title: str = None,
    png_path: Path | str = None,
) -> object:
    """
    A function to plot a histogram based on *numeric* columns in a DataFrame.
    Accepts:
        - a numeric series
        - a dataframe with only numeric columns

    Parameters:
        df_ser (pd.DataFrame | pd.Series): The input containing the data to be plotted.
        histnorm (Literal["probability", "probability density", "density", "percent", None]): The normalization mode for the histogram. Default is None.
        nbins (int): The number of bins in the histogram. Default is 0.
        orientation (Literal["h", "v"]): The orientation of the histogram. Default is "v".
        precision (int): The precision for rounding the data. Default is 2.
        height (int): The height of the plot. Default is 500.
        width (int): The width of the plot. Default is 1600.
        text_auto (bool): Whether to automatically display text on the plot. Default is True.
        barmode (Literal["group", "overlay", "relative"]): The mode for the bars in the histogram. Default is "relative".
        renderer (Literal["png", "svg", None]): The renderer for displaying the plot. Default is "png".
        caption (str): The caption for the plot. Default is None.
        title (str): The title of the plot. Default is None.
        png_path (Path | str, optional): The path to save the image as a png file. Defaults to None.
        

    Returns:
        plot object
    """

    # * convert to df if series
    if isinstance(df_ser, pd.Series):
        df = df_ser.to_frame()
    else:
        df = df_ser

    col_not_num = df.select_dtypes(exclude="number").columns
    if any(col_not_num):
        print(
            f"❌ all columns must be numeric, but the following are not: [{', '.join(col_not_num)}]. consider using plot_bars()."
        )
        return

    # * rounding
    df = df.applymap(lambda x: round(x, precision))

    # ! plot
    _caption = _set_caption(caption)
    fig = px.histogram(
        data_frame=df,
        histnorm=histnorm,
        nbins=nbins,
        marginal="box",
        barmode=barmode,
        text_auto=text_auto,
        height=height,
        width=width,
        orientation=orientation,
        title=title or f"{_caption}[{', '.join(df.columns)}], n={df.shape[0]:_}",
        template="plotly_dark" if os.getenv("THEME") == "dark" else "plotly",
    )
    # * set title properties
    fig.update_layout(
        title={
            # 'x': 0.1,
            "y": 0.95,
            "xanchor": "left",
            "yanchor": "top",
            "font": {
                "size": 24,
            },
        },
        showlegend=False if df.shape[1] == 1 else True,
    )

    fig.show(renderer)
    
    # * save to png if path is provided
    if png_path is not None:
        fig.write_image(Path(png_path).as_posix())

    return fig


def plot_joint(
    df: pd.DataFrame,
    kind: Literal["reg", "hist", "hex", "kde"] = "hex",
    precision: int = 2,
    size: int = 5,
    dropna: bool = False,
    caption: str = "",
    title: str = "",
    png_path: Path | str = None,
) -> object:
    """
    Generate a seaborn joint plot for *two numeric* columns of a given DataFrame.

    Parameters:
        - df: The DataFrame containing the data to be plotted.
        - kind: The type of plot to generate (default is "hex").
        - precision: The number of decimal places to round the data to (default is 2).
        - size: The size of the plot (default is 5).
        - dropna: Whether to drop NA values before plotting (default is False).
        - caption: A caption for the plot.
        - title: The title of the plot.
        - png_path (Path | str, optional): The path to save the image as a png file. Defaults to None.

    Returns:
        plot object
    """

    if df.shape[1] != 2:
        print("❌ df must have 2 columns")
        return

    col_not_num = df.select_dtypes(exclude="number").columns
    if any(col_not_num):
        print(
            f"❌ both columns must be numeric, but the following are not: [{', '.join(col_not_num)}]. consider using plot_bars()."
        )
        return

    df = df.applymap(lambda x: round(x, precision))

    # ! plot
    # * set theme and palette
    sb.set_theme(style="darkgrid", palette="tab10")
    if os.getenv("THEME") == "dark":
        _style = "dark_background"
        _cmap = "rocket"
    else:
        _style = "bmh"
        _cmap = "bone_r"
    plt.style.use(_style)

    dict_base = {
        "x": df.columns[0],
        "y": df.columns[1],
        "data": df,
        "height": size,
        "kind": kind,
        "ratio": 10,
        "marginal_ticks": False,
        "dropna": dropna,
        # "title": f"{caption}[{ser.name}], n = {len(ser):_}" if not title else title,
    }
    dict_hex = {"cmap": _cmap}
    dict_kde = {"fill": True, "cmap": _cmap}

    if kind == "hex":
        fig = sb.jointplot(**dict_base, **dict_hex)
    elif kind == "kde":
        fig = sb.jointplot(**dict_base, **dict_kde)
    else:
        fig = sb.jointplot(**dict_base)

    # * emojis dont work in good ol seaborn
    _caption = "" if not caption else f"#{caption}, "
    fig.figure.suptitle(
        title or f"{_caption}[{df.columns[0]}] vs [{df.columns[1]}], n = {len(df):_}"
    )
    # * leave some room for the title
    fig.figure.tight_layout()
    fig.figure.subplots_adjust(top=0.90)

    # sb.jointplot(
    #     x=df.columns[0],
    #     y=df.columns[1],
    #     data=df,
    #     height=size,
    #     kind=kind,
    #     ratio=10,
    #     marginal_ticks=False,
    #     dropna=dropna,
    #     cmap=_cmap,
    # )
    # * save to png if path is provided
    if png_path is not None:
        fig.savefig(Path(png_path).as_posix())

    return fig


def plot_box(
    ser: pd.Series,
    points: Literal["all", "outliers", "suspectedoutlieres", None] = None,
    precision: int = 2,
    height: int = 200,
    width: int = 1200,
    annotations: bool = True,
    summary: bool = True,
    caption: str = None,
    title: str = None,
    violin: bool = False,
    x_min: float = None,
    x_max: float = None,
    png_path: Path | str = None,
) -> object:
    """
    Plots a horizontal box plot for the given pandas Series.

    Args:
        ser: The pandas Series to plot.
        points: The type of points to plot on the box plot ('all', 'outliers', 'suspectedoutliers', None).
        precision: The precision of the annotations.
        height: The height of the plot.
        width: The width of the plot.
        annotations: Whether to add annotations to the plot.
        violin: Use violin plot or not
        x_min: The minimum value for the x-axis scale (max and min must be set)
        x_max: The maximum value for the x-axis scale (max and min must be set)
        summary: Whether to add a summary table to the plot
        png_path (Path | str, optional): The path to save the image as a png file. Defaults to None.

    Returns:
        plot object
    """
    ser = to_series(ser)
    if ser is None:
        return

    # * drop na to keep scipy sane
    n_ = len(ser)
    ser.dropna(inplace=True)
    n = len(ser)

    # hack
    median = ser.median()
    mean = ser.mean()
    q25 = ser.quantile(0.25)
    q75 = ser.quantile(0.75)
    min = ser.min()
    max = ser.max()
    fence0_ = q25 - 1.5 * (q75 - q25)
    fence0 = fence0_ if fence0_ > min else min
    fence1_ = q75 + 1.5 * (q75 - q25)
    fence1 = fence1_ if fence1_ < max else max
    lvl1 = height * 0.05
    lvl2 = height * 0.15
    lvl3 = height * 0.25

    caption = _set_caption(caption)

    dict = {
        "data_frame": ser,
        "orientation": "h",
        "template": "plotly_dark" if os.getenv("THEME") == "dark" else "plotly",
        "height": height,
        "width": width,
        "points": points,
        # 'box':True,
        "title": f"{caption}[{ser.name}], n = {n_:_}({n:_})" if not title else title,
    }

    fig = px.violin(**{**dict, "box": True}) if violin else px.box(**dict)

    if (x_min or x_min == 0) and (x_max or x_max == 0):
        fig.update_xaxes(range=[x_min, x_max])

    # fig=px.violin(
    #     ser,
    #     template=os.getenv('THEME_PLOTLY'),
    #     orientation='h',
    #     height=height,
    #     width=width,
    #     points=points,
    #     box=True,
    #     title=f"{caption}[{ser.name}], n = {len(ser):_}" if not title else title,
    #     )
    if annotations:
        fig.add_annotation(
            x=min,
            text=f"min: {round(min,precision)}",
            showarrow=True,
            yshift=lvl1,
            y=-0,
        )
        fig.add_annotation(
            x=fence0,
            text=f"lower: {round(fence0,precision)}",
            showarrow=True,
            yshift=lvl3,
            y=-0,
        )
        fig.add_annotation(
            x=q25,
            text=f"q25: {round(q25,precision)}",
            showarrow=True,
            yshift=lvl2,
            y=-0,
        )
        fig.add_annotation(
            x=median,
            text=f"median: {round(median,precision)}",
            showarrow=True,
            yshift=lvl1,
            y=-0,
        )
        fig.add_annotation(
            x=mean,
            text=f"mean: {round(mean,precision)}",
            showarrow=True,
            yshift=lvl3,
            y=-0,
        )
        fig.add_annotation(
            x=q75,
            text=f"q75: {round(q75,precision)}",
            showarrow=True,
            yshift=lvl2,
            y=-0,
        )
        fig.add_annotation(
            x=fence1,
            text=f"upper: {round(fence1,precision)}",
            showarrow=True,
            yshift=lvl1,
            y=-0,
        )
        fig.add_annotation(
            x=max,
            text=f"max: {round(max,precision)}",
            showarrow=True,
            yshift=lvl3,
            y=-0,
        )

    fig.show("png")

    if summary:
        print_summary(ser)

    # * save to png if path is provided
    if png_path is not None:
        fig.write_image(Path(png_path).as_posix())

    return fig


def plot_boxes(
    df: pd.DataFrame,
    caption: str = None,
    points: Literal["all", "outliers", "suspectedoutliers", None] = None,
    precision: int = 2,
    height: int = 600,
    width: int = 800,
    annotations: bool = True,
    summary: bool = True,
    title: str = None,
    png_path: Path | str = None,
) -> object:
    """
    [Experimental] Plot vertical boxes for each unique item in the DataFrame and add annotations for statistics.

    Args:
        df (pd.DataFrame): The input DataFrame with two columns, where the first column is string or bool type and the second column is numeric.
        caption (str): The caption for the plot.
        points (Literal["all", "outliers", "suspectedoutliers", None]): The points to be plotted.
        precision (int): The precision for rounding the statistics.
        height (int): The height of the plot.
        width (int): The width of the plot.
        annotations (bool): Whether to add annotations to the plot.
        summary (bool): Whether to add a summary to the plot.
        png_path (Path | str, optional): The path to save the image as a png file. Defaults to None.

    Returns:
        plot object
    """

    if (
        len(df.columns) != 2
        or not (
            (pd.api.types.is_string_dtype(df.iloc[:, 0]))
            or (pd.api.types.is_bool_dtype(df.iloc[:, 0]))
        )
        or not pd.api.types.is_numeric_dtype(df.iloc[:, 1])
    ):
        print(f"❌ df must have 2 columns: [0] str or bool, [1] num")
        return
    # * layout gaps
    xlvl1 = -50
    xlvl2 = 0
    xlvl3 = 50

    # * not working
    # yspan_seg = (df.iloc[:, 1].max() - df.iloc[:, 1].max()) * .05
    # ylvl1 = -yspan_seg
    # ylvl2 = 0
    # ylvl3 = yspan_seg

    # * unique items
    items = df.iloc[:, 0].unique()

    caption = _set_caption(caption)

    # * main plot
    fig = px.box(
        df,
        x=df.iloc[:, 0],
        y=df.iloc[:, 1],
        template="plotly_dark" if os.getenv("THEME") == "dark" else "plotly",
        orientation="v",
        height=height,
        width=width,
        points=points,
        title=(
            f"{caption}[{df.columns[0]}] on [{df.columns[1]}], n = {len(df):_.0f}"
            if not title
            else title
        ),
    )

    # * yshift is trivial
    YS = 0

    # * loop annotations
    if annotations:
        for i, item in enumerate(items):
            max = round(df[df.iloc[:, 0] == item].iloc[:, 1].max(), precision)
            min = round(df[df.iloc[:, 0] == item].iloc[:, 1].min(), precision)
            mean = round(df[df.iloc[:, 0] == item].iloc[:, 1].mean(), precision)
            median = round(df[df.iloc[:, 0] == item].iloc[:, 1].median(), precision)
            q25 = round(df[df.iloc[:, 0] == item].iloc[:, 1].quantile(0.25), precision)
            q75 = round(df[df.iloc[:, 0] == item].iloc[:, 1].quantile(0.75), precision)
            fence0_ = round(q25 - 1.5 * (q75 - q25), precision)
            fence0 = fence0_ if fence0_ > min else min
            fence1_ = round(q75 + 1.5 * (q75 - q25), precision)
            fence1 = fence1_ if fence1_ < max else max
            fig.add_annotation(
                x=i, y=min, text=f"min: {min}", yshift=YS, showarrow=True, xshift=xlvl1
            )
            fig.add_annotation(
                x=i,
                y=fence0,
                text=f"lower: {fence0}",
                yshift=YS,
                showarrow=True,
                xshift=xlvl3,
            )
            fig.add_annotation(
                x=i, y=q25, text=f"q25: {q25}", yshift=YS, showarrow=True, xshift=xlvl2
            )
            fig.add_annotation(
                x=i,
                y=mean,
                text=f"mean: {mean}",
                yshift=YS,
                showarrow=True,
                xshift=xlvl1,
            )
            fig.add_annotation(
                x=i,
                y=median,
                text=f"median: {median}",
                yshift=YS,
                showarrow=True,
                xshift=xlvl3,
            )
            fig.add_annotation(
                x=i, y=q75, text=f"q75: {q75}", yshift=YS, showarrow=True, xshift=xlvl2
            )
            fig.add_annotation(
                x=i,
                y=fence1,
                text=f"upper: {fence1}",
                yshift=YS,
                showarrow=True,
                xshift=xlvl3,
            )
            fig.add_annotation(
                x=i, y=max, text=f"max: {max}", yshift=YS, showarrow=True, xshift=xlvl1
            )

    fig.update_xaxes(title_text=df.columns[0])
    fig.update_yaxes(title_text=df.columns[1])

    fig.show("png")
    if summary:
        print_summary(df)

    # * save to png if path is provided
    if png_path is not None:
        fig.write_image(Path(png_path).as_posix())

    return fig


def aggregate_data(df: pd.DataFrame, top_n_index: int, top_n_category: int, top_n_facet: int, null_label: str) -> pd.DataFrame:
    """
    Aggregates the data, ensuring each combination of 'index', 'col', and 'facet' is unique with summed 'value'.
    
    Args:
        df (pd.DataFrame): Input DataFrame.
        top_n_index (int): Top N values of the first column to keep. 0 means take all.
        top_n_category (int): Top N values of the second column to keep. 0 means take all.
        top_n_facet (int): Top N values of the third column to keep. 0 means take all.
        null_label (str): Label for null values.

    Returns:
        pd.DataFrame: Aggregated and filtered dataset.
    """
    # Replace nulls with a placeholder for consistent handling
    for col in ['index', 'col', 'facet']:  # Skip 'value' column (numeric)
        df[col] = df[col].fillna(null_label)

    # Aggregate data to ensure unique combinations
    aggregated_df = df.groupby(['index', 'col', 'facet'], as_index=False)['value'].sum()

    # Reduce data based on top_n parameters
    if top_n_index > 0:
        top_indexes = aggregated_df.groupby('index')['value'].sum().nlargest(top_n_index).index
        aggregated_df = aggregated_df[aggregated_df['index'].isin(top_indexes)]
    if top_n_category > 0:
        top_categories = aggregated_df.groupby('col')['value'].sum().nlargest(top_n_category).index
        aggregated_df = aggregated_df[aggregated_df['col'].isin(top_categories)]
    if top_n_facet > 0:
        top_facets = aggregated_df.groupby('facet')['value'].sum().nlargest(top_n_facet).index
        aggregated_df = aggregated_df[aggregated_df['facet'].isin(top_facets)]
    
    return aggregated_df


def assign_column_colors(columns: pd.Series, color_palette: str, null_label: str) -> dict:
    """
    Assign colors to columns using the selected color palette and handle null columns separately.
    
    Args:
        columns (pd.Series): The unique column categories.
        color_palette (str): The name of the color palette.
        null_label (str): The label to be used for null values.

    Returns:
        dict: Mapping of column values to colors.
    """
    if hasattr(px.colors.qualitative, color_palette):
        color_scale = px.colors.qualitative.__dict__.get(color_palette, px.colors.qualitative.Plotly)
    else:
        color_scale = px.colors.sequential.__dict__.get(color_palette, px.colors.sequential.Viridis)

    column_colors = {
        column: color_scale[i % len(color_scale)] 
        for i, column in enumerate(columns) if column != null_label
    }
    column_colors[null_label] = "gray"  # Assign gray to null columns
    
    return column_colors


def plot_facet_stacked_bars(
    df: pd.DataFrame,
    subplots_per_row: int = 4,
    top_n_index: int = 0,
    top_n_category: int = 0,
    top_n_facet: int = 0,
    null_label: str = "<NA>",
    subplot_size: int = 300,
    color_palette: str = "Plotly",
    caption: str = "",
    renderer: Optional[Literal["png", "svg"]] = "png",
    annotations: bool = False,
    precision: int = 0,
    png_path: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Create a grid of stacked bar charts.

    Args:
        df (pd.DataFrame): DataFrame with 3 or 4 columns.
        subplots_per_row (int): Number of subplots per row.
        top_n_index (int): Top N index values to keep.
        top_n_category (int): Top N category values to keep.
        top_n_facet (int): Top N facet values to keep.
        null_label (str): Label for null values.
        subplot_size (int): Size of each subplot.
        color_palette (str): Name of the color palette.
        caption (str): Optional caption to prepend to the title.
        renderer (Optional[Literal["png", "svg"]]): Renderer for saving the image.
        annotations (bool): Whether to show annotations in the subplots.
        precision (int): Decimal precision for annotations.
        png_path (Optional[Path]): Path to save the image.

    Returns:
        pd.DataFrame: Aggregated dataset used for plotting.
    """
    # Validate input DataFrame
    if not (df.shape[1] == 3 or df.shape[1] == 4):
        raise ValueError("Input DataFrame must have 3 or 4 columns.")
    
    # Store original column names
    original_column_names = df.columns.tolist()

    # Rename columns to more concise names
    if df.shape[1] == 3:
        df.columns = ['index', 'col', 'facet']
        df['value'] = 1  # Treat all rows as having a value of 1
    elif df.shape[1] == 4:
        df.columns = ['index', 'col', 'facet', 'value']

    # Aggregate and filter data
    aggregated_df = aggregate_data(df, top_n_index, top_n_category, top_n_facet, null_label)

    # Get unique facets and columns
    facets = aggregated_df['facet'].unique()
    columns = aggregated_df['col'].unique()

    # Assign colors to columns
    column_colors = assign_column_colors(columns, color_palette, null_label)

    # Create subplot grid
    fig = make_subplots(
        rows=-(-len(facets) // subplots_per_row),  # Ceiling division
        cols=min(subplots_per_row, len(facets)),
        subplot_titles=facets,
    )

    # Add traces for each facet
    added_to_legend = set()  # Track which columns have been added to the legend
    for i, facet in enumerate(facets):
        facet_data = aggregated_df[aggregated_df['facet'] == facet]
        row = (i // subplots_per_row) + 1
        col = (i % subplots_per_row) + 1

        for column in columns:
            column_data = facet_data[facet_data['col'] == column]
            show_legend = column not in added_to_legend
            if show_legend:
                added_to_legend.add(column)

            fig.add_trace(
                go.Bar(
                    x=column_data['index'],
                    y=column_data['value'],
                    name=column,
                    marker=dict(color=column_colors[column]),
                    showlegend=show_legend,
                ),
                row=row,
                col=col,
            )

            # Add annotations if annotations is True
            if annotations:
                for _, row_data in column_data.iterrows():
                    fig.add_annotation(
                        x=row_data['index'],
                        y=row_data['value'],
                        text=f"{row_data['value']:.{precision}f}",
                        showarrow=False,
                        row=row,
                        col=col,
                    )

    # Create the dynamic title
    unique_rows = len(aggregated_df)
    title = f"{caption} [{original_column_names[0]}] by [{original_column_names[1]}] by [{original_column_names[2]}], n = {unique_rows:_}"

    # Update layout for stacking, title, and theme
    template = "plotly_dark" if os.getenv("THEME") == "dark" else "plotly"
    fig.update_layout(
        title=title,
        barmode="stack",  # Enable stacking
        height=subplot_size * (-(-len(facets) // subplots_per_row)),
        width=subplot_size * min(subplots_per_row, len(facets)),
        showlegend=True,
        template=template,
    )

    # Save the figure if png_path is specified
    if png_path:
        png_path = Path(png_path)
        fig.write_image(str(png_path))

    # Show the figure with the renderer specified
    fig.show(renderer)

    # Return the aggregated dataset
    return aggregated_df

