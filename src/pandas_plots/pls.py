from pathlib import Path
import warnings

from pandas_plots import tbl

import os
from typing import Optional, Literal

import pandas as pd
import seaborn as sb
from matplotlib import pyplot as plt
from plotly import express as px
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
import plotly  # needed for return types

import re

from .hlp import *
from .tbl import print_summary

warnings.filterwarnings("ignore")

### helper functions

def _set_caption(caption: str) -> str:
    return f"#️⃣{' '.join(caption.split())}, " if caption else ""


def aggregate_data(
    df: pd.DataFrame,
    top_n_index: int,
    top_n_color: int,
    top_n_facet: int,
    null_label: str,
    show_other: bool = False,
    sort_values_index: bool = False,
    sort_values_color: bool = False,
    sort_values_facet: bool = False,
) -> pd.DataFrame:
    """
    Aggregates the data, ensuring each combination of 'index', 'col', and 'facet' is unique with summed 'value'.

    Args:
        df (pd.DataFrame): Input DataFrame.
        top_n_index (int): top N values of the first column to keep. 0 means take all.
        top_n_color (int): top N values of the second column to keep. 0 means take all.
        top_n_facet (int): top N values of the third column to keep. 0 means take all.
        null_label (str): Label for null values.
        show_other (bool): Whether to include "<other>" for columns not in top_n_color. Defaults to False.
        sort_values (bool): Whether to sort values in descending order based on group sum. Defaults to False.

    Returns:
        pd.DataFrame: Aggregated and filtered dataset (but not sorted!)
    """

    for col in ["index", "col", "facet"]:  # Skip 'value' column (numeric)
        df[col] = df[col].fillna(null_label)

    # Aggregate data to ensure unique combinations
    aggregated_df = df.groupby(["index", "col", "facet"], as_index=False)["value"].sum()

    # * Reduce data based on top_n parameters
    if sort_values_index:
        top_indexes = (
            aggregated_df.groupby("index")["value"]
            .sum()
            .sort_values(ascending=False)[: top_n_index or None]
            .index
        )

    else:
        top_indexes = (
            aggregated_df["index"].sort_values().unique()[: top_n_index or None]
        )

    aggregated_df = aggregated_df[aggregated_df["index"].isin(top_indexes)]

    if sort_values_color:
        top_colors = (
            aggregated_df.groupby("col")["value"]
            .sum()
            .sort_values(ascending=False)[: top_n_color or None]
            .index
        )
    else:
        top_colors = aggregated_df["col"].sort_values().unique()[: top_n_color or None]

    others_df = df[~df["col"].isin(top_colors)]
    aggregated_df = aggregated_df[aggregated_df["col"].isin(top_colors)]
    if show_other and top_n_color > 0 and not others_df.empty:
        other_agg = others_df.groupby(["index", "facet"], as_index=False)["value"].sum()
        other_agg["col"] = "<other>"
        other_agg = other_agg[["index", "col", "facet", "value"]]
        aggregated_df = pd.concat([aggregated_df, other_agg], ignore_index=True)
        top_colors = [*top_colors, "<other>"]

    if sort_values_facet:
        top_facets = (
            aggregated_df.groupby("facet")["value"]
            .sum()
            .sort_values(ascending=False)[: top_n_facet or None]
            .index
        )
    else:
        top_facets = (
            aggregated_df["facet"].sort_values().unique()[: top_n_facet or None]
        )

    aggregated_df = aggregated_df[aggregated_df["facet"].isin(top_facets)]

    return aggregated_df


def assign_column_colors(columns, color_palette, null_label):
    """
    Assigns colors to columns, with a special gray color for null values.

    Args:
        columns (list): List of column values.
        color_palette (str): Name of the color palette.
        null_label (str): Label for null values.

    Returns:
        dict: Mapping of column values to colors.
    """
    if hasattr(px.colors.qualitative, color_palette):
        palette = getattr(px.colors.qualitative, color_palette)
    else:
        raise ValueError(f"Invalid color palette: {color_palette}")

    colors = {col: palette[i % len(palette)] for i, col in enumerate(sorted(columns))}
    colors[null_label] = "lightgray"
    return colors


