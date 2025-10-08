import os
from pathlib import Path
import pandas as pd
from ..hlp import *
from ..helper import set_caption
import matplotlib.pyplot as plt
import os
from pathlib import Path


def plot_pie(
    data: pd.Series | pd.DataFrame,
    caption: str = None,
    width: int = 800,
    height: int = 500,
    donut_size=0,
    precision: int=1,
    png_path: Path | str = None,
) -> None:
    """
    Creates and displays a pie or donut chart using Matplotlib.

    Args:
        data (pd.Series or pd.DataFrame): The data to plot.
            If a DataFrame, it must have only one column. The index will be
            used for labels and the values for the pie slice sizes.
        caption (str): The caption for the plot.
        height (int, optional): The height of the plot in pixels.
        width (int, optional): The width of the plot in pixels.
        donut_size (float, optional): A value between 0 and 1 to create a donut chart.
            A value of 0 results in a regular pie chart. Defaults to 0.
        png_path (Path | str, optional): The path to save the image as a png file. Defaults to None.
    """
    
    # * 1. Check for correct data type first
    if not isinstance(data, (pd.Series, pd.DataFrame)):
        print("Error: Data must be a pandas Series or DataFrame.")
        return

    # * 2. **CONVERT SERIES TO DATAFRAME**
    if isinstance(data, pd.Series):
        # * Get the name of the Series
        label = data.name if data.name else "Category"
        # * Convert the Series to a DataFrame with a column named 'values'
        data = data.to_frame(name="values")
    else:
        # * Get the name of the first column
        label = data.columns[0]

    # * 3. Ensure the DataFrame has only one column
    if len(data.columns) != 1:
        print("Error: DataFrame must have exactly one column for this function.")
        return

    # * take 1st (only) column and use value counts to get distribution
    # This Series contains the values and the index contains the labels
    data_counts = data.iloc[:, 0].value_counts()
    
    # * Get the number of observations (before grouping)
    n = data.shape[0]

    # --- Matplotlib/Seaborn Setup ---
    
    # * Set dark theme based on environment (NOTE: Matplotlib applies style globally)
    if os.getenv("THEME") == "dark":
        plt.style.use('dark_background')
    else:
        plt.style.use('default')

    # * Set figure size (Matplotlib size is in inches, so scale pixels/DPI)
    DPI = 100
    plt.figure(figsize=(width / DPI, height / DPI))
    
    # * Determine the wedge properties for donut chart
    wedge_properties = {}
    if 0 < donut_size < 1:
        wedge_properties = dict(width=1.0 - donut_size, edgecolor='w')
    
    # * Apply Title
    plot_title = f"{set_caption(caption)}{label}, n={n:_}"
    plt.title(plot_title)

    # * 4. Create the pie chart using Matplotlib
    plt.pie(
        x=data_counts.values,
        labels=data_counts.index,
        autopct=f'%1.{precision}f%%', # Format for displaying percentages
        startangle=90,     # Start at the top
        wedgeprops=wedge_properties, # Creates the donut/hole effect
        # Matplotlib's default color cycle (tab10) is similar to Plotly's default
    )
    
    # * Ensure the plot is circular
    plt.axis('equal') 
    
    # * Display the plot
    plt.tight_layout()
    plt.show()

    # * 5. Save and Cleanup
    if png_path is not None:
        # Use Path for robust file saving
        plt.savefig(Path(png_path).as_posix(), format='png', transparent=False)

    plt.close()
    plt.style.use('default') # Reset style
