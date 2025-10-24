import os
from pathlib import Path
from typing import Literal

import pandas as pd
import seaborn as sb
from matplotlib import pyplot as plt

from ..hlp import *
from ..tbl import print_summary
from ..helper import set_caption


def plot_boxes_large(
    df: pd.DataFrame,
    caption: str = None,
    points: Literal["all", "outliers", "suspectedoutliers", None] = None,
    precision: int = 2,
    height: int = 600,
    width: int = 1200,
    summary: bool = True,
    title: str = None,
    violin: bool = False,
    use_log: bool = False,
    box_width: float = 0.5,
    png_path: Path | str = None,
) -> None:
    """
    Plots vertical box plots for each unique item in the DataFrame using Seaborn/Matplotlib.
    Use it for large datasets.

    Args:
        df (pd.DataFrame): The input DataFrame with two columns: [0] str or bool (category),
                            and [1] numeric (value).
        caption (str): The caption for the plot.
        points (Literal["all", "outliers", "suspectedoutliers", None]): Controls the visibility of fliers (outliers).
                        'all' or 'outliers' shows fliers. None hides them.
        precision (int): The precision for rounding the statistics.
        height (int): The height of the plot figure in pixels.
        width (int): The height of the plot figure in pixels.
        summary (bool): Whether to add a summary to the plot.
        title (str): The specific title to use for the plot.
        use_log (bool): Whether to use logarithmic scale for the plot (cannot show negative values).
        violin (bool): If True, generates a violin plot instead of a box plot.
        box_width (float): The relative width of the boxes (0 to 1).
        png_path (Path | str, optional): The path to save the image as a png file. Defaults to None.

    Returns: None
    """

    if (
        len(df.columns) != 2
        or not ((pd.api.types.is_object_dtype(df.iloc[:, 0])) or (pd.api.types.is_bool_dtype(df.iloc[:, 0])))
        or not pd.api.types.is_numeric_dtype(df.iloc[:, 1])
    ):
        print("❌ df must have 2 columns: [0] str or bool, [1] num")
        return

    # * Set theme and figure size
    if os.getenv("THEME") == "dark":
        plt.style.use("dark_background")
    else:
        plt.style.use("default")

    scale_factor = 100
    plt.figure(figsize=(width / scale_factor, height / scale_factor))

    # * Prepare DataFrame for Seaborn
    col_cat, col_num = df.columns[0], df.columns[1]

    # * type of col0 must be str, not object
    if pd.api.types.is_object_dtype(df.iloc[:, 0]):
        df.loc[:, col_cat] = df[col_cat].astype(str)

    # * unique items (needed for title and potential ordering)
    # items = sorted(df[col_cat].unique())

    # * Sort by category
    df=df.sort_values(col_cat)

    # * Title and Labels
    caption = set_caption(caption)
    log_str = " (log-scale)" if use_log else ""
    plot_title = f"{caption}[{col_cat}] by [{col_num}]{log_str}, n={len(df):_.0f}" if not title else title

    # * Determine flier/outlier display
    showfliers = True
    flier_size = 5
    if points == "outliers" or points == "all":
        showfliers = True
    elif points is None or points == "suspectedoutliers":
        # Plotly's 'suspectedoutliers' is not directly translatable, treat as None (hide fliers)
        if points == "suspectedoutliers":
            showfliers = False

    # * Main Plotting with Seaborn - Use Boxplot or Violinplot
    if violin:
        sb.violinplot(
            data=df,
            x=col_cat,
            y=col_num,
            hue=col_cat,
            palette="tab10",
            width=box_width,
            inner="box" if not use_log else None,  # inner="box" is standard for violin
            ax=plt.gca(),
        )
    else:
        sb.boxplot(
            data=df,
            x=col_cat,
            y=col_num,
            hue=col_cat,
            palette="tab10",
            width=box_width,
            showfliers=showfliers,
            flierprops={"markerfacecolor": "white", "markersize": flier_size} if showfliers else {},
            ax=plt.gca(),
        )

    # * Apply log scale and title
    ax = plt.gca()
    if use_log:
        ax.set_yscale("log")  # Vertical plot means log scale is applied to y-axis

    ax.set_title(plot_title)

    # * Display the plot
    plt.tight_layout()
    plt.show()

    if summary:
        # * sort df by first column before printing summary
        # * print all data
        print_summary(df=df.sort_values(col_cat), precision=precision,sparse=False,)

        # * print values
        print_summary(df=df.sort_values(col_cat), precision=precision,sparse=True,)

    # * save to png if path is provided
    if png_path is not None:
        plt.savefig(Path(png_path).as_posix(), format="png", transparent=False)

    plt.close()
    plt.style.use("default")  # Reset style

    return
