# import warnings
# warnings.filterwarnings("ignore")

import math
import os
from collections import abc
from typing import Literal, get_args
import numpy as np

import numpy as np
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
from scipy import stats

from .hlp import wrap_text

import duckdb as ddb

# from devtools import debug

pd.options.display.colheader_justify = "right"
# pd.options.mode.chained_assignment = None

TOTAL_LITERAL = Literal[
    "sum", "mean", "median", "min", "max", "std", "var", "skew", "kurt"
]
KPI_LITERAL = Literal[
    "rag_abs", "rag_rel", "min_max_xy", "max_min_xy", "min_max_x", "max_min_x"
]


def descr_db(db: ddb.duckdb.DuckDBPyRelation, caption: str = "db")->None:
    cols = ", ".join(db.columns)
    print(f'🗄️ {caption}\t{db.count("*").fetchone()[0]:_}, {db.columns.__len__()}\n\t("{cols}")')

def describe_df(
    df: pd.DataFrame,
    caption: str,
    use_plot: bool = True,
    use_columns: bool = True,
    use_missing: bool = False,
    renderer: Literal["png", "svg", None] = "png",
    fig_cols: int = 3,
    fig_offset: int = None,
    fig_rowheight: int = 300,
    sort_mode: Literal["value", "index"] = "value",
    top_n_uniques: int = 30,
    top_n_chars_in_index: int = 0,
    top_n_chars_in_columns: int = 0,
):
    """
    This function takes a pandas DataFrame and a caption as input parameters and prints out the caption as a styled header, followed by the shape of the DataFrame and the list of column names. For each column, it prints out the column name, the number of unique values, and the column data type. If the column is a numeric column with more than 100 unique values, it also prints out the minimum, mean, maximum, and sum values. Otherwise, it prints out the first 100 unique values of the column.

    Args:
    df (DataFrame): dataframe
    caption (str): caption to describe dataframe
    use_plot (bool): display plot?
    use_columns (bool): display columns values?
    use_missing (bool): display missing values? (no support for dark theme)
    renderer (Literal["png", "svg", None]): renderer for plot
    fig_cols (int): number of columns in plot
    fig_offset (int): offset for plots as iloc Argument. None = no offset, -1 = omit last plot
    fig_rowheight (int): row height for plot (default 300)
    sort_mode (Literal["value", "index"]): sort by value or index
    top_n_uniques (int): number of uniques to display
    top_n_chars_in_index (int): number of characters to display on plot axis
    top_n_chars_in_columns (int): number of characters to display on plot axis. If set, minimum is 10.

    usage:
    describe_df(
        df=df,
        caption="dataframe",
        use_plot=True,
        renderer="png",
        template="plotly",
        fig_cols=3,
        fig_offset=None,
        sort_mode="value",
    )

    hint: skewness may not properly work if the columns is float and/or has only 1 value
    """
    # * copy df, df col types are modified
    df = df.fillna(pd.NA).copy()
    df_ = df.copy()

    # * check if df is empty
    if len(df) == 0:
        print(f"DataFrame is empty!")
        return

    # ! fix bug(?) in plotly - empty float columns are not plotted, set these to str
    for col in df.columns:
        if df[col].notna().sum() == 0 and df[col].dtype == "float":
            df[col] = df[col].astype(str)

    print(f"🔵 {'*'*3} df: {caption} {'*'*3}")
    print(f"🟣 shape: ({df.shape[0]:_}, {df.shape[1]}) columns: {np.array(df.columns)} ")
    # print(f"🟣 shape: ({df.shape[0]:_}, {df.shape[1]}) columns: {df.columns.tolist()} ")
    print(f"🟣 duplicates: {df.duplicated().sum():_}")
    print(f"🟣 missings: {dict(df.isna().sum())}")

    def get_uniques_header(col: str):
        # * sorting has issues when col is of mixed type (object)
        if df[col].dtype == "object":
            df[col] = df[col].astype(str)
        # * get unique values
        # unis = df[col].sort_values().unique()
        unis = list(df[col].value_counts().sort_index().index)
        # * get header
        header = f"🟠 {col}({len(unis):_}|{df[col].dtype})"
        return unis, header

    # hack this block somehow interferes with the plotly renderer. so its run even when use_columns=False
    if use_columns:
        print("--- column uniques (all)")
        print(f"🟠 index {wrap_text(df.index.tolist()[:top_n_uniques])}")
    for col in df.columns[:]:
        _u, _h = get_uniques_header(col)
        # * check col type
        is_str = df.loc[:, col].dtype.kind == "O"
        # * wrap output
        if use_columns:
                print(
                    f"{_h} {wrap_text(_u[:top_n_uniques], max_items_in_line=70, use_apo=is_str)}"
                )

    print("--- column stats (numeric)")
    # * only show numerics
    for col in df.select_dtypes("number").columns:
        _u, _h = get_uniques_header(col)

        # * extra care for scipy metrics, these are very vulnarable to nan
        # print(
        #     f"{_h} min: {round(df[col].min(),3):_} | max: {round(df[col].max(),3):_} | median: {round(df[col].median(),3):_} | mean: {round(df[col].mean(),3):_} | std: {round(df[col].std(),3):_} | cv: {round(df[col].std() / df[col].mean(),3):_} | sum: {round(df[col].sum(),3):_} | skew: {round(stats.skew(df[col].dropna().tolist()),3)} | kurto: {round(stats.kurtosis(df[col].dropna().tolist()),3)}"
        # )
        print_summary(df[col], _h)

    #  * show first 3 rows
    display(df[:3])

    # ! *** PLOTS ***
    if use_plot:
        # * reduce column names len if selected
        if top_n_chars_in_columns > 0:
            # * minumum 10 chars, or display is cluttered
            top_n_chars_in_columns = (
                10 if top_n_chars_in_columns < 10 else top_n_chars_in_columns
            )
            col_list = []
            for i, col in enumerate(df.columns):
                col_list.append(col[:top_n_chars_in_columns] + "_" + str(i).zfill(3))
            df.columns = col_list

        # * respect fig_offset to exclude unwanted plots from maintanance columns
        cols = df.iloc[:, :fig_offset].columns
        cols_num = df.select_dtypes(np.number).columns.tolist()
        # cols_str = list(set(df.columns) - set(cols_num))

        # * set constant column count, calc rows
        fig_rows = math.ceil(len(cols) / fig_cols)

        fig = make_subplots(
            rows=fig_rows,
            cols=fig_cols,
            shared_xaxes=False,
            shared_yaxes=False,
            subplot_titles=cols,
        )
        # * layout settings
        fig.layout.height = fig_rowheight * fig_rows
        fig.layout.width = 400 * fig_cols

        # * construct subplots
        for i, col in enumerate(cols):
            # * get unique values as sorted list
            if sort_mode == "value":
                span = df[col].value_counts().sort_values(ascending=False)
            else:
                span = df[col].value_counts().sort_index()

            # * check if num col w/ too many values (disabled)
            if col in cols_num and len(span) > 100 and False:
                figsub = px.box(df, x=col, points="outliers")
            else:
                # * only respect 100 items (fixed value)
                x = span.iloc[:100].index
                y = span.iloc[:100].values
                # * cut long strings
                if x.dtype == "object" and top_n_chars_in_index > 0:
                    x = x.astype(str).tolist()
                    _cut = lambda s: (
                        s[:top_n_chars_in_index] + ".."
                        if len(s) > top_n_chars_in_index
                        else s[:top_n_chars_in_index]
                    )
                    x = [_cut(item) for item in x]

                figsub = px.bar(
                    x=x,
                    y=y,
                )
            # * grid position
            _row = math.floor((i) / fig_cols) + 1
            _col = i % fig_cols + 1

            # * add trace to fig, only data not layout, only 1 series
            fig.add_trace(figsub["data"][0], row=_row, col=_col)

        # * set template
        fig.update_layout(
            template="plotly_dark" if os.getenv("THEME") == "dark" else "plotly"
        )
        fig.show(renderer)
    
    if use_missing:
        import missingno as msno
        msno.matrix(df_, figsize=(12, 5))


