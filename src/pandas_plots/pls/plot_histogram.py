import os
from pathlib import Path
from typing import Literal

import pandas as pd
import plotly.express as px

from ..hlp import *
from ..tbl import print_summary
from ..helper import set_caption

def plot_histogram(
    df_ser: pd.DataFrame | pd.Series,
    histnorm: Literal["probability", "probability density", "density", "percent", None] = None,
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

    ⚠️ on large dataframes, this diagram will be EXTREMELY bloated. use the `_large` version!

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
    df = df.map(lambda x: round(x, precision))

    _caption = set_caption(caption)

    # * nbins defaults to number of unique values
    if nbins == -1:
        # Calling int on a single element Series is deprecated and will raise a TypeError in the future. Use int(ser.iloc[0]) instead
        nbins = int(df.iloc[0].max() - df.iloc[0].min())

    # ! plot
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
        print_summary(df)

    return