### main functions


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
        plt.savefig(Path(png_path).as_posix(), format="png")

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
    renderer: Literal["png", "svg", None] = None,
    caption: str = None,
    sort_values: bool = False,
    sort_values_index: bool = False,
    sort_values_color: bool = False,
    show_total: bool = False,
    precision: int = 0,
    png_path: Path | str = None,
    color_palette: str = "Plotly",
    null_label: str = "<NA>",
    show_other: bool = False,
    show_pct_all: bool = False,
    show_pct_bar: bool = False,
) -> None:
    """
    Generates a stacked bar plot using the provided DataFrame.

    Parameters:
    - df (pd.DataFrame): The input DataFrame with at least two categorical columns and one numerical column.
    - top_n_index (int): Limit the number of categories displayed on the index axis.
    - top_n_color (int): Limit the number of categories displayed in the color legend.
    - dropna (bool): If True, removes rows with missing values; otherwise, replaces them with `null_label`.
    - swap (bool): If True, swaps the first two columns.
    - normalize (bool): If True, normalizes numerical values between 0 and 1.
    - relative (bool): If True, normalizes the bars to a percentage scale.
    - orientation (Literal["h", "v"]): Defines the orientation of the bars ("v" for vertical, "h" for horizontal).
    - height (int): Height of the plot.
    - width (int): Width of the plot.
    - title (str): Custom title for the plot.
    - renderer (Literal["png", "svg", None]): Defines the output format.
    - caption (str): Optional caption for additional context.
    - sort_values (bool):
        - If True, sorts bars by the sum of their values (descending).
        - If False, sorts bars alphabetically.
    - show_total (bool): If True, adds a row with the total sum of all categories.
    - precision (int): Number of decimal places for numerical values.
    - png_path (Path | str): If specified, saves the plot as a PNG file.
    - color_palette (str): Name of the color palette to use.
    - null_label (str): Label for null values.
    - show_other (bool): If True, shows the "Other" category in the legend.
    - sort_values_index (bool): If True, sorts the index categories by group sum
    - sort_values_color (bool): If True, sorts the columns categories by group sum
    - show_pct_all (bool): If True, formats the bar text with percentages from the total n.
    - show_pct_bar (bool): If True, formats the bar text with percentages from the bar's total.

    Returns: None
    """
    BAR_LENGTH_MULTIPLIER = 1.05

    # * 2 axis means at least 2 columns
    if len(df.columns) < 2 or len(df.columns) > 3:
        print("❌ df must have exactly 2 or 3 columns")
        return

    # ! do not enforce str columns anymore
    # # * check if first 2 columns are str
    # dtypes = set(df.iloc[:, [0, 1]].dtypes)
    # dtypes_kind = [i.kind for i in dtypes]

    # if set(dtypes_kind) - set(["O", "b"]):
    #     print("❌ first 2 columns must be str")
    #     # * overkill ^^
    # df.iloc[:, [0, 1]] = df.iloc[:, [0, 1]].astype(str)

    # # * but last col must be numeric
    # if df.iloc[:, -1].dtype.kind not in ("f", "i"):
    #     print("❌ last column must be numeric")
    #     return

    df = df.copy()  # Copy the input DataFrame to avoid modifying the original

    # * add count column[2] as a service if none is present
    if len(df.columns) == 2:
        df["cnt"] = 1

    # * handle null values
    if not dropna:
        df = df.fillna(null_label)
    else:
        df.dropna(inplace=True)

    # * strip whitespaces if columns are str
    if df.iloc[:, 0].dtype.kind == "O":
        df.iloc[:, 0] = df.iloc[:, 0].str.strip()
    if df.iloc[:, 1].dtype.kind == "O":
        df.iloc[:, 1] = df.iloc[:, 1].str.strip()

    # * apply precision
    df.iloc[:, 2] = df.iloc[:, 2].round(precision)

    # # * set index + color col
    col_index = df.columns[0] if not swap else df.columns[1]
    col_color = df.columns[1] if not swap else df.columns[0]

    # * ensure df is grouped to prevent false aggregations
    df = df.groupby([df.columns[0], df.columns[1]])[df.columns[2]].sum().reset_index()

    # * add total as aggregation of df
    if show_total:
        df_total = df.groupby(df.columns[1], observed=True, as_index=False)[
            df.columns[2]
        ].sum()
        df_total[df.columns[0]] = " Total"
        df = pd.concat([df, df_total], ignore_index=True)

    # * calculate n
    divider = 2 if show_total else 1
    n = int(df.iloc[:, 2].sum() / divider)

    # * title str
    _title_str_top_index = f"TOP{top_n_index} " if top_n_index > 0 else ""
    _title_str_top_color = f"TOP{top_n_color} " if top_n_color > 0 else ""
    _title_str_null = f", NULL excluded" if dropna else ""
    _title_str_n = f", n={len(df):_} ({n:_})"

    _df = df.copy().assign(facet=None)
    _df.columns = (
        ["index", "col", "value", "facet"]
        if not swap
        else ["col", "index", "value", "facet"]
    )

    aggregated_df = aggregate_data(
        df=_df,
        top_n_index=top_n_index,
        top_n_color=top_n_color,
        top_n_facet=0,
        null_label=null_label,
        show_other=show_other,
        sort_values_index=sort_values_index,
        sort_values_color=sort_values_color,
        sort_values_facet=False,  # just a placeholder
    )

    df = aggregated_df.copy()

    # * calculate bar totals
    bar_totals = df.groupby("index")["value"].transform("sum")

    caption = _set_caption(caption)

    # * after grouping add cols for pct and formatting
    df["cnt_pct_all_only"] = (df["value"] / n * 100).apply(lambda x: f"{(x):.{precision}f}%")
    df["cnt_pct_bar_only"] = (df["value"] / bar_totals * 100).apply(lambda x: f"{(x):.{precision}f}%")

    # * format output
    df["cnt_str"] = df["value"].apply(lambda x: f"{x:_.{precision}f}")

    divider2 = "<br>" if orientation == "v" else " "
    
    # Modify this section
    df["cnt_pct_all_str"] = df.apply(
        lambda row: f"{row['cnt_str']}{divider2}({row['cnt_pct_all_only']})"
        if (row["value"] / n * 100) >= 5 else row["cnt_str"],
        axis=1
    )
    df["cnt_pct_bar_str"] = df.apply(
        lambda row: f"{row['cnt_str']}{divider2}({row['cnt_pct_bar_only']})"
        if (row["value"] / bar_totals.loc[row.name] * 100) >= 5 else row["cnt_str"],
        axis=1
    )

    text_to_show = "cnt_str"
    if show_pct_all:
        text_to_show = "cnt_pct_all_str"
    elif show_pct_bar:
        text_to_show = "cnt_pct_bar_str"

    if sort_values_color:
        colors_unique = (
            df.groupby("col", observed=True)["value"]
            .sum()
            .sort_values(ascending=False)
            .index.tolist()
        )
    else:
        colors_unique = sorted(df["col"].unique().tolist())

    if sort_values_index:
        index_unique = (
            df.groupby("index", observed=True)["value"]
            .sum()
            .sort_values(ascending=False)
            .index.tolist()
        )
    else:
        index_unique = sorted(df["index"].unique().tolist())

    color_map = assign_column_colors(colors_unique, color_palette, null_label)

    cat_orders = {
        "index": index_unique,
        "col": colors_unique,
    }

    # Ensure bl is categorical with the correct order
    df["index"] = pd.Categorical(
        df["index"], categories=cat_orders["index"], ordered=True
    )

    # * plot
    fig = px.bar(
        df,
        x="index" if orientation == "v" else "value",
        y="value" if orientation == "v" else "index",
        # color=columns,
        color="col",
        text=text_to_show,
        orientation=orientation,
        title=title
        or f"{caption}{_title_str_top_index}[{col_index}] by {_title_str_top_color}[{col_color}]{_title_str_null}{_title_str_n}",
        template="plotly_dark" if os.getenv("THEME") == "dark" else "plotly",
        color_discrete_map=color_map,  # Use assigned colors
        category_orders=cat_orders,
    )

    # print(cat_orders)
    # print(color_map)
    # display(df)

    # * get longest bar
    bar_max = (
        df.groupby("index")["value"].sum().sort_values(ascending=False).iloc[0]
        * BAR_LENGTH_MULTIPLIER
    )
    # * ignore if bar mode is on
    if not relative:
        if orientation == "v":
            fig.update_yaxes(range=[0, bar_max])
        else:
            fig.update_xaxes(range=[0, bar_max])
    else:
        fig.update_layout(barnorm="percent")

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
    )
    fig.update_layout(legend_traceorder="normal")
    fig.update_layout(legend_title_text=col_color)

    # * set dtick
    if orientation == "h":
        if relative:
            fig.update_xaxes(dtick=5)
        # bug dticks are ultra dense
        # elif normalize:
        #     fig.update_xaxes(dtick=0.05)
    else:
        if relative:
            fig.update_yaxes(dtick=5)
        # elif normalize:
        #     fig.update_yaxes(dtick=0.05)

    # * show grids, set to smaller distance on pct scale
    fig.update_xaxes(showgrid=True, gridwidth=1)
    fig.update_yaxes(showgrid=True, gridwidth=1)

    fig.update_layout(
        width=width,
        height=height,
    )

    # * save to png if path is provided
    if png_path is not None:
        fig.write_image(Path(png_path).as_posix())

    fig.show(
        renderer=renderer or os.getenv("RENDERER"),
        width=width,
        height=height,
    )

    return

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
            if not (df_in.iloc[:, 0].dtype.kind in ["O", "b"]) or not (
                df_in.iloc[:, 1].dtype.kind in ["i", "f"]
            ):
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
                    lambda x: mean_confidence_interval(
                        x, use_median=(ci_agg == "median")
                    )[1],
                ),
            )
            .reset_index()
        )
        # * enforce vertical bars **when using ci**, normalize=False, dropna=True, set empty margin to 0 to avoid dropping the bar
        orientation = "v"
        normalize = False
        dropna = True
        df.margin.fillna(0, inplace=True)
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
        f", n={n_len:_} ({n:_})"
        if not use_ci
        else f", n={n_len:_})<br><sub>ci(95) on {ci_agg}s<sub>"
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
    renderer: Literal["png", "svg", None] = None,
    caption: str = None,
    title: str = None,
    png_path: Path | str = None,
    summary: bool = False,
) -> None:
    """
    A function to plot a histogram based on *numeric* columns in a DataFrame.
    Accepts:
        - a numeric series
        - a dataframe with only numeric columns

    Parameters:
        df_ser (pd.DataFrame | pd.Series): The input containing the data to be plotted.
        histnorm (Literal["probability", "probability density", "density", "percent", None]): The normalization mode for the histogram. Default is None.
        nbins (int): The number of bins in the histogram. Default is 0. If its set to -1, the number of bins will represent the integer span of the data.
        orientation (Literal["h", "v"]): The orientation of the histogram. Default is "v".
        precision (int): The precision for rounding the data. Default is 2.
        height (int): The height of the plot. Default is 500.
        width (int): The width of the plot. Default is 1600.
        text_auto (bool): Whether to automatically display text on the plot. Default is True.
        barmode (Literal["group", "overlay", "relative"]): The mode for the bars in the histogram. Default is "relative".
        renderer (Literal["png", "svg", None]): The renderer for displaying the plot. Default is None.
        caption (str): The caption for the plot. Default is None.
        title (str): The title of the plot. Default is None.
        png_path (Path | str, optional): The path to save the image as a png file. Defaults to None.
        print_summary (bool): Whether to print a summary table of the data. Default is False.


    Returns: None
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

    # * nbins defaults to number of unique values
    if nbins == -1:
        nbins = int(df.max() - df.min())

    # ! plot
    _caption = _set_caption(caption)
    fig = px.histogram(
        data_frame=df,
        histnorm=histnorm,
        nbins=nbins,
        marginal="box",
        barmode=barmode,
        text_auto=text_auto,
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
    
    fig.update_layout(
        width=width,
        height=height,
    )    

    fig.show(
        renderer=renderer or os.getenv("RENDERER"),
        width=width,
        height=height,
    )

    # * save to png if path is provided
    if png_path is not None:
        fig.write_image(Path(png_path).as_posix())

    if summary:
        tbl.print_summary(df)

    return


def plot_joint(
    df: pd.DataFrame,
    kind: Literal["reg", "hist", "hex", "kde"] = "hex",
    precision: int = 2,
    size: int = 5,
    dropna: bool = False,
    caption: str = "",
    title: str = "",
    png_path: Path | str = None,
) -> None:
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

    Returns: None
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

    return


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
    use_log: bool = False,
    png_path: Path | str = None,
    renderer: Literal["png", "svg", None] = None,
) -> None:
    """
    Plots a horizontal box plot for the given pandas Series.

    Args:
        ser: The pandas Series to plot.
        points: The type of points to plot on the box plot ('all', 'outliers', 'suspectedoutliers', None).
        precision: The precision of the annotations.
        height: The height of the plot.
        width: The width of the plot.
        annotations: Whether to add annotations to the plot.
        summary: Whether to add a summary table to the plot.
        caption: The caption for the plot.
        title: The title of the plot.
        violin: Use violin plot or not.
        x_min: The minimum value for the x-axis scale (max and min must be set).
        x_max: The maximum value for the x-axis scale (max and min must be set).
        use_log: Use logarithmic scale for the axis.
        png_path (Path | str, optional): The path to save the image as a png file. Defaults to None.
        renderer (Literal["png", "svg", None], optional): The renderer to use for saving the image. Defaults to None.

    Returns: None
    """
    ser = to_series(ser)
    if ser is None:
        return

    # * drop na to keep scipy sane
    n_ = len(ser)
    ser.dropna(inplace=True)
    # n = len(ser)

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
    log_str = " (log-scale)" if use_log else ""
    dict = {
        "data_frame": ser,
        "orientation": "h",
        "template": "plotly_dark" if os.getenv("THEME") == "dark" else "plotly",
        "points": points,
        # 'box':True,
        "log_x": use_log,  # * logarithmic scale, axis is always x
        # "notched": True,
        "title": f"{caption}[{ser.name}]{log_str}, n = {n_:_}" if not title else title,
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

    fig.update_layout(
        width=width,
        height=height,
    )

    fig.show(
        renderer=renderer or os.getenv("RENDERER"),
        width=width,
        height=height,
    )

    if summary:
        # * if only series is provided, col name is None
        print_summary(ser.to_frame())

    # * save to png if path is provided
    if png_path is not None:
        fig.write_image(Path(png_path).as_posix())

    return


def plot_boxes(
    df: pd.DataFrame,
    caption: str = None,
    points: Literal["all", "outliers", "suspectedoutliers", None] = None,
    precision: int = 2,
    height: int = 600,
    width: int = 1200,
    annotations: bool = True,
    summary: bool = True,
    title: str = None,
    use_log: bool = False,
    box_width: float = 0.5,
    png_path: Path | str = None,
    renderer: Literal["png", "svg", None] = None,
) -> None:
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
        use_log (bool): Whether to use logarithmic scale for the plot (cannot show negative values).
        png_path (Path | str, optional): The path to save the image as a png file. Defaults to None.
        renderer (Literal["png", "svg", None], optional): The renderer to use for saving the image. Defaults to None.

    Returns: None
    """

    if (
        len(df.columns) != 2
        or not (
            (pd.api.types.is_object_dtype(df.iloc[:, 0]))
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
    
    # * type of col0 must be str, not object. otherwise px.box will fail since sorting will fail
    if pd.api.types.is_object_dtype(df.iloc[:, 0]):
        df.iloc[:, 0] = df.iloc[:, 0].astype(str)

    # * unique items
    # Sort the unique items alphabetically
    items = sorted(df.iloc[:, 0].unique())

    caption = _set_caption(caption)
    log_str = " (log-scale)" if use_log else ""

    # * main plot
    fig = px.box(
        df,
        x=df.iloc[:, 0],
        y=df.iloc[:, 1],
        color=df.iloc[:, 0],
        template="plotly_dark" if os.getenv("THEME") == "dark" else "plotly",
        orientation="v",
        points=points,
        log_y=use_log,
        # color_discrete_sequence=px.colors.qualitative.Plotly,
        title=(
            f"{caption}[{df.columns[0]}] by [{df.columns[1]}]{log_str}, n = {len(df):_.0f}"
            if not title
            else title
        ),
    )

    # * Set the order of the x-axis categories
    fig.update_xaxes(categoryorder="array", categoryarray=items)

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
    fig.update_layout(boxmode="group")  # Ensures boxes are not too compressed
    fig.update_layout(showlegend=False)
    fig.update_traces(
        marker=dict(size=5), width=box_width
    )  # Adjust width (default ~0.5)

    fig.show(renderer=renderer or os.getenv("RENDERER"), width=width, height=height)
    if summary:
        # * sort df by first column
        print_summary(df=df.sort_values(df.columns[0]), precision=precision)

    # * save to png if path is provided
    if png_path is not None:
        fig.write_image(Path(png_path).as_posix())

    return


def plot_facet_stacked_bars(
    df: pd.DataFrame,
    subplots_per_row: int = 4,
    top_n_index: int = 0,
    top_n_color: int = 0,
    top_n_facet: int = 0,
    null_label: str = "<NA>",
    subplot_size: int = 300,
    color_palette: str = "Plotly",
    caption: str = "",
    renderer: Optional[Literal["png", "svg", None]] = "png",
    annotations: bool = False,
    precision: int = 0,
    png_path: Optional[Path] = None,
    show_other: bool = False,
    sort_values: bool = True,
    sort_values_index: bool = False,
    sort_values_color: bool = False,
    sort_values_facet: bool = False,
    relative: bool = False,
    show_pct: bool = False,
) -> None:

    """
    A function to plot multiple (subplots_per_row) stacked bar charts, facetted by the third column, with the first column as the index and the second column as the colors.

    Parameters:
    - df (pd.DataFrame): Input DataFrame with 3 or 4 columns.
    - subplots_per_row (int): The number of subplots to display per row.
    - top_n_index (int): The number of top indexes to include in the chart. Default is 0, which includes all indexes.
    - top_n_color (int): The number of top colors to include in the chart. Default is 0, which includes all colors.
    - top_n_facet (int): The number of top facets to include in the chart. Default is 0, which includes all facets.
    - null_label (str): The label to use for null values. Default is "<NA>".
    - subplot_size (int): The size of each subplot in pixels. Default is 300.
    - color_palette (str): The name of the color palette to use. Default is "Plotly".
    - caption (str): An optional string indicating the caption for the chart.
    - renderer (str): The output format. Default is "png".
    - annotations (bool): Whether to include annotations on the chart. Default is False.
    - precision (int): The number of decimal places to round the values to. Default is 0.
    - png_path (str): The path to save the chart to, if provided.
    - show_other (bool): Whether to include "<other>" for columns not in top_n_color. Default is False.
    - sort_values (bool): Whether to sort the values in the chart. Default is True.
    - sort_values_index (bool): Whether to sort the index column. Default is False.
    - sort_values_color (bool): Whether to sort the color column. Default is False.
    - sort_values_facet (bool): Whether to sort the facet column. Default is False.
    - relative (bool): Whether to show the bars as relative values (0-1 range). Default is False.
    - show_pct (bool): Whether to show the annotations as percentages. Default is False.

    Returns: None
    """
    # ENFORCE show_pct RULES ---
    if not relative:
        # If bars are absolute, annotations MUST be absolute
        if show_pct:
            print(
                "Warning: 'show_pct' cannot be True when 'relative' is False. Setting 'show_pct' to False."
            )
            show_pct = False
    # 

    try:
        precision = int(precision)
    except (ValueError, TypeError):
        print(
            f"Warning: 'precision' received as {precision} (type: {type(precision)}). Defaulting to 0."
        )
        precision = 0

    df_copy = df.copy()

    if not (df_copy.shape[1] == 3 or df_copy.shape[1] == 4):
        raise ValueError("Input DataFrame must have 3 or 4 columns.")

    original_column_names = df_copy.columns.tolist()

    if df_copy.shape[1] == 3:
        df_copy.columns = ["index", "col", "facet"]
        df_copy["value"] = 1
    elif df_copy.shape[1] == 4:
        df_copy.columns = ["index", "col", "facet", "value"]

    n = df_copy["value"].sum()
    original_rows = len(df_copy)

    aggregated_df = aggregate_data(  # Assumes aggregate_data is accessible
        df_copy,
        top_n_index,
        top_n_color,
        top_n_facet,
        null_label,
        show_other=show_other,
        sort_values_index=sort_values_index,
        sort_values_color=sort_values_color,
        sort_values_facet=sort_values_facet,
    )

    aggregated_df["index"] = aggregated_df["index"].astype(str)
    aggregated_df["col"] = aggregated_df["col"].astype(str)
    aggregated_df["facet"] = aggregated_df["facet"].astype(str)

    # --- Store original 'value' for annotations before potential scaling ---
    aggregated_df["annotation_value"] = aggregated_df["value"].copy()
    # ----------------------------------------------------------------------

    if relative:
        # This transforms the bar heights (value column) to percentages (0-1 range)
        aggregated_df["value"] = aggregated_df.groupby(["facet", "index"])[
            "value"
        ].transform(lambda x: x / x.sum())

    category_orders = {}

    if sort_values_index:
        sum_by_index = (
            aggregated_df.groupby("index")["value"].sum().sort_values(ascending=False)
        )
        category_orders["index"] = sum_by_index.index.tolist()

    if sort_values_color:
        sum_by_col = (
            aggregated_df.groupby("col")["value"].sum().sort_values(ascending=False)
        )
        category_orders["col"] = sum_by_col.index.tolist()

    if sort_values_facet:
        sum_by_facet = (
            aggregated_df.groupby("facet")["value"].sum().sort_values(ascending=False)
        )
        category_orders["facet"] = sum_by_facet.index.tolist()

    columns_for_color = sorted(aggregated_df["col"].unique().tolist())
    column_colors_map = assign_column_colors(
        columns_for_color, color_palette, null_label
    )  # Assumes assign_column_colors is accessible

    #  Prepare the text series for annotations with 'show_pct' control
    if annotations:
        if show_pct:
            # When show_pct is True, use the scaled 'value' column (0-1) and format as percentage
            formatted_text_series = aggregated_df["value"].apply(
                lambda x: f"{x:.{precision}%}".replace(".", ",")
            )
        else:
            # When show_pct is False, use the 'annotation_value' (original absolute) and format as absolute
            formatted_text_series = aggregated_df["annotation_value"].apply(
                lambda x: f"{x:_.{precision}f}".replace(".", ",")
            )
    else:
        formatted_text_series = None
    # - - - -

    fig = px.bar(
        aggregated_df,
        x="index",
        y="value",
        color="col",
        facet_col="facet",
        facet_col_wrap=subplots_per_row,
        barmode="stack",
        color_discrete_map=column_colors_map,
        category_orders=category_orders,
        text=formatted_text_series,
        text_auto=False,
        # height=subplot_size * (-(-len(aggregated_df["facet"].unique()) // subplots_per_row)),
        title=f"{caption} {original_column_names[0]}, {original_column_names[1]}, {original_column_names[2]}",
    )

    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

    fig.update_xaxes(matches=None)
    for axis in fig.layout:
        if axis.startswith("xaxis"):
            fig.layout[axis].showticklabels = True

    template = "plotly_dark" if os.getenv("THEME") == "dark" else "plotly"

    layout_updates = {
        "title_text": f"{caption} "
        f"{'TOP ' + str(top_n_index) + ' ' if top_n_index > 0 else ''}[{original_column_names[0]}] "
        f"{'TOP ' + str(top_n_color) + ' ' if top_n_color > 0 else ''}[{original_column_names[1]}] "
        f"{'TOP ' + str(top_n_facet) + ' ' if top_n_facet > 0 else ''}[{original_column_names[2]}] "
        f", n = {original_rows:_} ({n:_})",
        "showlegend": True,
        "template": template,
        # "width": subplot_size * subplots_per_row,
    }

    if relative:
        layout_updates["yaxis_range"] = [0, 1.1]
        layout_updates["yaxis_tickformat"] = ".0%"

    fig.update_layout(**layout_updates)

    if relative:
        fig.update_yaxes(tickformat=".0%")

    fig.update_layout(
        width=subplot_size * subplots_per_row,
        height=subplot_size
        * (-(-len(aggregated_df["facet"].unique()) // subplots_per_row)),
    )

    if png_path:
        png_path = Path(png_path)
        fig.write_image(str(png_path))

    fig.show(
        renderer=renderer or os.getenv("RENDERER"),
        width=subplot_size * subplots_per_row,
        height=subplot_size
        * (-(-len(aggregated_df["facet"].unique()) // subplots_per_row)),
    )

    return


def plot_sankey(
    df=None,
    max_events_per_id=None,
    height=None,
    width=None,
    exclude_overlap_id=False,
    exclude_overlap_event=False,
    renderer=None,
    show_start_node=True,
    font_size=10,
):
    """
    Generates a Sankey diagram from a Pandas DataFrame, assuming the column order is:
    1. ID (string or integer)
    2. Date (date, datetime, or string convertible to numeric)
    3. Event Name (string)

    Nodes represent the order of events (e.g., "[1] op", "[2] syst").
    A default demo is shown if no DataFrame is provided.

    Args:
        df (pd.DataFrame, optional): A Pandas DataFrame containing the event data.
                        Expected column order: ID, Date, Event.
        max_events_per_id (int, optional): The maximum number of events to display for each ID.
                                        If None, all events for each ID will be used.
        height (int, optional): The height of the plot in pixels.
        width (int, optional): The width of the plot in pixels.
        exclude_overlap_id (bool): If True, excludes any IDs that have multiple events on the same date.
                                This takes precedence over `exclude_overlap_event`.
        exclude_overlap_event (bool): If True, only excludes the specific events that fall on the same date,
                                    retaining other non-overlapping events for that ID.
        renderer (str, optional): The renderer to use for displaying the plot. Options include
                                'browser', None, 'json', 'png', 'svg', 'jpeg', 'webp', or 'pdf'.
                                If None, plotly's default renderer is used.
        show_start_node (bool): If True, adds a visual 'start' node and links all
                                first events to it. This is useful for visualizing
                                IDs with only one event.
        font_size (int): The font size of the labels in the plot.
    """
    # --- Example Usage with Enlarged Pandas DataFrame if no DataFrame is provided ---
    if df is None:
        data_demo = {  # Renamed to data_demo for clarity
            "tumor-id": [
                "1",
                "1",
                "1",
                "1",
                "1",
                "2",
                "2",
                "2",
                "2",
                "3",
                "3",
                "3",
                "3",
                "4",
                "4",
                "4",
                "5",
                "5",
                "6",
                "6",
                "7",
                "7",
                "8",
                "9",
                "10",
                "11",
                "12",
            ],
            "diagnosis date": [
                "2020-01-01",
                "2021-02-01",
                "2022-03-01",
                "2023-04-01",
                "2024-05-01",  # Tumor 1
                "2010-01-01",
                "2011-02-01",
                "2012-03-01",
                "2013-04-01",  # Tumor 2
                "2015-01-01",
                "2016-02-01",
                "2017-03-01",
                "2018-04-01",  # Tumor 3
                "2005-01-01",
                "2006-02-01",
                "2007-03-01",  # Tumor 4
                "2019-01-01",
                "2020-02-01",  # Tumor 5
                "2021-01-01",
                "2022-02-01",  # Tumor 6
                "2014-01-01",
                "2015-02-01",  # Tumor 7
                "2025-01-01",  # Tumor 8 (single event)
                "2025-02-01",  # Tumor 9 (single event)
                "2025-03-01",  # Tumor 10 (single event)
                "2025-04-01",  # Tumor 11 (single event)
                "2025-05-01",  # Tumor 12 (single event)
            ],
            "treatment": [
                "op",
                "syst",
                "op",
                "rad",
                "op",  # Tumor 1
                "syst",
                "st",
                "op",
                "rad",  # Tumor 2
                "op",
                "rad",
                "syst",
                "op",  # Tumor 3
                "st",
                "syst",
                "op",  # Tumor 4
                "op",
                "rad",  # Tumor 5
                "syst",
                "op",  # Tumor 6
                "st",
                "rad",  # Tumor 7
                "op",  # Tumor 8
                "op",  # Tumor 9
                "syst",  # Tumor 10
                "rad",  # Tumor 11
                "op",  # Tumor 12
            ],
        }
        df = pd.DataFrame(data_demo)
        print("--- Using demo data (data_demo) ---")
        print(df.head().to_string())  # Print first 5 rows of the DataFrame prettily
        print("-----------------------------------")

    # --- Simplified Column Recognition based on index ---
    id_col_name = df.columns[0]
    date_col_name = df.columns[1]
    event_col_name = df.columns[2]

    df_processed = df.copy()

    # --- Aggregate the data to remove duplicate rows before processing ---
    df_processed = df_processed.drop_duplicates(
        subset=[id_col_name, date_col_name, event_col_name]
    )

    try:
        df_processed[date_col_name] = pd.to_datetime(df_processed[date_col_name])
    except (ValueError, TypeError):
        print(
            f"Error: Could not convert column '{date_col_name}' to a valid date format."
        )
        return None

    # --- Handle overlap exclusion based on user selection ---
    overlap_title_part = ""
    if exclude_overlap_id:
        overlapping_ids = (
            df_processed.groupby([id_col_name, date_col_name])
            .size()
            .loc[lambda x: x > 1]
            .index.get_level_values(id_col_name)
            .unique()
        )
        df_processed = df_processed[
            ~df_processed[id_col_name].isin(overlapping_ids)
        ].copy()
        overlap_title_part = ", overlap ids excluded"
    elif exclude_overlap_event:
        overlapping_event_set = set(
            df_processed.groupby([id_col_name, date_col_name])
            .size()
            .loc[lambda x: x > 1]
            .index
        )
        df_processed = df_processed[
            ~df_processed.set_index([id_col_name, date_col_name]).index.isin(
                overlapping_event_set
            )
        ].copy()
        overlap_title_part = ", overlap events excluded"

    df_sorted = df_processed.sort_values(by=[id_col_name, date_col_name])

    # --- Performance Optimization: Use vectorized operations instead of loops ---
    df_sorted["event_order"] = df_sorted.groupby(id_col_name).cumcount() + 1

    if max_events_per_id is not None:
        df_sorted = df_sorted[df_sorted["event_order"] <= max_events_per_id]

    df_sorted["ordered_event_label"] = (
        "[" + df_sorted["event_order"].astype(str) + "] " + df_sorted[event_col_name]
    )

    if df_sorted.empty:
        print("No valid data to plot after filtering.")
        return None

    # Use a vectorized shift operation to create source and target columns
    df_sorted["source_label"] = df_sorted.groupby(id_col_name)[
        "ordered_event_label"
    ].shift(1)
    df_with_links = df_sorted.dropna(subset=["source_label"]).copy()

    # Create the start node and links if enabled
    if show_start_node:
        first_events = df_sorted.groupby(id_col_name).first().reset_index()
        first_events["source_label"] = "[0] start"
        df_with_links = pd.concat(
            [
                first_events[["source_label", "ordered_event_label"]],
                df_with_links[["source_label", "ordered_event_label"]],
            ],
            ignore_index=True,
        )

    link_counts = (
        df_with_links.groupby(["source_label", "ordered_event_label"])
        .size()
        .reset_index(name="value")
    )

    # Get all unique nodes for the labels and sorting
    all_labels = pd.concat(
        [link_counts["source_label"], link_counts["ordered_event_label"]]
    ).unique()
    unique_labels_df = pd.DataFrame(all_labels, columns=["label"])
    unique_labels_df["event_order_num"] = (
        unique_labels_df["label"].str.extract(r"\[(\d+)\]").astype(float).fillna(0)
    )
    unique_labels_df["event_name"] = (
        unique_labels_df["label"].str.extract(r"\] (.*)").fillna("start")
    )
    unique_labels_df_sorted = unique_labels_df.sort_values(
        by=["event_order_num", "event_name"]
    )
    unique_unformatted_labels_sorted = unique_labels_df_sorted["label"].tolist()

    label_to_index = {
        label: i for i, label in enumerate(unique_unformatted_labels_sorted)
    }

    # Calculate total unique IDs for percentage calculation
    total_unique_ids = df_processed[id_col_name].nunique()

    display_labels = []
    node_counts = df_sorted["ordered_event_label"].value_counts()
    for label in unique_unformatted_labels_sorted:
        if label == "[0] start":
            count = total_unique_ids
        else:
            count = node_counts.get(label, 0)

        percentage = (count / total_unique_ids) * 100
        formatted_count = f"{count:,}".replace(",", "_")
        formatted_percentage = f"({int(round(percentage, 0))}%)"

        display_labels.append(f"{label} {formatted_count} {formatted_percentage}")

    # Map sources and targets to indices
    sources = link_counts["source_label"].map(label_to_index).tolist()
    targets = link_counts["ordered_event_label"].map(label_to_index).tolist()
    values = link_counts["value"].tolist()

    # Define a color palette for links
    color_palette = [
        "rgba(255, 99, 71, 0.6)",
        "rgba(60, 179, 113, 0.6)",
        "rgba(65, 105, 225, 0.6)",
        "rgba(255, 215, 0, 0.6)",
        "rgba(147, 112, 219, 0.6)",
        "rgba(0, 206, 209, 0.6)",
        "rgba(255, 160, 122, 0.6)",
        "rgba(124, 252, 0, 0.6)",
        "rgba(30, 144, 255, 0.6)",
        "rgba(218, 165, 32, 0.6)",
    ]
    start_link_color = "rgba(128, 128, 128, 0.6)"

    link_colors = []
    link_type_to_color = {}
    color_index = 0
    for i, row in link_counts.iterrows():
        source_l = row["source_label"]
        target_l = row["ordered_event_label"]
        if source_l == "[0] start":
            link_colors.append(start_link_color)
        else:
            source_event_name = re.search(r"\] (.*)", source_l).group(1)
            target_event_name = re.search(r"\] (.*)", target_l).group(1)
            link_type = (source_event_name, target_event_name)

            if link_type not in link_type_to_color:
                link_type_to_color[link_type] = color_palette[
                    color_index % len(color_palette)
                ]
                color_index += 1
            link_colors.append(link_type_to_color[link_type])

    formatted_total_ids = f"{total_unique_ids:,}".replace(",", "_")
    total_rows = len(df_processed)
    formatted_total_rows = f"{total_rows:,}".replace(",", "_")

    chart_title = f"[{id_col_name}] over [{event_col_name}]"
    if max_events_per_id is not None:
        chart_title += f", top {max_events_per_id} events"
    chart_title += overlap_title_part
    chart_title += f", n = {formatted_total_ids} ({formatted_total_rows})"

    fig = go.Figure(
        data=[
            go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=display_labels,
                    color="blue",
                    align="left",
                ),
                link=dict(
                    source=sources, target=targets, value=values, color=link_colors
                ),
            )
        ]
    )


    fig.update_layout(title_text=chart_title, font_size=font_size, width=width, height=height)
    fig.show(renderer=renderer or os.getenv("RENDERER"), width=width, height=height)


def plot_pie(
    data: pd.Series | pd.DataFrame,
    caption: str = None,
    width=800,
    height=500,
    renderer="notebook",
    donut_size=0,
):
    """
    Creates and displays a pie or donut chart using Plotly Express.

    Args:
        data (pd.Series or pd.DataFrame): The data to plot.
            If a DataFrame, it must have only one column. The index will be
            used for labels and the values for the pie slice sizes.
        caption (str): The title for the plot.
        height (int, optional): The height of the plot in pixels. Defaults to 800.
        width (int, optional): The width of the plot in pixels. Defaults to 500.
        renderer (str, optional): The Plotly renderer to use (e.g., 'notebook', 'png', 'svg').
            Defaults to 'notebook'.
        donut_size (float, optional): A value between 0 and 1 to create a donut chart.
            A value of 0 results in a regular pie chart. Defaults to 0.
    """
    # Store the original renderer to restore it later
    # original_renderer = pio.renderers.default
    # ? override renderer
    original_renderer = "notebook"

    # * 1. Check for correct data type first
    if not isinstance(data, (pd.Series, pd.DataFrame)):
        print("Error: Data must be a pandas Series or DataFrame.")
        return

    # * 2. **CONVERT SERIES TO DATAFRAME**
    if isinstance(data, pd.Series):
        # * Get the name of the Series
        label = data.name
        # * Convert the Series to a DataFrame with a column named 'values'
        # * The index will automatically become the DataFrame index
        data = data.to_frame(name="values")
    else:
        # * Get the name of the first column
        label = data.columns[0]

    # * 3. Ensure the DataFrame has only one column
    if len(data.columns) != 1:
        print("Error: DataFrame must have exactly one column for this function.")
        return

    # * Set the temporary renderer for the plot
    pio.renderers.default = renderer

    # * Get the number of observations
    n = len(data)

    # * take 1st (only) column and use value counts to get distribution
    data = data.iloc[:, 0].value_counts()

    # * 4. Create the figure
    fig = px.pie(
        data,
        values=data,
        names=data.index,
        title=f"{_set_caption(caption)}{label}, n = {n:_}",
        height=height,
        width=width,
        hole=donut_size,
        template="plotly_dark" if os.getenv("THEME") == "dark" else "plotly",
    )

    # * Display the plot
    fig.show()

    # finally:
    # * 5. Restore the original renderer, ensuring it's always done
    pio.renderers.default = original_renderer



# * extend objects to enable chaining
pd.DataFrame.plot_bars = plot_bars
pd.DataFrame.plot_stacked_bars = plot_stacked_bars
pd.DataFrame.plot_facet_stacked_bars = plot_facet_stacked_bars
pd.DataFrame.plot_stacked_box = plot_box
pd.DataFrame.plot_stacked_boxes = plot_boxes
pd.DataFrame.plot_quadrants = plot_quadrants
pd.DataFrame.plot_histogram = plot_histogram
pd.DataFrame.plot_joint = plot_joint
pd.DataFrame.plot_sankey = plot_sankey
pd.DataFrame.plot_pie = plot_pie
