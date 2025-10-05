import os
from pathlib import Path
from typing import Literal

import pandas as pd
import plotly.express as px

from ..hlp import *
from ..tbl import print_summary
from ..helper import set_caption

def plot_boxes(
    df: pd.DataFrame,
    caption: str = None,
    points: Literal["all", "outliers", "suspectedoutliers", None] = None,
    precision: int = 2,
    height: int = 600,
    width: int = 1200,
    annotations: bool = False,
    summary: bool = True,
    title: str = None,
    use_log: bool = False,
    box_width: float = 0.5,
    png_path: Path | str = None,
    renderer: Literal["png", "svg", None] = None,
) -> None:
    """
    [Experimental] Plot vertical boxes for each unique item in the DataFrame and add annotations for statistics.

    ⚠️ ⚠️ DEPRECATION WARNING: on large dataframes, this diagram will be EXTREMELY bloated. use the `_large` version!


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
        or not ((pd.api.types.is_object_dtype(df.iloc[:, 0])) or (pd.api.types.is_bool_dtype(df.iloc[:, 0])))
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

    caption = set_caption(caption)
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
        title=(f"{caption}[{df.columns[0]}] by [{df.columns[1]}]{log_str}, n={len(df):_.0f}" if not title else title),
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
    fig.update_layout(boxmode="group")  # Ensures boxes are not too compressed
    fig.update_layout(showlegend=False)
    fig.update_traces(marker=dict(size=5), width=box_width)  # Adjust width (default ~0.5)

    fig.show(renderer=renderer or os.getenv("RENDERER"), width=width, height=height)
    if summary:
        # * sort df by first column before printing summary
        # * print all data
        print_summary(df=df.sort_values(df.columns[0]), precision=precision,sparse=False,)

        # * print values
        print_summary(df=df.sort_values(df.columns[0]), precision=precision,sparse=True,)

    # * save to png if path is provided
    if png_path is not None:
        fig.write_image(Path(png_path).as_posix())

    return
