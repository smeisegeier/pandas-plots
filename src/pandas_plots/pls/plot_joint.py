import os
from pathlib import Path
from typing import Literal

import pandas as pd
import seaborn as sb
from matplotlib import pyplot as plt

from ..hlp import *


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
        # "title": f"{caption}[{ser.name}], n={len(ser):_}" if not title else title,
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
    fig.figure.suptitle(title or f"{_caption}[{df.columns[0]}] vs [{df.columns[1]}], n={len(df):_}")
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
