import os
from pathlib import Path
from typing import Literal

import pandas as pd
import plotly.express as px

from pandas_plots import const

from ..helper import _add_alt_text, _assign_column_colors, _set_caption
from ..hlp import *
from ..tbl import print_summary


def plot_boxes(
    df: pd.DataFrame,
    caption: str = None,
    caption_only_n: bool = False,
    points: Literal["all", "outliers", "suspectedoutliers", None] = None,
    precision: int = 2,
    height: int = 600,
    width: int = 1600,
    annotations: bool = False,
    facet_col: str = None,
    summary: bool = True,
    title: str = None,
    use_log: bool = False,
    box_width: float = 0.5,
    png_path: Path | str = None,
    renderer: Literal["png", "svg", None] = None,
    color_palette: str | list[str] = const.PALETTE_RKI1,
    null_label: str = "(NA)",
    first_col_grey: bool = False,
    alt_text: str = None,
) -> None:
    """
    Plot vertical boxes for each unique item in the DataFrame and add annotations for statistics.

    ⚠️: on large dataframes, this diagram will be EXTREMELY bloated. use the `_large` version!

    if facet_col is not None, the plot will be faceted by facet_col. facet_col must be last column

    Args:
        df (pd.DataFrame): The input DataFrame with two columns, where the first column is string or bool type and the second column is numeric.
        caption (str): The caption for the plot.
        caption_only_n (bool): Whether to show only n in the caption.
        points (Literal["all", "outliers", "suspectedoutliers", None]): The points to be plotted.
        precision (int): The precision for rounding the statistics.
        height (int): The height of the plot.
        width (int): The width of the plot.
        annotations (bool): Whether to add annotations to the plot.
        facet_col (str): The column to facet the plot by.
        summary (bool): Whether to add a summary to the plot.
        use_log (bool): Whether to use logarithmic scale for the plot (cannot show negative values).
        box_width (float): The relative width of the boxes (0 to 1). Default is 0.5.
        png_path (Path | str, optional): The path to save the image as a png file. Defaults to None.
        renderer (Literal["png", "svg", None], optional): The renderer to use for saving the image. Defaults to None.
        color_palette (str | list[str]): Name of the color palette to use, or a list of colors.
            - Default: `const.PALETTE_RKI1`
            - 🎨 Plotly names: `D3`, `Pastel`, `Dark24`, `Light24`, `Plotly`
            - Example: `const.PALETTE_RKI1`, `const.PALETTE_RKI2`
        null_label (str): Label for null values.
        first_col_grey (bool): If True, sets the first category to grey.
        alt_text (str, optional): Custom alt text for accessibility. Defaults to title or caption if not provided.

    Returns: None
    """

    if (
        len(df.columns) not in (2, 3)
        or not ((pd.api.types.is_object_dtype(df.iloc[:, 0])) or (pd.api.types.is_bool_dtype(df.iloc[:, 0])))
        or not pd.api.types.is_numeric_dtype(df.iloc[:, 1])
    ):
        print("❌ df must have 2 or 3 columns: [0] str or bool, [1] num, [2] (optional) str")
        return
    # * layout gaps
    xlvl1 = -50
    xlvl2 = 0
    xlvl3 = 50

    col_cat = df.columns[0]
    col_num = df.columns[1]

    # * handle null values FIRST before any type conversion
    df[col_cat] = df[col_cat].fillna(null_label)
    # Also replace pd.NA and string "nan" / "<NA>" that may result from conversion
    df[col_cat] = df[col_cat].replace([pd.NA, "nan", "<NA>"], null_label)

    # * type of col0 must be str, not object. otherwise px.box will fail since sorting will fail
    if pd.api.types.is_object_dtype(df.iloc[:, 0]):
        df.iloc[:, 0] = df.iloc[:, 0].astype(str)

    # * unique items
    # Sort the unique items alphabetically
    items = sorted(df[col_cat].unique())

    # * assign colors
    color_map = _assign_column_colors(items, color_palette, null_label, first_col_grey)

    log_str = " (log-scale)" if use_log else ""
    n_str = f"n={len(df):_.0f}"
    if caption_only_n:
        plot_title = n_str
    elif title:
        plot_title = f"{title}, {n_str}"
    else:
        plot_title = f"{_set_caption(caption)} [{df.columns[0]}] by [{df.columns[1]}]{log_str}, {n_str}"

    # * main plot
    fig = px.box(
        df,
        x=df.iloc[:, 0],
        y=df.iloc[:, 1],
        color=df.iloc[:, 0],
        facet_col=facet_col,
        template="plotly_dark" if os.getenv("THEME") == "dark" else "plotly",
        orientation="v",
        points=points,
        log_y=use_log,
        color_discrete_map=color_map,
        title=plot_title,
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
            fig.add_annotation(x=i, y=min, text=f"min: {min}", yshift=YS, showarrow=True, xshift=xlvl1)
            fig.add_annotation(
                x=i,
                y=fence0,
                text=f"lower: {fence0}",
                yshift=YS,
                showarrow=True,
                xshift=xlvl3,
            )
            fig.add_annotation(x=i, y=q25, text=f"q25: {q25}", yshift=YS, showarrow=True, xshift=xlvl2)
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
            fig.add_annotation(x=i, y=q75, text=f"q75: {q75}", yshift=YS, showarrow=True, xshift=xlvl2)
            fig.add_annotation(
                x=i,
                y=fence1,
                text=f"upper: {fence1}",
                yshift=YS,
                showarrow=True,
                xshift=xlvl3,
            )
            fig.add_annotation(x=i, y=max, text=f"max: {max}", yshift=YS, showarrow=True, xshift=xlvl1)

    fig.update_xaxes(title_text=df.columns[0])
    fig.update_yaxes(title_text=df.columns[1])
    fig.update_layout(boxmode="group", height=height, width=width)  # Ensures boxes are not too compressed
    fig.update_layout(showlegend=False)
    fig.update_traces(marker=dict(size=5), width=box_width)  # Adjust width (default ~0.5)

    alt_text = alt_text or title or caption
    _add_alt_text(alt_text)
    fig.show(renderer=renderer or os.getenv("RENDERER"), width=width, height=height)
    if summary:
        # * sort df by first column before printing summary
        # * print all data
        print_summary(
            df=df.sort_values(df.columns[0]),
            precision=precision,
            sparse=False,
        )

        # * print values
        print_summary(
            df=df.sort_values(df.columns[0]),
            precision=precision,
            sparse=True,
        )

    # * save to png if path is provided
    if png_path is not None:
        fig.write_image(Path(png_path).as_posix())

    return
