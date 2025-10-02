import os
from pathlib import Path
from typing import Literal

import pandas as pd
import seaborn as sb
from matplotlib import pyplot as plt

from ..hlp import *
from ..tbl import print_summary
from ..helper import set_caption


def plot_box_large(
    ser: pd.Series,
    points: Literal["all", "outliers", "suspectedoutliers", None] = None,
    precision: int = 2,
    height: int = 200,
    width: int = 1200,
    annotations: bool = False,
    summary: bool = True,
    caption: str = None,
    title: str = None,
    violin: bool = False,
    x_min: float = None,
    x_max: float = None,
    use_log: bool = False,
    png_path: Path | str = None,
) -> None:
    """
    Plots a horizontal box or violin plot for a pandas Series.

    This function is designed to handle large datasets efficiently by rendering a
    static image instead of a large interactive plot structure.

    Args:
        ser: The pandas Series containing the data to plot.
        points: Controls outlier visibility. 'all' or 'outliers' shows fliers;
                None or 'suspectedoutliers' hides them (Plotly's distinct types
                are not fully supported by Seaborn's static output).
        precision: The decimal precision for the annotation labels.
        height: The height of the plot figure in pixels (scaled to Matplotlib inches).
        width: The width of the plot figure in pixels (scaled to Matplotlib inches).
        annotations: If True, adds calculated statistical values (min, max, quartiles,
                    mean, fences) as text and arrows onto the plot.
        summary: If True, prints a statistical summary table below the plot.
        caption: A custom prefix added to the default plot title.
        title: The specific title to use for the plot (overrides the default generated title).
        violin: If True, generates a violin plot with an inner boxplot; otherwise,
                generates a standard boxplot.
        x_min: The minimum value for the x-axis scale.
        x_max: The maximum value for the x-axis scale.
        use_log: If True, uses a logarithmic scale for the x-axis.
        png_path (Path | str, optional): The file path to save the generated image.
                                        The plot will be saved in PNG format.
        renderer (Literal["png", "svg", None], optional): This argument is maintained
                for compatibility but is **ignored** as Seaborn/Matplotlib uses
                `plt.show()` for display.

    Returns:
        None
    """
    ser = to_series(ser)
    if ser is None:
        return

    # * drop na to keep scipy sane
    n_ = len(ser)
    ser.dropna(inplace=True)

    # ----------------------------------------------------
    # --- Data and Layout Setup ---
    # ----------------------------------------------------

    # * apply theme early
    if os.getenv("THEME") == "dark":
        plt.style.use("dark_background")
    else:
        plt.style.use("default")

    # Seaborn/Matplotlib setup for size
    # figsize takes (width, height) in inches, so we scale by a factor (e.g., 100 DPI)
    scale_factor = 100
    plt.figure(figsize=(width / scale_factor, height / scale_factor))

    # Create a dummy DataFrame suitable for Seaborn's y/x mapping for a single Series
    # We use 'value' for the numeric data and a constant 'category' for the y-axis
    df_plot = pd.DataFrame({"value": ser.values, "category": ser.name or "Series"})

    caption = set_caption(caption)
    log_str = " (log-scale)" if use_log else ""
    plot_title = f"{caption}[{ser.name}]{log_str}, n={n_:_}" if not title else title

    # ----------------------------------------------------
    # --- Seaborn Plotting ---
    # ----------------------------------------------------

    if violin:
        # Use violinplot
        ax = sb.violinplot(
            data=df_plot,
            x="value",
            y="category",
            orient="h",
            cut=0,  # Seaborn argument to control how far the plot extends past whiskers
            inner="box",  # Show a mini boxplot inside the violin
        )
    else:
        # Use boxplot
        # The 'points' argument is partially supported via 'fliersize' and 'showfliers'

        # Determine flier/outlier display
        showfliers = True
        flier_size = 5  # Default size
        if points == "outliers" or points == "all":
            showfliers = True
        elif points is None or points == "suspectedoutliers":
            # Note: Seaborn/Matplotlib doesn't distinguish between 'outliers' and 'suspected' like Plotly
            # 'suspectedoutliers' is not directly translatable, so we'll treat it as 'None' (no fliers)
            if points == "suspectedoutliers":
                showfliers = False

        ax = sb.boxplot(
            data=df_plot,
            x="value",
            y="category",
            orient="h",
            palette="tab10",
            showfliers=showfliers,
            flierprops={"markerfacecolor": "red", "markersize": flier_size} if showfliers else {},
        )

    # Apply axis limits and scale
    if use_log:
        ax.set_xscale("log")
        # use_log: bool = False, # Handled above with ax.set_xscale

    if (x_min is not None) and (x_max is not None):
        ax.set_xlim(x_min, x_max)
        # x_min: float = None, # Handled above with ax.set_xlim
        # x_max: float = None, # Handled above with ax.set_xlim

    ax.set_title(plot_title)
    ax.set_ylabel("")  # Remove the category label on the y-axis

    # ----------------------------------------------------
    # --- Annotations and Summary ---
    # ----------------------------------------------------

    # Recalculate stats for annotations
    median = ser.median()
    mean = ser.mean()
    q25 = ser.quantile(0.25)
    q75 = ser.quantile(0.75)
    min_val = ser.min()
    max_val = ser.max()
    iqr = q75 - q25

    # Calculate fences (Matplotlib standard)
    fence0_ = q25 - 1.5 * iqr
    fence0 = fence0_ if fence0_ > min_val else min_val
    fence1_ = q75 + 1.5 * iqr
    fence1 = fence1_ if fence1_ < max_val else max_val

    # Note: Annotations in Matplotlib are tedious and highly dependent on figure size.
    # The Plotly yshift logic (lvl1, lvl2, lvl3) is not easily portable.
    # We use a simple constant y position (0.5 for the single series) and a vertical offset.

    if annotations:
        y_pos = 0.5  # Center of the single boxplot on the y-axis
        v_offset = 0.05  # Vertical distance for labels

        # Simplified annotation loop to place labels above/below the plot
        labels = [
            (min_val, f"min: {min_val:.{precision}f}", v_offset),
            (fence0, f"lower: {fence0:.{precision}f}", v_offset * 2),
            (q25, f"q25: {q25:.{precision}f}", v_offset),
            (median, f"median: {median:.{precision}f}", -v_offset * 2),
            (mean, f"mean: {mean:.{precision}f}", v_offset * 3),
            (q75, f"q75: {q75:.{precision}f}", -v_offset),
            (fence1, f"upper: {fence1:.{precision}f}", v_offset),
            (max_val, f"max: {max_val:.{precision}f}", -v_offset * 3),
        ]

        for x, text, offset in labels:
            ax.annotate(
                text,
                xy=(x, y_pos),
                xytext=(x, y_pos + offset),
                ha="center",
                arrowprops=dict(facecolor="black", arrowstyle="->", connectionstyle="arc3,rad=0.0"),
                fontsize=8,
            )

    # height: int = 200, # Handled by plt.figure(figsize=...)
    # width: int = 1200, # Handled by plt.figure(figsize=...)
    # caption: str = None, # Handled in title
    # renderer: Literal["png", "svg", None] = None, # NOT SUPPORTED/COMMENTED OUT

    # Display the plot
    plt.tight_layout()
    plt.show()

    if summary:
        print_summary(ser.to_frame())

    # * save to png if path is provided
    if png_path is not None:
        plt.savefig(Path(png_path).as_posix(), format="png")

    # Clear the figure to prevent display issues if multiple plots are run
    plt.close()
    plt.style.use("default")
    return


# Example usage (assuming _set_caption etc. are available)
# df = pd.DataFrame({'DataPoints': np.random.lognormal(size=1000)})
# plot_box(df['DataPoints'], annotations=True, use_log=True, height=300, width=800, png_path='test_seaborn_box.png')
