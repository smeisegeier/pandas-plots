import warnings
from IPython.display import Markdown, display

import os
from collections import abc
from pathlib import Path
from typing import Literal, Optional, get_args

from ..hlp.group_kkr import group_kkr

import numpy as np
import dataframe_image as dfi

warnings.filterwarnings("ignore")

TOTAL_LITERAL = Literal[
    "sum", "mean", "median", "min", "max", "std", "var", "skew", "kurt"
]
KPI_LITERAL = Literal[
    "rag_abs", "rag_rel", "min_max_xy", "max_min_xy", "min_max_x", "max_min_x"
]

def show_num_df(
    df,
    total_mode: TOTAL_LITERAL = "sum",
    total_axis: Literal["x", "y", "xy", None] = "xy",
    total_exclude: bool = False,
    heatmap_axis: Literal["x", "y", "xy", None] = None,
    data_bar_axis: Literal["x", "y", "xy", None] = None,
    pct_axis: Literal["x", "xy", None] = None,
    swap: bool = False,
    precision: int = 0,
    kpi_rag_list: list[float] = None,
    kpi_mode: KPI_LITERAL = None,
    kpi_shape: Literal["squad", "circle"] = "squad",
    show_as_pct: bool = False,
    alter_font: bool = True,
    font_size_th: int = 0,
    font_size_td: int = 0,
    col1_width: int = 0,
    png_path: str | Path = None,
    png_conversion: Literal["chrome", "selenium"] = "selenium",
    kkr_col: Optional[str] = None,
    image_scale: str = None,
):
    """
    A function to display a DataFrame with various options for styling and formatting, including the ability to show totals, apply data bar coloring, and control the display precision.

    if unset, `font_size_th`, `font_size_td` are filled up by ENV variables in `setup_rendering`.  
    **⚠️ this is currently not active.**

    increasing `font_size_th` and `font_size_td` will also increase tables image size and visual sharpness.  
    too large tables will be cut off by the chromium engine, so stick to values around 12/11  
    `image_scale` is best declared as a percentage of the viewports width, e.g. "60%" (100% seems not to work)  
    
    Args:
    - df: the DataFrame to display
    - total_mode: a Literal indicating the mode for aggregating totals ["sum", "mean", "median", "min", "max", "std", "var", "skew", "kurt"]
    - total_axis (Literal["x", "y", "xy", None], optional): The axis for displaying totals. Defaults to "xy".
    - total_exclude (bool, optional): Whether to exclude totals from the coloring in heatmap and data bar. Defaults to False.
    - heatmap_axis (Literal["x","y","xy", None], optional): The axis for displaying heatmaps. Defaults to None.
    - data_bar_axis: a Literal indicating the axis for applying data bar coloring ["x","y","xy", None]
    - pct_axis: a Literal indicating the directions for displaying percentages ["x","xy", None]. "x" means sum up pct per column
    - swap: a boolean indicating whether to swap the axes
    - precision: an integer indicating the display precision
    - kpi_mode: a Literal indicating the mode for displaying KPIs ["rag_abs","rag_rel", "min_max_xy", "max_min_xy", "min_max_x", "max_min_x"]
        - rag_abs: rag lights (red amber green) based on tresholds given in kpi_rag_list
        - rag_rel: rag lights (red amber green) based on percentiles given in kpi_rag_list (0-1)
        - min_max_xy: min value green, max valued red for all axes
        - max_min_xy: max value green, min valued red for all axes
        - min_max_x: min value green, max valued red for x axis
        - max_min_x: max value green, min valued red for x axis
    - kpi_rag_list: a list of floats indicating the thresholds for rag lights. The list should have 2 elements.
    - kpi_shape: a Literal indicating the shape of the KPIs ["squad", "circle"]
    - show_as_pct: a boolean indicating whether to show value as percentage (only advised on values ~1)
    - alter_font: a boolean indicating whether to alter the font family
    - font_size_th: an integer indicating the font size for the header
    - font_size_td: an integer indicating the font size for the table data
    - col1_width: an integer indicating the width of the first column in px
    - png_path: a string or Path indicating the path to save the PNG file
    - png_conversion: a Literal indicating the conversion method for the PNG file ["chrome", "selenium"]
    - kkr_col: a string indicating the column name for KKR grouping
    - image_scale: a string indicating the scale of the image width for markdown. eg "800" or "60%" (->60% of viewport)

    Returns:
    The function returns a styled representation of the DataFrame.
    """
    # * ensure arguments match parameter definition
    if any([df[col].dtype.kind not in ["i", "u", "f"] for col in df.columns]) == True:
        print(
            f"❌ table must contain numeric data only. Maybe you forgot to convert this table with pivot or pivot_table first?"
        )
        return

    if (
        (pct_axis and pct_axis not in ["x", "xy"])
        or (data_bar_axis and data_bar_axis not in ["x", "y", "xy"])
        or (heatmap_axis and heatmap_axis not in ["x", "y", "xy"])
    ):
        print(f"❌ axis not supported")
        return

    if total_mode and total_mode not in get_args(TOTAL_LITERAL):
        print(f"❌ total_mode '{total_mode}' not supported")
        return

    if kpi_mode and kpi_mode not in get_args(KPI_LITERAL):
        print(f"❌ kpi_mode '{kpi_mode}' not supported")
        return

    if (kpi_mode and kpi_mode.startswith("rag")) and (
        not isinstance(kpi_rag_list, abc.Iterable) or len(kpi_rag_list) != 2
    ):
        print(f"❌ kpi_rag_list must be a list of 2 if kpi_mode is set")
        return

    if kpi_mode == "rag_rel":
        # * transform values into percentiles
        if all(i <= 1 and i >= 0 for i in kpi_rag_list):
            kpi_rag_list = [int(i * 100) for i in kpi_rag_list]
        else:
            print(f"❌ kpi_list for relative mode must be between 0 and 1")
            return

    theme = os.getenv("THEME") or "light"
    
    df = df.copy()

    if kkr_col:
        df = group_kkr(df=df, kkr_col=kkr_col)

    # * copy df, do not reference original
    df_ = df if not swap else df.T

    # * get minmax values before totals are added
    tbl_min = df_.min().min()
    tbl_max = df_.max().max()
    tbl_sum = df_.sum().sum()

    # * copy df before totals
    df_orig = df_.copy()

    # * add totals
    if total_mode and total_axis in ["x", "xy"]:
        df_.loc["Total"] = df_.agg(total_mode, axis=0)
    if total_mode and total_axis in ["y", "xy"]:
        df_.loc[:, "Total"] = df_.agg(total_mode, axis=1)

    # hack
    # * column sum values are distorted by totals, these must be rendered out
    col_divider = (
        2
        if (total_axis in ["x", "xy"] and pct_axis == "x" and total_mode == "sum")
        else 1
    )
    col_sum = df_.sum() / col_divider

    # * min values are unaffected
    col_min = df_.min()

    # * max values are affected by totals, ignore total row if present
    last_row = -1 if (total_axis in ["x", "xy"] and total_mode == "sum") else None
    col_max = df_[:last_row].max()

    # * derive style
    out = df_.style

    color_highlight = "lightblue" if theme == "light" else "#666666"
    color_zeros = "#A9A9A9" if theme == "light" else "#888888"
    color_pct = "grey" if theme == "light" else "yellow"
    color_values = "black" if theme == "light" else "white"
    color_minus = "red" if theme == "light" else "red"
    cmap_heat = "Blues" if theme == "light" else "copper"

    # * apply data bar coloring
    if data_bar_axis:
        out.bar(
            color=f"{color_highlight}",
            axis=0 if data_bar_axis == "x" else 1 if data_bar_axis == "y" else None,
            width=100,
            # * apply subset if total_exclude
            subset=(df_orig.index, df_orig.columns) if total_exclude else None,
            # align="zero",
        )

    def get_kpi(val: float, col: str) -> str:
        """
        Function to calculate and return the appropriate icon based on the given value and key performance indicator (KPI) mode.

        Parameters:
        val (float): The value to be evaluated.
        col (str): The column associated with the value.

        Returns:
        str: The appropriate icon based on the value and KPI mode.
        """

        # * no icon if no mode. (or Total column, but total index cannot be located)
        if not kpi_mode:
        # if not kpi_mode or col == "Total":
            return ""

        

        dict_icons = {
            "squad": {
                "light": ["🟩", "🟨", "🟥", "⬜"],
                "dark": ["🟩", "🟨", "🟥", "⬛"],
            },
            "circle": {
                "light": ["🟢", "🟡", "🔴", "⚪"],
                "dark": ["🟢", "🟡", "🔴", "⚫"],
            },
        }
        icons = dict_icons[kpi_shape][theme]
        # * transform values into percentiles if relative mode
        kpi_rag_list_ = kpi_rag_list
        if kpi_mode == "rag_rel":
            # * get both percentile thresholds
            pcntl_1 = np.percentile(df_orig, kpi_rag_list[0])
            pcntl_2 = np.percentile(df_orig, kpi_rag_list[1])
            kpi_rag_list_ = [pcntl_1, pcntl_2]

        # * for rag mopde both rel and abs
        if kpi_mode.startswith("rag"):
            # * get fitting icon
            if kpi_rag_list_[0] < kpi_rag_list_[1]:
                icon = (
                    icons[0]
                    if val < kpi_rag_list_[0]
                    else icons[1] if val < kpi_rag_list_[1] else icons[2]
                )
            else:
                icon = (
                    icons[0]
                    if val > kpi_rag_list_[0]
                    else icons[1] if val > kpi_rag_list_[1] else icons[2]
                )
            return icon

        # * for min/max mode, get min and max either from table or column
        # ! care for max values
        min_ = tbl_min if kpi_mode.endswith("_xy") else col_min[col]
        max_ = tbl_max if kpi_mode.endswith("_xy") else col_max[col]

        # * calculate order of icons
        if kpi_mode.startswith("min_max"):
            result = icons[0] if val == min_ else icons[2] if val == max_ else icons[3]
        elif kpi_mode.startswith("max_min"):
            result = icons[0] if val == max_ else icons[2] if val == min_ else icons[3]
        else:
            # * no matching mode found
            result = ""
        return result

    # * all cell formatting in one place
    def format_cell(val, col):
        """
        A function to format a cell value based on the sum and percentage axis.
        Parameters:
        - val: The value of the cell.
        - col: The column index of the cell.

        Returns a formatted string for the cell value.
        """
        # * calc sum depending on pct_axis
        sum_ = tbl_sum if pct_axis == "xy" else col_sum[col] if pct_axis == "x" else val
        val_rel = 0 if sum_ == 0 else val / sum_

        # * get kpi icon
        kpi = get_kpi(val, col=col)
        # * extra format for 0 / neg values
        if val == 0:
            return f'<span style="color: {color_zeros}">{val:.0f} {kpi}</span>'
        if val < 0:
            return (
                f'<span style="color: {color_minus}">{val:_.{precision}f} {kpi}</span>'
            )
        # * here cell > 0
        if pct_axis:
            return f'{val:_.{precision}f} <span style="color: {color_pct}">({val_rel:.1%}) {kpi}</span>'
        if show_as_pct:
            return f"{val:.{precision}%} {kpi}"
        return f"{val:_.{precision}f} {kpi}"

    # * formatter is a dict comprehension, only accepts column names
    formatter = {col: lambda x, col=col: format_cell(x, col=col) for col in df_.columns}

    # ? pct_axis y is not implemented, needs row wise formatting
    #     row_sums = _df.sum(axis=1) / divider
    #     formatter = {
    #         row: lambda x, row=row: format_cell(x, row_sums[row]) for row in _df.index
    #     }

    # * apply formatter
    # debug(formatter)
    out.format(formatter=formatter)
    
    # * apply fonts for cells
    if alter_font:
        out.set_properties(**{"font-family": "Courier"})

    # * apply fonts for th (inkl. index)
    _props_th = [
        # ("font-weight", "bold"),
        ("text-align", "right")
    ]

    _props_td = [
        ("text-align", "right")
    ]

    # * set font sizes: 1) from args, 2) from env vars
    env_th = int(os.getenv("FONT_SIZE_TH",0))
    env_td = int(os.getenv("FONT_SIZE_TD",0))
    
    _th = font_size_th if font_size_th > 0 else env_th
    _td = font_size_td if font_size_td > 0 else env_td
    
    # print(_th, _td)
    
    if font_size_th > 0:
        _props_th.append(("font-size", f"{_th}pt"))
    if font_size_td > 0:
        _props_td.append(("font-size", f"{_td}pt"))
    
    out.set_table_styles(
        [
            dict(selector="th", props=_props_th),
            dict(selector="td", props=_props_td),
        ]
    )
    
    if  col1_width > 0:
        out.set_table_styles([
            {'selector': 'th:first-child, td:first-child', 
            'props': [(f'min-width', f'{col1_width}px !important'), 
                    (f'max-width', f'{col1_width}px !important'), 
                    ('white-space', 'nowrap'), 
                    ('overflow', 'hidden')]}
        ])

    if heatmap_axis:
        out.background_gradient(
            cmap=cmap_heat,
            axis=None if heatmap_axis == "xy" else 0 if heatmap_axis == "y" else 1,
            subset=(df_orig.index, df_orig.columns) if total_exclude else None,
        )

    if png_path is not None:
        # * 72dpi default is too low for high res displays
        dfi.export(obj=out, filename=png_path, dpi=150, table_conversion=png_conversion)
    
    if image_scale:
        display(Markdown(f"<!-- SCALE-{image_scale} -->"))
    
    return out
