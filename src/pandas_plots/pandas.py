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
    def get_uniques_header(col: str):
        # * sorting has issues when col is of mixed type (object)
        if df[col].dtype=='object':
            df[col]=df[col].astype(str)
        # * get unique values
        unis = df[col].sort_values().unique()
        # * get header
        header = f"🟠 {col}({len(unis):_}|{df[col].dtype})"
        return unis, header

    # * show all columns
    for col in df.columns[:]:
        _u, _h = get_uniques_header(col)
        if use_columns:
            # * limit output to 100 items
            print(f"{_h} {_u[:top_n_uniques]}")
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
    normalize: bool = False,
    normalize_mixed: bool = False,
    swap: bool = False,
    top_n_index: int = 0,
    top_n_columns: int = 0,
    data_bar_axis: Literal["x", "y", "all", False] = "all",
    precision: int = 0,
    totals: Literal["x", "y", "all", False] = "all",
# ) -> pd.DataFrame:
) -> None:
    """
    Pivots a DataFrame and performs various operations based on the specified parameters.

    Parameters:
        df (pd.DataFrame): The DataFrame to be pivoted.
        dropna (bool, optional): Whether to drop rows with missing values. Defaults to False.
        normalize (bool, optional): Whether to normalize the values. Defaults to False.
        normalize_mixed (bool, optional): Whether to show mixed values. Defaults to False. OVERRIDES "normalize"
        swap (bool, optional): Whether to swap the index and column names. Defaults to False.
        top_n_index (int, optional): The number of top indexes to consider. Defaults to 0.
        top_n_columns (int, optional): The number of top columns to consider. Defaults to 0.
        data_bar_axis (Literal["x", "y", "all", False], optional): The axis to apply data bars on. Defaults to "all".
        precision (int, optional): The precision of the values. Defaults to 0.
        totals (Literal["x", "y", "all", False], optional): Whether to show totals. Defaults to "all".

    Returns:
        None
    Usage:
    pivot_df(
        df,
        dropna=True,
        normalize=True,
        normalize_mixed=True
        swap=True,
        top_n_index=5,
        top_n_columns=2,
        data_bar_axis=None,
        precision=2,
    )
    """

    theme = os.getenv('THEME') or 'light'

    color_highlight = 'lightblue' if theme == 'light' else 'darkgrey'
    color_zeros = 'grey' if theme == 'light' else 'grey'
    color_pct = 'grey' if theme == 'light' else 'yellow'
    color_values = 'black' if theme == 'light' else 'white'
    color_minus = 'red' if theme == 'light' else 'red'

    if len(df.columns) != 3:
        print("df must have exactly 3 columns")
        return
    if not pd.api.types.is_numeric_dtype(df.iloc[:, 2]):
        print("3rd column must be numeric")
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

    # * now calculate n, after dropna, before top n
    n = df[col_value].sum()

    if normalize:
        df[col_value] = df[col_value] / n
        _formatter = f"{{:_.{precision}%}}"
    else:
        # _type= 'int'
        _formatter = f"{{:_.{precision}f}}"

    if normalize_mixed:
        _formatter = (
            lambda x: f"{{:_.0f}} <span style='color: {color_pct}'>({{:.1%}})</span>".format(x, x / n)
            if x > 0
            else x
        )

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

    # top n columns
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

    if totals in(['x','all']):
        df.loc["Total"] = df.sum(axis=0)
    if totals in(['y','all']):
        df.loc[:, "Total"] = df.sum(axis=1)

    out = df.style.map(
        lambda x: f"color: {color_zeros}"
        if x == 0
        else f"color: {color_minus}"
        if x < 0
        else f"color: {color_values}"
    )

    # * apply data bar coloring
    if data_bar_axis:
        out.bar(
            color=f"{color_highlight}",
            axis=1 if data_bar_axis == "y" else 0 if data_bar_axis == "x" else None,
            # props="width: 5%;",
        )

    # * apply formatter selected above
    out.format(_formatter)

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

    display(out)
    return

