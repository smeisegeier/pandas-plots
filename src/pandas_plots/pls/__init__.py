"""
pandas-plots pls module.

This module contains all the plotting functions previously in the single pls.py file.
"""

from .plot_bars import plot_bars
from .plot_box import plot_box
from .plot_box_large import plot_box_large
from .plot_boxes import plot_boxes
from .plot_boxes_large import plot_boxes_large
from .plot_facet_stacked_bars import plot_facet_stacked_bars
from .plot_histogram import plot_histogram
from .plot_histogram_large import plot_histogram_large
from .plot_joint import plot_joint
from .plot_pie import plot_pie
from .plot_quadrants import plot_quadrants
from .plot_sankey import plot_sankey
from .plot_stacked_bars import plot_stacked_bars

# Re-export all functions to maintain the same interface
__all__ = [
    "plot_quadrants",
    "plot_stacked_bars",
    "plot_bars",
    "plot_histogram",
    "plot_histogram_large",
    "plot_joint",
    "plot_box",
    "plot_box_large",
    "plot_boxes",
    "plot_boxes_large",
    "plot_facet_stacked_bars",
    "plot_sankey",
    "plot_pie",
]

# Add methods to pandas DataFrame to enable chaining
import pandas as pd

pd.DataFrame.plot_bars = plot_bars
pd.DataFrame.plot_stacked_bars = plot_stacked_bars
pd.DataFrame.plot_facet_stacked_bars = plot_facet_stacked_bars
pd.DataFrame.plot_stacked_box = plot_box
pd.DataFrame.plot_stacked_boxes = plot_boxes
pd.DataFrame.plot_quadrants = plot_quadrants
pd.DataFrame.plot_histogram = plot_histogram
pd.DataFrame.plot_joint = plot_joint
pd.DataFrame.plot_sankey = plot_sankey
pd.DataFrame.plot_pie = plot_pie
