# import warnings
# warnings.filterwarnings("ignore")

from pathlib import Path
from typing import Literal, Optional
from ..hlp.group_kkr import group_kkr

import pandas as pd


TOTAL_LITERAL = Literal[
    "sum", "mean", "median", "min", "max", "std", "var", "skew", "kurt"
]
KPI_LITERAL = Literal[
    "rag_abs", "rag_rel", "min_max_xy", "max_min_xy", "min_max_x", "max_min_x"
]

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
    show_as_pct: bool = False,
    alter_font: bool = True,
    font_size_th: int = 0,
    font_size_td: int = 0,
    col1_width: int = 0,
    png_path: str | Path = None,
    png_conversion: Literal["chrome", "selenium"] = "selenium",
    kkr_col: Optional[str] = None,
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
        show_as_pct (bool, optional): Whether to show values as percentages. Defaults to False.
        alter_font (bool, optional): Whether to alter the font. Defaults to True.
        font_size_th (int, optional): The font size for the header. Defaults to 0.
        font_size_td (int, optional): The font size for the table data. Defaults to 0.
        col1_width (int, optional): The width of the first column in px. Defaults to 0.
        png_path (str | Path, optional): The path to save the output PNG file. Defaults to None.
        png_conversion (Literal["chrome", "selenium"], optional): The conversion method for the PNG file. Defaults to "selenium".
        kkr_col (str): Edge case: Name of the column that contains kkr name to ensure all kkr are shown


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

    if kkr_col:
        df = group_kkr(df=df, kkr_col=kkr_col)


    col_index = df.columns[0]
    col_column = df.columns[1]
    col_value: str = df.columns[2]

    if not dropna:
        df[col_index] = df[col_index].fillna("<NA>")
        df[col_index] = df[col_index].fillna("<NA>")
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

    from .show_num_df import show_num_df
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
        show_as_pct=show_as_pct,
        alter_font=alter_font,
        font_size_th=font_size_th,
        font_size_td=font_size_td,
        col1_width=col1_width,
        png_path=png_path,
        png_conversion=png_conversion,
    )
