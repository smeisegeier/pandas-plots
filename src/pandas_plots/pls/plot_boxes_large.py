import os
from pathlib import Path
from typing import Literal

import pandas as pd
import seaborn as sb
from matplotlib import pyplot as plt

from pandas_plots import const

from ..helper import _add_alt_text, _assign_column_colors, _set_caption
from ..hlp import *
from ..tbl import print_summary


def plot_boxes_large(
    df: pd.DataFrame,
    caption: str = None,
    caption_only_n: bool = False,
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
    color_palette: str | list[str] = const.PALETTE_RKI1,
    null_label: str = "(NA)",
    first_col_grey: bool = False,
    alt_text: str = None,
) -> None:
    """
    Plots vertical box plots for each unique item in the DataFrame using Seaborn/Matplotlib.
    Use it for large datasets.

    Args:
        df (pd.DataFrame): The input DataFrame with two columns: [0] str or bool (category),
                            and [1] numeric (value).
        caption (str): The caption for the plot.
        caption_only_n (bool): Whether to show only n in the caption.
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

    if os.getenv("PDF") == "1":
        summary = False

    scale_factor = 100
    plt.figure(figsize=(width / scale_factor, height / scale_factor))

    # * Prepare DataFrame for Seaborn
    col_cat, col_num = df.columns[0], df.columns[1]

    # * handle null values FIRST before any type conversion
    df[col_cat] = df[col_cat].fillna(null_label)
    # Also replace pd.NA and string "nan" / "<NA>" that may result from conversion
    df[col_cat] = df[col_cat].replace([pd.NA, "nan", "<NA>"], null_label)

    # * type of col0 must be str, not object
    if pd.api.types.is_object_dtype(df.iloc[:, 0]):
        df.loc[:, col_cat] = df[col_cat].astype(str)

    # * unique items (needed for title and potential ordering)
    # items = sorted(df[col_cat].unique())

    # * Sort by category
    df = df.sort_values(col_cat)

    # * assign colors
    colors_unique = df[col_cat].unique().tolist()
    color_map = _assign_column_colors(colors_unique, color_palette, null_label, first_col_grey)
    # convert dict to list in the order of colors_unique
    color_list = [color_map[cat] for cat in colors_unique]

    # * Title and Labels
    log_str = " (log-scale)" if use_log else ""
    n_str = f"n={len(df):_.0f}"
    if caption_only_n:
        plot_title = n_str
    elif title:
        plot_title = f"{title}, {n_str}"
    else:
        plot_title = f"{_set_caption(caption)} [{col_cat}] by [{col_num}]{log_str}, {n_str}"

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
            palette=color_list,
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
            palette=color_list,
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
    alt_text = alt_text or title or caption
    _add_alt_text(alt_text)
    plt.show()

    if summary:
        # * sort df by first column before printing summary
        # * print all data
        print_summary(
            df=df.sort_values(col_cat),
            precision=precision,
            sparse=False,
        )

        # * print values
        print_summary(
            df=df.sort_values(col_cat),
            precision=precision,
            sparse=True,
        )

    # * save to png if path is provided
    if png_path is not None:
        plt.savefig(Path(png_path).as_posix(), format="png", transparent=False)

    plt.close()
    plt.style.use("default")  # Reset style

    return