def pivot_df(
    df: pd.DataFrame,
    dropna: bool = False,
    swap: bool = False,
    top_n_index: int = 0,
    top_n_columns: int = 0,
    data_bar_axis: Literal["x", "y", "xy", None] = "xy",
    pct_axis: Literal["x", "xy", None] = "xy",
    precision: int = 0,
    heatmap_axis: Literal["x", "y", "xy", None] = None,
    total_mode: TOTAL_LITERAL = "sum",
    total_axis: Literal["x", "y", "xy", None] = "xy",
    kpi_rag_list: list[float] = None,
    kpi_mode: KPI_LITERAL = None,
    kpi_shape: Literal["squad", "circle"] = "squad",
) -> pd.DataFrame:
    """
    A function to pivot a DataFrame based on specified parameters hand over to the *show_num_df* function.
    It does not provide much added value since the built-in pivot_table function does the same thing.
    However, it can be useful in certain situations (applying top_n_index and top_n_columns).
    
    First two must be [index] and [columns]
    If 3 columns are given, last one must be the weights column.
    If 2 columns are given, column 3 will be added as flat count.

    Args:
        df (pd.DataFrame): The input DataFrame to be pivoted.
        dropna (bool, optional): Whether to drop NaN values. Defaults to False.
        swap (bool, optional): Whether to swap index and column. Defaults to False.
        top_n_index (int, optional): The number of top index values to consider. Defaults to 0.
        top_n_columns (int, optional): The number of top column values to consider. Defaults to 0.
        data_bar_axis (Literal["x", "y", "xy", None], optional): The axis for displaying data bars. Defaults to "xy".
        pct_axis (Literal["x", "xy", None], optional): The axis for displaying percentages. Defaults to None.
        precision (int, optional): The precision for displaying values. Defaults to 0.
        heatmap_axis (Literal["x","y","xy", None], optional): The axis for displaying heatmaps. Defaults to None.
        total_mode (Literal["sum", "mean", "median", "min", "max", "std", "var", "skew", "kurt"], optional): The aggregation mode for displaying totals. Defaults to "sum".
        total_axis (Literal["x", "y", "xy", None], optional): The axis for displaying totals. Defaults to "xy".
        kpi_mode: a Literal indicating the mode for displaying KPIs ["rag_abs","rag_rel", "min_max_xy", "max_min_xy", "min_max_x", "max_min_x"]
            rag_abs: rag lights (red amber green) based on tresholds given in kpi_rag_list
            rag_rel: rag lights (red amber green) based on percentiles given in kpi_rag_list (0-1)
            min_max_xy: min value green, max valued red for all axes
            max_min_xy: max value green, min valued red for all axes
            min_max_x: min value green, max valued red for x axis
            max_min_x: max value green, min valued red for x axis
        kpi_rag_list: a list of floats indicating the thresholds for rag lights. The list should have 2 elements.
        kpi_shape: a Literal indicating the shape of the KPIs ["squad", "circle"]

    Returns:
        pd.DataFrame: The pivoted DataFrame.
    """
    # * ensure arguments match parameter definition
    if (pct_axis and pct_axis not in ["x", "xy"]) or (
        data_bar_axis and data_bar_axis not in ["x", "y", "xy"]
    ):
        print(f"❌ axis not supported")
        return

    # * if only 2 are provided, add cnt col
    if len(df.columns) == 2:
        df = df.assign(cnt=1)

    if len(df.columns) != 3:
        print("❌ df must have exactly 3 columns")
        return

    if not pd.api.types.is_numeric_dtype(df.iloc[:, 2]):
        print("❌ 3rd column must be numeric")
        return

    df = df.copy()

    col_index = df.columns[0]
    col_column = df.columns[1]
    col_value: str = df.columns[2]

    if not dropna:
        df[col_index].fillna("<NA>", inplace=True)
        df[col_column].fillna("<NA>", inplace=True)
    else:
        df.dropna(inplace=True, subset=[col_index])
        df.dropna(inplace=True, subset=[col_column])

    # * top n indexes
    if top_n_index > 0:
        # * get top n -> series
        # * on pivot tables (all cells are values) you can also use sum for each column[df.sum(axis=1) > n]
        ser_top_n = (
            df.groupby(col_index)[col_value]
            .sum()
            .sort_values(ascending=False)[:top_n_index]
        )
        # * only process top n indexes. this does not change pct values
        df = df[df[col_index].isin(ser_top_n.index)]

    # * top n columns
    if top_n_columns > 0:
        # * get top n -> series
        # * on pivot tables (all cells are values) you can also use sum for each column[df.sum(axis=1) > n]
        ser_top_n_col = (
            df.groupby(col_column)[col_value]
            .sum()
            .sort_values(ascending=False)[:top_n_columns]
        )
        # * only process top n columns. this does not change pct values
        df = df[df[col_column].isin(ser_top_n_col.index)]

    # * create pivot
    df = (
        df.groupby([col_index, col_column], dropna=False)[col_value]
        .sum()
        .reset_index()
        .pivot(index=col_index, columns=col_column, values=col_value)
    )
    df = df.fillna(0)  # .astype(_type)

    return show_num_df(
        df,
        total_mode=total_mode,
        total_axis=total_axis,
        data_bar_axis=data_bar_axis,
        pct_axis=pct_axis,
        swap=swap,
        precision=precision,
        heatmap_axis=heatmap_axis,
        kpi_mode=kpi_mode,
        kpi_rag_list=kpi_rag_list,
        kpi_shape=kpi_shape,
    )


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
):
    """
    A function to display a DataFrame with various options for styling and formatting, including the ability to show totals, apply data bar coloring, and control the display precision.

    Parameters:
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

    # * copy df, do not reference original
    df_ = df.copy() if not swap else df.T.copy()

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
    color_zeros = "grey" if theme == "light" else "grey"
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
    out.set_properties(**{"font-family": "Courier"})

    # * apply fonts for th (inkl. index)
    _props = [
        # ("font-size", "10pt"),
        # ("font-weight", "bold"),
        # ("font-family", "Courier"),
        ("text-align", "right")
    ]
    out.set_table_styles(
        [
            dict(selector="th", props=_props),
            # dict(selector="th:nth-child(1)", props=_props),
        ]
    )

    if heatmap_axis:
        out.background_gradient(
            cmap=cmap_heat,
            axis=None if heatmap_axis == "xy" else 0 if heatmap_axis == "y" else 1,
            subset=(df_orig.index, df_orig.columns) if total_exclude else None,
        )

    return out

def print_summary(df: pd.DataFrame | pd.Series, name: str="🟠 "):
    """
    Print statistical summary for a pandas DataFrame or Series.

    The function computes and prints various statistics for each numeric column in a DataFrame 
    or for a Series. Statistics include minimum, lower bound, 25th percentile (Q1), median, mean, 
    75th percentile (Q3), upper bound, maximum, standard deviation, coefficient of variation, 
    sum, skewness, and kurtosis. The interquartile range (IQR) is used to compute the lower 
    and upper bounds, which are adjusted not to exceed the min and max of the data.

    Args:
        df (Union[pd.DataFrame, pd.Series]): Input DataFrame or Series. Only numeric columns 
        in DataFrame are considered.
    """
    if df.empty:
        return 

    def print_summary_ser(ser: pd.Series, name: str=""):
        # Calculate IQR and pass `rng=(25, 75)` to get the interquartile range
        iqr_value = stats.iqr(ser)

        # Using the iqr function, we still calculate the bounds manually
        q1 = stats.scoreatpercentile(ser, 25)
        q3 = stats.scoreatpercentile(ser, 75)

        # Calculate upper bound directly
        min = round(ser.min(),3)
        med = round(ser.median(),3)
        upper = round(q3 + 1.5 * iqr_value,3)
        lower = round(q1 - 1.5 * iqr_value,3)
        mean = round(ser.mean(),3)
        std = round(ser.std(),3)
        cv = round(ser.std() / ser.mean(),3)
        max = round(ser.max(),3)
        sum = round(ser.sum(),3)
        skew = round(stats.skew(ser.dropna().tolist()),3)
        kurto = round(stats.kurtosis(ser.dropna().tolist()),3)
        
        lower = min if lower < min else lower
        upper = max if upper > max else upper

        # * extra care for scipy metrics, these are very vulnarable to nan
        print(
            f"""{name} min: {min:_} | lower: {lower:_} | q25: {q1:_} | median: {med:_} | mean: {mean:_} | q75: {q3:_} | upper: {upper:_} | max: {max:_} | std: {std:_} | cv: {cv:_} | sum: {sum:_} | skew: {skew} | kurto: {kurto}""")

    if isinstance(df, pd.Series):
        print_summary_ser(df, name)
        return
    if isinstance(df, pd.DataFrame):
        # * only show numerics
        for col in df.select_dtypes("number").columns:
            print_summary_ser(ser=df[col], name=col)
    return