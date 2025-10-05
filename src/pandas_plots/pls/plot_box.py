import os
from pathlib import Path
from typing import Literal

import pandas as pd
import plotly.express as px

from ..hlp import *
from ..tbl import print_summary
from ..helper import set_caption


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

    ⚠️ DEPRECATION WARNING: on large dataframes, this diagram will be EXTREMELY bloated. use the `_large` version!

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

    caption = set_caption(caption)
    log_str = " (log-scale)" if use_log else ""
    dict = {
        "data_frame": ser,
        "orientation": "h",
        "template": "plotly_dark" if os.getenv("THEME") == "dark" else "plotly",
        "points": points,
        # 'box':True,
        "log_x": use_log,  # * logarithmic scale, axis is always x
        # "notched": True,
        "title": f"{caption}[{ser.name}]{log_str}, n={n_:_}" if not title else title,
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
    #     title=f"{caption}[{ser.name}], n={len(ser):_}" if not title else title,
    #     )
    if annotations:
        fig.add_annotation(
            x=min,
            text=f"min: {round(min, precision)}",
            showarrow=True,
            yshift=lvl1,
            y=-0,
        )
        fig.add_annotation(
            x=fence0,
            text=f"lower: {round(fence0, precision)}",
            showarrow=True,
            yshift=lvl3,
            y=-0,
        )
        fig.add_annotation(
            x=q25,
            text=f"q25: {round(q25, precision)}",
            showarrow=True,
            yshift=lvl2,
            y=-0,
        )
        fig.add_annotation(
            x=median,
            text=f"median: {round(median, precision)}",
            showarrow=True,
            yshift=lvl1,
            y=-0,
        )
        fig.add_annotation(
            x=mean,
            text=f"mean: {round(mean, precision)}",
            showarrow=True,
            yshift=lvl3,
            y=-0,
        )
        fig.add_annotation(
            x=q75,
            text=f"q75: {round(q75, precision)}",
            showarrow=True,
            yshift=lvl2,
            y=-0,
        )
        fig.add_annotation(
            x=fence1,
            text=f"upper: {round(fence1, precision)}",
            showarrow=True,
            yshift=lvl1,
            y=-0,
        )
        fig.add_annotation(
            x=max,
            text=f"max: {round(max, precision)}",
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
