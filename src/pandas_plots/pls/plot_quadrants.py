import os
import pandas as pd
from pathlib import Path
from matplotlib import pyplot as plt
import seaborn as sb

def plot_quadrants(
    df: pd.DataFrame,
    title: str = None,
    caption: str = None,
    png_path: Path | str = None,
) -> object:
    """
    Plot a heatmap for the given dataframe, with options for title and caption.

    Args:
        df (pd.DataFrame): The input dataframe with 2 or 3 columns.
            df must have 3 columns, first 2 must be present
                index axis
                columns axis
                values (can be derived as cnt=1)
            df columns must contain 2 values
        title (str, optional): The title for the heatmap to override the default.
        caption (str, optional): The caption for the heatmap. Defaults to None.
        png_path (Path | str, optional): The path to save the image as a png file. Defaults to None.

    Returns:
        q1, q2, q3, q4, n: The values for each quadrant and the total count.
    """
    if len(df.columns) < 2 or len(df.columns) > 3:
        print("❌ df must have 2 or 3 columns")
        return

    if len(df.iloc[:, 0].unique()) != 2 or len(df.iloc[:, 0].unique()) != 2:
        print("❌ both columns must have 2 values")
        return

    if len(df.columns) == 2:
        df["cnt"] = 1

    heat = (
        df.groupby(
            by=[df.columns[0], df.columns[1]],
            as_index=True,  # * use index to keep track of all columns
        )[df.columns[2]]
        .sum()
        .reset_index()  # * then reset index to get a dataframe with all columns
    )
    # * create pivot table in wide format for heatmap
    heat_wide = heat.pivot(
        index=df.columns[0],
        columns=df.columns[1],
        values=df.columns[2],
    )

    # * derive label for heatmap
    n = heat_wide.sum().sum()
    heat_label = heat_wide.map(lambda x: f"{x:_}\n({x/n*100:.1f}%)")

    # * seaborn. use less fancy stuff :)
    caption = f"#{caption.lower()}, " if caption else "heatmap, "

    # * plot
    theme = "dark_background" if os.getenv("THEME") == "dark" else "ggplot"

    plt.style.use(theme)
    _ = sb.heatmap(
        # data=_heat_wide,
        data=heat_wide.map(lambda x: x / n),
        annot=heat_label,
        fmt="",
        cmap="BuPu",
        vmin=0,  # * to have relative values in colorbar
        vmax=1,
    ).set_title(f"{caption}n = {n:_.0f}" if not title else title)

    # * dont output na values
    heat_wide_out = heat_wide.fillna(0)
    q1 = heat_wide_out.iloc[1, 1]
    q2 = heat_wide_out.iloc[1, 0]
    q3 = heat_wide_out.iloc[0, 0]
    q4 = heat_wide_out.iloc[0, 1]

    # * save to png if path is provided
    if png_path is not None:
        plt.savefig(Path(png_path).as_posix(), format="png")

    return q1, q2, q3, q4, n
    # * plotly express is not used for the heatmap, although it does not need the derived wide format.
    # * but theres no option to alter inner values in the heatmap
