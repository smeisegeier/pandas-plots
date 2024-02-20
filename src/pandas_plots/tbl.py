import warnings
warnings.filterwarnings('ignore')

from scipy import stats
from typing import Literal
import numpy as np
import pandas as pd
import plotly.express as px
import pandas as pd
import math
import os
from plotly.subplots import make_subplots
# pd.options.mode.chained_assignment = None
from . import txt

# ! check pandas version
assert pd.__version__ > '2.0.0', 'pandas version must be >= 2.0.0'

def describe_df(
    df: pd.DataFrame,
    caption: str, 
    use_plot: bool = True,
    use_columns: bool = True,
    renderer: Literal["png", "svg", None] = "png",
    fig_cols: int = 3,
    fig_offset: int = None,
    fig_rowheight: int = 300,
    sort_mode: Literal["value", "index"] = "value",
    top_n_uniques: int = 30,
    top_n_chars_in_index: int = 0,
):
    """
    This function takes a pandas DataFrame and a caption as input parameters and prints out the caption as a styled header, followed by the shape of the DataFrame and the list of column names. For each column, it prints out the column name, the number of unique values, and the column data type. If the column is a numeric column with more than 100 unique values, it also prints out the minimum, mean, maximum, and sum values. Otherwise, it prints out the first 100 unique values of the column.

    Args:
    df (DataFrame): dataframe
    caption (str): caption to describe dataframe
    use_plot (bool): display plot?
    use_columns (bool): display columns values?
    renderer (Literal["png", "svg", None]): renderer for plot
    fig_cols (int): number of columns in plot
    fig_offset (int): offset for plots as iloc Argument. None = no offset, -1 = omit last plot
    fig_rowheight (int): row height for plot (default 300)
    sort_mode (Literal["value", "index"]): sort by value or index
    top_n_uniques (int): number of uniques to display
    top_n_chars_in_index (int): number of characters to display on plot axis
    
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
    df = df.copy()
    
    # * check if df is empty
    if len(df) == 0:
        print(f"DataFrame is empty!")
        return

    print(f"🔵 {'*'*3} df: {caption} {'*'*3}")
    print(f"🟣 shape: ({df.shape[0]:_}, {df.shape[1]}) columns: {df.columns.tolist()} ")
    print(f"🟣 duplicates: {df.duplicated().sum():_}")
    print(f"🟣 missings: {dict(df.isna().sum())}")
    print("--- column uniques (all)")
    print(f"🟠 index {txt.wrap(df.index.tolist()[:top_n_uniques])}")
    def get_uniques_header(col: str):
        # * sorting has issues when col is of mixed type (object)
        if df[col].dtype=='object':
            df[col]=df[col].astype(str)
        # * get unique values
        # unis = df[col].sort_values().unique()
        unis = list(df[col].value_counts().sort_index().index)
        # * get header
        header = f"🟠 {col}({len(unis):_}|{df[col].dtype})"
        return unis, header

    # * show all columns
    for col in df.columns[:]:
        _u, _h = get_uniques_header(col)
        if use_columns:
            # * check col type
            is_str=df.loc[:,col].dtype.kind == 'O'
            # * wrap output
            print(f"{_h} {txt.wrap(_u[:top_n_uniques], max_items_in_line=70, apo=is_str)}")
            # print(f"{_h} {_u[:top_n_uniques]}")
        else:
            print(f"{_h}")

    print("--- column stats (numeric)")
    # * only show numerics
    for col in df.select_dtypes('number').columns:
        _u, _h = get_uniques_header(col)

        # * extra care for scipy metrics, these are very vulnarable to nan
        print(
            f"{_h} min: {round(df[col].min(),3):_} | max: {round(df[col].max(),3):_} | median: {round(df[col].median(),3):_} | mean: {round(df[col].mean(),3):_} | std: {round(df[col].std(),3):_} | cv: {round(df[col].std() / df[col].mean(),3):_} | sum: {round(df[col].sum(),3):_} | skew: {round(stats.skew(df[col].dropna().tolist()),3)} | kurto: {round(stats.kurtosis(df[col].dropna().tolist()),3)}"
        )

    #  * show first 3 rows
    display(df[:3])

    # ! *** PLOTS ***
    if not use_plot:
        return

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
            x=span.iloc[:100].index
            y=span.iloc[:100].values
            # * cut long strings
            if x.dtype=='object' and top_n_chars_in_index > 0:
                x=x.astype(str).tolist()
                _cut = lambda s: s[:top_n_chars_in_index] + '..' if len(s) > top_n_chars_in_index else s[:top_n_chars_in_index]
                x=[_cut(item) for item in x]
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
    fig.update_layout(template="plotly_dark" if os.getenv("THEME") == "dark" else "plotly")
    fig.show(renderer)

def pivot_df(
    df: pd.DataFrame,
    dropna: bool = False,
    swap: bool = False,
    top_n_index: int = 0,
    top_n_columns: int = 0,
    data_bar_axis: Literal["x", "y", "xy", None] = "xy",
    pct_axis: Literal["x", "xy", None] = "xy",
    precision: int = 0,
    show_totals: bool = True,
) -> pd.DataFrame:
    """
    A function to pivot a DataFrame based on specified parameters and return the result as a new DataFrame.
    
    Args:
        df (pd.DataFrame): The input DataFrame to be pivoted.
        dropna (bool, optional): Whether to drop NaN values. Defaults to False.
        swap (bool, optional): Whether to swap index and column. Defaults to False.
        top_n_index (int, optional): The number of top index values to consider. Defaults to 0.
        top_n_columns (int, optional): The number of top column values to consider. Defaults to 0.
        data_bar_axis (Literal["x", "y", "xy", None], optional): The axis for displaying data bars. Defaults to "xy".
        pct_axis (Literal["x", "xy", None], optional): The axis for displaying percentages. Defaults to None.
        precision (int, optional): The precision for displaying values. Defaults to 0.
        show_totals (bool, optional): Whether to show totals in the result. Defaults to False.
        
    Returns:
        pd.DataFrame: The pivoted DataFrame.
    """
    # * ensure arguments match parameter definition
    if (pct_axis and pct_axis not in ["x", "xy"]) or (data_bar_axis and  data_bar_axis not in ["x","y","xy"]):
        print(f"❌ axis not supported")
        return

    if len(df.columns) != 3:
        print("❌ df must have exactly 3 columns")
        return

    if not pd.api.types.is_numeric_dtype(df.iloc[:, 2]):
        print("❌ 3rd column must be numeric")
        return

    col_index = df.columns[0] if not swap else df.columns[1]
    col_column = df.columns[1] if not swap else df.columns[0]
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

    return show_num_df(df, show_totals=show_totals, data_bar_axis=data_bar_axis, pct_axis=pct_axis, swap=swap, precision=precision)

def show_num_df(
    df,
    show_totals: bool = False,
    data_bar_axis: Literal["x","y","xy", None] = None,
    pct_axis: Literal["x", "xy", None] = None,
    swap: bool = False,
    precision: int=0,
):
    """
    A function to display a DataFrame with various options for styling and formatting, including the ability to show totals, apply data bar coloring, and control the display precision. 

    Parameters:
    - df: the DataFrame to display
    - show_totals: a boolean indicating whether to show totals
    - data_bar_axis: a Literal indicating the axis for applying data bar coloring ["x","y","xy", None]
    - pct_axis: a Literal indicating the directions for displaying percentages ["x","xy", None]. "x" means sum up pct per column
    - swap: a boolean indicating whether to swap the axes
    - precision: an integer indicating the display precision

    The function returns a styled representation of the DataFrame.
    """
    # * ensure arguments match parameter definition
    if any([df[col].dtype.kind not in ['i','u','f'] for col in df.columns]) == True:
        print(f"❌ table must contain numeric data only")
        return
    
    if (pct_axis and pct_axis not in ["x", "xy"]) or (data_bar_axis and  data_bar_axis not in ["x","y","xy"]):
        print(f"❌ axis not supported")
        return

    theme = os.getenv("THEME") or "light"
    
    # * copy df, do not reference original
    df_ = df.copy() if not swap else df.T.copy()
    
    # * alter _df, add totals
    if show_totals:
        df_.loc["Total"] = df_.sum(axis=0)
        df_.loc[:, "Total"] = df_.sum(axis=1)

    # * derive style
    out = df_.style

    color_highlight = "lightblue" if theme == "light" else "darkgrey"
    color_zeros = "grey" if theme == "light" else "grey"
    color_pct = "grey" if theme == "light" else "yellow"
    color_values = "black" if theme == "light" else "white"
    color_minus = "red" if theme == "light" else "red"

    # * apply data bar coloring
    if data_bar_axis:
        out.bar(
            color=f"{color_highlight}",
            axis= 0 if data_bar_axis == "x" else 1 if data_bar_axis == "y" else None,
        )

    # * all cell formatting in one place
    # call hierarchy is not very well organized. all options land here, even if no cellwise formatting is applied
    def format_cell(cell, sum, show_pct):
        if cell == 0:
            return f'<span style="color: {color_zeros}">{cell:.0f}</span>'
        if cell < 0:
            return f'<span style="color: {color_minus}">{cell:_.{precision}f}</span>'
        # * here cell > 0
        if show_pct:
            return f'{cell:_.{precision}f} <span style="color: {color_pct}">({(cell /sum):.1%})</span>'
        return f'{cell:_.{precision}f}'

    # * build pct formatting
    if pct_axis =='x':
        # * totals on either axis influence the sum
        divider = 2 if show_totals else 1
        # * cell formatting to each column instead of altering values w/ df.apply
        # * uses dictionary comprehension, and a lambda function with two input variables
        col_sums = df_.sum() / divider
        formatter = {
            col: lambda x, col=col: format_cell(x, col_sums[col], pct_axis) for col in df_.columns
        }

    # ? y is not implemented, needs row wise formatting
    # elif axis=='y':
    #     row_sums = _df.sum(axis=1) / divider
    #     formatter = {
    #         row: lambda x, row=row: format_cell(x, row_sums[row]) for row in _df.index
    #     }

    elif pct_axis=='xy':
        divider = 4 if show_totals else 1
        n = df_.sum().sum() / divider
        formatter = {
            col: lambda x, col=col: format_cell(x, n, pct_axis) for col in df_.columns
        }
    else:
        # * 
        formatter = {
            col: lambda x, col=col: format_cell(x, x, False) for col in df_.columns
        }

    out.format(formatter=formatter)

    # * apply fonts for cells
    out.set_properties(**{'font-family': 'Courier'})

    # * apply fonts for th (inkl. index)
    _props=[
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

    return out