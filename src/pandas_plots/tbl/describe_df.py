# import warnings
# warnings.filterwarnings("ignore")

import math
import os
from typing import Literal
from IPython.display import display

import numpy as np
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
from scipy import stats

from ..hlp.wrap_text import wrap_text
from .print_summary import print_summary

# from IPython.display import display, HTML

TOTAL_LITERAL = Literal[
    "sum", "mean", "median", "min", "max", "std", "var", "skew", "kurt"
]
KPI_LITERAL = Literal[
    "rag_abs", "rag_rel", "min_max_xy", "max_min_xy", "min_max_x", "max_min_x"
]

def describe_df(
    df: pd.DataFrame,
    caption: str = "<unknown>",
    use_plot: bool = True,
    use_columns: bool = True,
    use_missing: bool = False,
    renderer: Literal["png", "svg", None] = None,
    fig_cols: int = 5,
    fig_offset: int = None,
    fig_rowheight: int = 300,
    fig_width: int = 300,
    sort_mode: Literal["value", "index"] = "value",
    top_n_uniques: int = 5,
    top_n_chars_in_index: int = 0,
    top_n_chars_in_columns: int = 0,
    missing_figsize: tuple[int, int] = (26, 6),
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
    fig_width (int): width for plot (default 400)
    sort_mode (Literal["value", "index"]): sort by value or index
    top_n_uniques (int): number of uniques to display
    top_n_chars_in_index (int): number of characters to display on index axis on the plot (value range)
    top_n_chars_in_columns (int): number of characters to display as subplot title (column name). If set, minimum is 10.
    missing_figsize (tuple[int, int]): figsize for missing plot (default (26, 6)

    usage:
    describe_df(
        df=df,
        caption="dataframe",
        use_plot=True,
        renderer=None,
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
        print("DataFrame is empty!")
        return

    # * check if print is enabled
    # is_print = (os.getenv("RENDERER") in ('png', 'svg'))

    # if is_print:
    #     # * print <br> to avoid .show() bug in duckdb?
    #     display(HTML("<br>"))

    print(f"🔵 {'*'*3} df: {caption} {'*'*3}  ")
    print(f"🟣 shape: ({df.shape[0]:_}, {df.shape[1]})")
    print(f"🟣 duplicates: {df.duplicated().sum():_}  ")
    # print(f"🟣 uniques: {wrap_text(str({col: f'{df[col].nunique():_}' for col in df})) }  ")
    # print(f"🟣 uniques: { {col: f'{df[col].nunique():_}' for col in df} }")
    # print(f"🟣 uniques: {{ {', '.join(f'{col}: {df[col].nunique():_}' for col in df)} }}")
    # print(f"🟣 missings: {wrap_text(str({col: f'{df[col].isna().sum():_}' for col in df})) }  ")
    # print(f"🟣 missings: { {col: f'{df[col].isna().sum():_}' for col in df} }")
    # print(f"🟣 missings: {dict(df.isna().sum())}")

    n_rows = len(df) # Define the total number of rows

    def get_uniques_header(col: str):
        # * Calculate Missing Values
        n_missing = df[col].isna().sum()
        percent_missing = (n_missing / n_rows) * 100
        
        # * Prep column for unique value count
        if df[col].dtype == "object":
            # Convert object to string to handle mixed types gracefully when counting uniques
            col_series = df[col].astype(str)
        else:
            col_series = df[col]
            
        # * Get unique values and count
        unis = list(col_series.value_counts(dropna=False).sort_index().index)
        n_uniques = len(unis)
        
        # * Format the header string: 🟠 col_name (dtype | uniques | missings)
        header = (
            f"- {col} ({df[col].dtype} | {n_uniques:_} | "
            f"{n_missing:_} ({percent_missing:.0f}%))"
        )
        
        return unis, header


    # hack this block somehow interferes with the plotly renderer. so its run even when use_columns=False
    if use_columns:
        print("🟠 column stats all (dtype | uniques | missings) [values]  ")
        print(f"- index {wrap_text(df.index.tolist()[:top_n_uniques])}  ")
        
    for col in df.columns[:]:
        _u, _h = get_uniques_header(col)
        
        # * check col type (use the original dtype for wrapping)
        is_str = df.loc[:, col].dtype.kind == "O"
        
        # * wrap output
        if use_columns:
                print(
                    f"{_h} {wrap_text(_u[:top_n_uniques], max_items_in_line=70, use_apo=is_str)}  "
                )

    print("🟠 column stats numeric  ")
    # * only show numerics
    # for col in df.select_dtypes("number").columns:
    #     _u, _h = get_uniques_header(col)
    #     print_summary(df=df[col], name=_h)
    print_summary(df=df)

    #  * show first 3 rows
    display(df[:3])

    # ! *** PLOTS ***
    if use_plot:
        # * fix bug(?) in plotly/choreographer - datetime columns are not plotted, set these to str
        # * also make bool -> str for plot to have the <NA> values shown
        datetime_cols = df.select_dtypes(include=['datetime64','boolean']).columns
        df[datetime_cols] = df[datetime_cols].astype(str)
        
        # * fix bug where empty Int64 columns are not plotted
        # * get Int64 columns that are all null -> set to object
        mask = df.dtypes.astype(str).str.lower().isin(['int64', 'float64'])
        df = df.astype(
            dict.fromkeys(
                df.columns[mask][df.loc[:, mask].isnull().all()],
                'object'
            )
        )

        # * now set all empty object columns to <NA>
        null_cols = df.columns[df.dtypes == 'object'][df.loc[:, df.dtypes == 'object'].isnull().all()]
        df[null_cols] = "<NA>"

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
        # fig.layout.height = fig_rowheight * fig_rows
        # fig.layout.width = 400 * fig_cols

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
                if (
                    x.dtype == "object"
                    and top_n_chars_in_index > 0
                    # * check if all values in span are datetime. if so - do not cut! (its just datetime..)
                    and not pd.to_datetime(x, errors='coerce').dropna().shape[0] == pd.Series(x).dropna().shape[0]
                    ) :
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

        # * set template and layout size
        fig.update_layout(
            template="plotly_dark" if os.getenv("THEME") == "dark" else "plotly",
            width=fig_width * fig_cols,  # <-- Set width here
            height=fig_rowheight * fig_rows,  # <-- Set height here
        )

        fig.show(
            renderer=renderer or os.getenv("RENDERER"),
            width=fig_width * fig_cols,  # <-- Set width here
            height=fig_rowheight * fig_rows,  # <-- Set height here
        )
    
    if use_missing:
        import missingno as msno
        msno.matrix(df_, figsize=missing_figsize)