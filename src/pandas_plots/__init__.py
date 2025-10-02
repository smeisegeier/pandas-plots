"""
pandas-plots main module.

This module provides various plotting functions for pandas DataFrames.
"""

# Import modules to maintain backward compatibility
from . import pls
from . import hlp
from . import tbl
from . import ven

# Re-export the modules to maintain the original import structure
__all__ = ["pls", "hlp", "tbl", "ven"]

# Optionally, also make individual functions available at the top level for convenience
from .pls import (
    plot_quadrants,
    plot_stacked_bars,
    plot_bars,
    plot_histogram,
    plot_histogram_large,
    plot_joint,
    plot_box,
    plot_box_large,
    plot_boxes,
    plot_boxes_large,
    plot_facet_stacked_bars,
    plot_sankey,
    plot_pie,
)

# Add individual functions to __all__ as well if needed
__all__.extend([
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
])