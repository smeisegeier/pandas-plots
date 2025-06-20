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
import plotly  # needed for return types

from .hlp import *
from .tbl import print_summary

### helper functions


def _set_caption(caption: str) -> str:
    return f"#️⃣{'-'.join(caption.split())}, " if caption else ""


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
            .sort_values(ascending=False)[:top_n_index or None]
            .index
        )
    
    else:
        top_indexes = aggregated_df["index"].sort_values().unique()[:top_n_index or None]

    aggregated_df = aggregated_df[aggregated_df["index"].isin(top_indexes)]

    if sort_values_color:
        top_colors = (
            aggregated_df.groupby("col")["value"]
            .sum()
            .sort_values(ascending=False)[:top_n_color or None]
            .index
        )
    else:
        top_colors = aggregated_df["col"].sort_values().unique()[:top_n_color or None]

    others_df = df[~df["col"].isin(top_colors)]
    aggregated_df = aggregated_df[aggregated_df["col"].isin(top_colors)]
    if show_other and top_n_color > 0 and not others_df.empty:
        other_agg = others_df.groupby(["index", "facet"], as_index=False)[
            "value"
        ].sum()
        other_agg["col"] = "<other>"
        other_agg = other_agg[["index", "col", "facet", "value"]]
        aggregated_df = pd.concat([aggregated_df, other_agg], ignore_index=True)
        top_colors = [*top_colors, "<other>"]

    if sort_values_facet:
        top_facets = (
            aggregated_df.groupby("facet")["value"]
            .sum()
            .sort_values(ascending=False)[:top_n_facet or None]
            .index
        )
    else:
        top_facets = aggregated_df["facet"].sort_values().unique()[:top_n_facet or None]

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
    renderer: Literal["png", "svg", None] = "png",
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
) -> plotly.graph_objects:
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

    Returns:
    - A Plotly figure object representing the stacked bar chart.
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
        sort_values_facet=False, # just a placeholder
    )

    df = aggregated_df.copy()

    caption = _set_caption(caption)

    # * after grouping add cols for pct and formatting
    df["cnt_pct_only"] = df["value"].apply(lambda x: f"{(x / n) * 100:.{precision}f}%")

    # * format output
    df["cnt_str"] = df["value"].apply(lambda x: f"{x:_.{precision}f}")

    divider2 = "<br>" if orientation == "v" else " "
    df["cnt_pct_str"] = df.apply(
        lambda row: f"{row['cnt_str']}{divider2}({row['cnt_pct_only']})", axis=1
    )

    if sort_values_color:
        colors_unique = (df
            .groupby("col", observed=True)["value"]
            .sum()
            .sort_values(ascending=False)
            .index.tolist()
        )
    else:
        colors_unique = sorted(df["col"].unique().tolist())

    if sort_values_index:
        index_unique = (df
            .groupby("index", observed=True)["value"]
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
    df["index"] = pd.Categorical(df["index"], categories=cat_orders["index"], ordered=True)


    # * plot
    fig = px.bar(
        df,
        x="index" if orientation == "v" else "value",
        y="value" if orientation == "v" else "index",
        # color=columns,
        color="col",
        text="cnt_pct_str" if normalize else "cnt_str",
        orientation=orientation,
        title=title
        or f"{caption}{_title_str_top_index}[{col_index}] by {_title_str_top_color}[{col_color}]{_title_str_null}{_title_str_n}",
        template="plotly_dark" if os.getenv("THEME") == "dark" else "plotly",
        width=width,
        height=height,
        color_discrete_map=color_map,  # Use assigned colors
        category_orders= cat_orders,
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

    # * save to png if path is provided
    if png_path is not None:
        fig.write_image(Path(png_path).as_posix())

    fig.show(renderer=renderer)

    return fig


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
        df = (df_in
            # ? dont dropna() here, this biases the input data
            .groupby(
                col_index,
                dropna=False,
            )
            .agg(
                mean=(col_name, ci_agg),
                # * retrieve margin from custom func
                margin=(col_name, lambda x: mean_confidence_interval(x, use_median = (ci_agg == "median"))[1]),
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
        f", n={n_len:_} ({n:_})" if not use_ci else f", n={n_len:_})<br><sub>ci(95) on {ci_agg}s<sub>"
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
        error_y=dict(thickness=5)
    )
    if use_ci:
        _fig.update_traces(
            textposition="inside",  # Put labels inside bars
            insidetextanchor="start",  # Align labels at the bottom
            textfont=dict(size=14, color="white")  # Adjust text color for visibility
        )
    else:
        _fig.update_traces(
            textposition="outside",
            # error_y=dict(thickness=0)
        )

    # * set axis title

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
    use_log: bool = False,
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
        summary: Whether to add a summary table to the plot.
        caption: The caption for the plot.
        title: The title of the plot.
        violin: Use violin plot or not.
        x_min: The minimum value for the x-axis scale (max and min must be set).
        x_max: The maximum value for the x-axis scale (max and min must be set).
        use_log: Use logarithmic scale for the axis.
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
        "height": height,
        "width": width,
        "points": points,
        # 'box':True,
        "log_x": use_log,   # * logarithmic scale, axis is always x
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

    fig.show("png")

    if summary:
        # * if only series is provided, col name is None
        print_summary(ser.to_frame())

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
    width: int = 1200,
    annotations: bool = True,
    summary: bool = True,
    title: str = None,
    use_log: bool = False,
    box_width: float = 0.5,
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
        use_log (bool): Whether to use logarithmic scale for the plot (cannot show negative values).
        png_path (Path | str, optional): The path to save the image as a png file. Defaults to None.

    Returns:
        plot object
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
        height=height,
        width=width,
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
    fig.update_traces(marker=dict(size=5), width=box_width)  # Adjust width (default ~0.5)

    fig.show("png")
    if summary:
        # * sort df by first column
        print_summary(df=df.sort_values(df.columns[0]), precision=precision)

    # * save to png if path is provided
    if png_path is not None:
        fig.write_image(Path(png_path).as_posix())

    return fig


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
    renderer: Optional[Literal["png", "svg"]] = "png",
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
) -> go.Figure:

    # --- ENFORCE show_pct RULES ---
    if not relative:
        # If bars are absolute, annotations MUST be absolute
        if show_pct:
            print("Warning: 'show_pct' cannot be True when 'relative' is False. Setting 'show_pct' to False.")
            show_pct = False
    # ------------------------------

    try:
        precision = int(precision)
    except (ValueError, TypeError):
        print(f"Warning: 'precision' received as {precision} (type: {type(precision)}). Defaulting to 0.")
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

    aggregated_df = aggregate_data( # Assumes aggregate_data is accessible
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

    aggregated_df['index'] = aggregated_df['index'].astype(str)
    aggregated_df['col'] = aggregated_df['col'].astype(str)
    aggregated_df['facet'] = aggregated_df['facet'].astype(str)

    # --- Store original 'value' for annotations before potential scaling ---
    aggregated_df['annotation_value'] = aggregated_df['value'].copy()
    # ----------------------------------------------------------------------

    if relative:
        # This transforms the bar heights (value column) to percentages (0-1 range)
        aggregated_df["value"] = aggregated_df.groupby(["facet", "index"])["value"].transform(lambda x: x / x.sum())

    category_orders = {}

    if sort_values_index:
        sum_by_index = aggregated_df.groupby('index')['value'].sum().sort_values(ascending=False)
        category_orders["index"] = sum_by_index.index.tolist()

    if sort_values_color:
        sum_by_col = aggregated_df.groupby('col')['value'].sum().sort_values(ascending=False)
        category_orders["col"] = sum_by_col.index.tolist()

    if sort_values_facet:
        sum_by_facet = aggregated_df.groupby('facet')['value'].sum().sort_values(ascending=False)
        category_orders["facet"] = sum_by_facet.index.tolist()

    columns_for_color = sorted(aggregated_df["col"].unique().tolist())
    column_colors_map = assign_column_colors(columns_for_color, color_palette, null_label) # Assumes assign_column_colors is accessible

    # --- Prepare the text series for annotations with 'show_pct' control ---
    if annotations:
        if show_pct:
            # When show_pct is True, use the scaled 'value' column (0-1) and format as percentage
            formatted_text_series = aggregated_df["value"].apply(lambda x: f"{x:.{precision}%}".replace('.', ','))
        else:
            # When show_pct is False, use the 'annotation_value' (original absolute) and format as absolute
            formatted_text_series = aggregated_df["annotation_value"].apply(lambda x: f"{x:_.{precision}f}".replace('.', ','))
    else:
        formatted_text_series = None
    # -----------------------------------------------------------------------

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
        height=subplot_size * (-(-len(aggregated_df["facet"].unique()) // subplots_per_row)),
        title=f"{caption} {original_column_names[0]}, {original_column_names[1]}, {original_column_names[2]}",
    )

    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

    fig.update_xaxes(matches=None)
    for axis in fig.layout:
        if axis.startswith("xaxis"):
            fig.layout[axis].showticklabels = True

    template = "plotly_dark" if os.getenv("THEME") == "dark" else "plotly"

    layout_updates = {
        "title_text":   f"{caption} "
                        f"{'TOP ' + str(top_n_index) + ' ' if top_n_index > 0 else ''}[{original_column_names[0]}] "
                        f"{'TOP ' + str(top_n_color) + ' ' if top_n_color > 0 else ''}[{original_column_names[1]}] "
                        f"{'TOP ' + str(top_n_facet) + ' ' if top_n_facet > 0 else ''}[{original_column_names[2]}] "
                        f", n = {original_rows:_} ({n:_})",
        "showlegend": True,
        "template": template,
        "width": subplot_size * subplots_per_row,
    }

    if relative:
        layout_updates['yaxis_range'] = [0, 1.1]
        layout_updates['yaxis_tickformat'] = ".0%"

    fig.update_layout(**layout_updates)

    if relative:
        fig.update_yaxes(tickformat=".0%")

    if png_path:
        png_path = Path(png_path)
        fig.write_image(str(png_path))

    fig.show(renderer=renderer)

    return fig

# * extend objects to enable chaining
pd.DataFrame.plot_bars = plot_bars
pd.DataFrame.plot_stacked_bars = plot_stacked_bars
pd.DataFrame.plot_facet_stacked_bars = plot_facet_stacked_bars
pd.DataFrame.plot_stacked_box = plot_box
pd.DataFrame.plot_stacked_boxes = plot_boxes
pd.DataFrame.plot_quadrants = plot_quadrants
pd.DataFrame.plot_histogram = plot_histogram
pd.DataFrame.plot_joint = plot_joint