import os
from pathlib import Path
from typing import Literal, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from ..hlp import *
from ..helper import set_caption, assign_column_colors, aggregate_data
from ..hlp.group_kkr import group_kkr


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
    kkr_col: Optional[str] = None,
    
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
    - kkr_col (str): Edge case: Name of the column that contains kkr name to ensure all kkr are shown

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

    if kkr_col:
        df = group_kkr(df=df, kkr_col=kkr_col)

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
        df_total = df.groupby(df.columns[1], observed=True, as_index=False)[df.columns[2]].sum()
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
    _df.columns = ["index", "col", "value", "facet"] if not swap else ["col", "index", "value", "facet"]

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

    caption = set_caption(caption)

    # * after grouping add cols for pct and formatting
    df["cnt_pct_all_only"] = (df["value"] / n * 100).apply(lambda x: f"{(x):.{precision}f}%")
    df["cnt_pct_bar_only"] = (df["value"] / bar_totals * 100).apply(lambda x: f"{(x):.{precision}f}%")

    # * format output
    df["cnt_str"] = df["value"].apply(lambda x: f"{x:_.{precision}f}")

    divider2 = "<br>" if orientation == "v" else " "

    # Modify this section
    df["cnt_pct_all_str"] = df.apply(
        lambda row: f"{row['cnt_str']}{divider2}({row['cnt_pct_all_only']})"
        if (row["value"] / n * 100) >= 5
        else row["cnt_str"],
        axis=1,
    )
    df["cnt_pct_bar_str"] = df.apply(
        lambda row: f"{row['cnt_str']}{divider2}({row['cnt_pct_bar_only']})"
        if (row["value"] / bar_totals.loc[row.name] * 100) >= 5
        else row["cnt_str"],
        axis=1,
    )

    text_to_show = "cnt_str"
    if show_pct_all:
        text_to_show = "cnt_pct_all_str"
    elif show_pct_bar:
        text_to_show = "cnt_pct_bar_str"

    if sort_values_color:
        colors_unique = df.groupby("col", observed=True)["value"].sum().sort_values(ascending=False).index.tolist()
    else:
        colors_unique = sorted(df["col"].unique().tolist())

    if sort_values_index:
        index_unique = df.groupby("index", observed=True)["value"].sum().sort_values(ascending=False).index.tolist()
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
    bar_max = df.groupby("index", observed=True)["value"].sum().sort_values(ascending=False).iloc[0] * BAR_LENGTH_MULTIPLIER
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
