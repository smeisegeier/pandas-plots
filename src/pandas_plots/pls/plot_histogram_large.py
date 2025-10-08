import os
from pathlib import Path

import pandas as pd
import seaborn as sb
from matplotlib import pyplot as plt

from ..hlp import *
from ..tbl import print_summary
from ..helper import set_caption


def plot_histogram_large(
    df_ser: pd.DataFrame | pd.Series,
    nbins: int = -1,
    precision: int = 2,
    height: int = 500,
    width: int = 1600,
    caption: str = None,
    title: str = None,
    png_path: Path | str = None,
    summary: bool = False,
) -> None:
    """
    A function to plot a histogram based on a large number of *numeric* columns in a DataFrame
    using Seaborn's histplot for efficient static rendering.

    Accepts:
        - a numeric series
        - a dataframe with only numeric columns


    Parameters:
        df_ser (pd.DataFrame | pd.Series): The input containing the data to be plotted.
        nbins (int): The number of bins in the histogram. If set to -1, the number of bins
                     will be calculated based on the data span (Seaborn will use 'auto' by default
                     if no integer is provided, which is generally better).
        precision (int): The precision for rounding the data.
        height (int): The height of the plot.
        width (int): The height of the plot.
        caption (str): The caption for the plot.
        title (str): The title of the plot.
        png_path (Path | str, optional): The path to save the image as a png file.
        summary (bool): Whether to print a summary table of the data. # UPDATED: Docstring for summary

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

    # * Only plot the first numeric column if DataFrame has multiple
    data_series = df.iloc[:, 0]

    # * rounding (apply only to the plotting data if needed)
    data_series = data_series.apply(lambda x: round(x, precision))

    # --- Matplotlib/Seaborn Setup ---

    # * Set dark theme based on environment (assuming _set_caption exists)
    if os.getenv("THEME") == "dark":
        plt.style.use("dark_background")
    else:
        plt.style.use("default")

    # * Set figure size
    scale_factor = 100
    plt.figure(figsize=(width / scale_factor, height / scale_factor))

    # * Title and Labels
    _caption = set_caption(caption)
    title_str = title or f"{_caption}[{data_series.name or 'Value'}], n={data_series.shape[0]:_.0f}"

    # * Determine number of bins (Fixes TypeError: bins must be an integer, a string, or an array)
    bins_arg = nbins if nbins > 0 else "auto"

    # * Main Plotting with Seaborn histplot
    sb.histplot(
        x=data_series,
        bins=bins_arg,
        kde=True,  # Standard histogram
        color="skyblue",  # Set a default color
        edgecolor=".2",  # Dark edges for bars
        ax=plt.gca(),
    )

    # * Apply title and labels
    ax = plt.gca()
    ax.set_title(title_str)
    ax.set_xlabel(data_series.name or "Value")
    ax.set_ylabel("Count")

    # * Display the plot
    plt.tight_layout()
    plt.show()

    # * save to png if path is provided
    if png_path is not None:
        plt.savefig(Path(png_path).as_posix(), format="png", transparent=False)

    plt.close()
    plt.style.use("default")  # Reset style

    if summary:
        # Assuming print_summary is a helper function that accepts a DataFrame
        print_summary(df)

    return
