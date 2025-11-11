import numbers
from typing import Literal

import numpy as np
import pandas as pd
from scipy import stats

from ..hlp.get_sparse_df import get_sparse_df

def _calculate_summary_ser(
    ser: pd.Series,
    precision: int = 2,
    extended: bool = False,
):
    """Calculates the statistics for a single Series (helper function)."""

    # Helper for formatting integers with underscores
    def _format_int_with_underscores(n):
        return f"{n:_}"

    # 1. Calculate missings and total count from the original series
    missing_count = ser.isna().sum()
    total_count = len(ser) # This is the total number of observations (including NaNs)

    # Calculate and format missing percentage (whole number)
    if total_count > 0:
        # CHANGED: Use int() for floor operation on percentage calculation
        missing_percent = int(missing_count / total_count * 100)
        # Format the count part of the string with underscores
        formatted_missings_count = _format_int_with_underscores(missing_count)
        formatted_missings = f"{formatted_missings_count} ({missing_percent}%)"
    else:
        # For a truly empty input Series
        formatted_missings = "0 (N/A)"


    # 2. Drop NaNs to get the clean data for statistics
    ser = ser.dropna()
    
    # 3. Handle series with zero non-missing values
    if ser.empty:
        if total_count == 0:
            return None # Input was an entirely empty Series
        
        # This handles the all-NaN case (total_count > 0, non-missing count is 0)
        summary = {
            "count": total_count, # NOW: Total observations (int, will be formatted by table function)
            "missings": formatted_missings, # Now includes formatted count and percentage
            "min": "N/A", "lower": "N/A", "q25": "N/A", "median": "N/A", 
            "mean": "N/A", "q75": "N/A", "upper": "N/A", "max": "N/A", 
            "std": "N/A", "cv": "N/A",
        }
        if extended:
            summary.update({"sum": "N/A", "skew": "N/A", "kurto": "N/A"})
        return summary

    # --- Calculations for non-empty data start here ---

    iqr_value = stats.iqr(ser)
    q1 = round(stats.scoreatpercentile(ser, 25), precision)
    q3 = round(stats.scoreatpercentile(ser, 75), precision)
    min_val = round(ser.min(), precision)
    med = round(ser.median(), precision)
    # upper = round(q3 + 1.5 * iqr_value, precision)
    # lower = round(q1 - 1.5 * iqr_value, precision)
    upper = round(ser[ser <= q3 + 1.5 * iqr_value].max(), precision)
    lower = round(ser[ser >= q1 - 1.5 * iqr_value].min(), precision)
    

    mean = round(ser.mean(), precision)
    std = round(ser.std(), precision)

    cv = ser.std() / ser.mean() if ser.mean() != 0 and ser.std() != 0 else np.nan
    cv = round(cv, precision) if not np.isnan(cv) else "N/A"

    max_val = round(ser.max(), precision)

    lower = min_val if lower < min_val else lower
    upper = max_val if upper > max_val else upper

    summary = {
        "count": total_count, # Total number of observations (incl. missings)
        "missings": formatted_missings, # Now includes formatted count and percentage
        "min": min_val,
        "lower": lower,
        "q25": q1,
        "median": med,
        "mean": mean,
        "q75": q3,
        "upper": upper,
        "max": max_val,
        "std": std,
        "cv": cv,
    }

    if extended:
        sum_val = round(ser.sum(), precision)
        skew = round(stats.skew(ser.tolist()), precision)
        kurto = round(stats.kurtosis(ser.tolist()), precision)
        summary["sum"] = sum_val
        summary["skew"] = skew
        summary["kurto"] = kurto

    return summary


def _format_summary_table(name_list: list[str], summaries: list[dict], precision: int, extended: bool):
    """
    Formats the list of summaries into a table-like string with simplified formatting.
    All numbers are formatted using f"{{value:_.{precision}f}}" and then the decimal
    point is replaced by an underscore.
    """

    if not summaries or not name_list:
        return ""

    # Define metrics list, conditional on 'extended'. 'missings' remains after 'count'.
    metrics = ["count", "missings", "min", "lower", "q25", "median", "mean", "q75", "upper", "max", "std", "cv"]
    if extended:
        metrics.extend(["sum", "skew", "kurto"])

    def format_number_string(value, precision):
        # The 'missings' value is now a pre-formatted string (e.g., "10_000 (10%)"),
        # so we just return its string representation.
        if not isinstance(value, numbers.Number):
            return str(value) 
        
        if isinstance(value, (float, np.float32, np.float64)):
            val_str = f"{value:_.{precision}f}"
        elif isinstance(value, (int, np.int32, np.int64)):
            # 'count' is an integer, formatted without decimals
            val_str = f"{value:_}" 
        else:
            return str(value)

        return val_str

    # --- Calculation of widths (using the new format_number_string) ---
    name_width = max(len("column"), max(len(n) for n in name_list))
    col_widths = {}

    for metric in metrics:
        value_strs = []
        for s in summaries:
            value = s.get(metric, "N/A")
            val_str = format_number_string(value, precision)
            value_strs.append(val_str)

        col_widths[metric] = max(len(metric), max(len(v) for v in value_strs))

    # --- Build the Table Header and Rows (using the new format_number_string) ---
    header = f"{'column':<{name_width}}"
    separator = f"{'-' * name_width}"

    for metric in metrics:
        header += f" | {metric:^{col_widths[metric]}}"
        separator += f"-+-{'-' * col_widths[metric]}"

    output = f"\n{header}\n{separator}\n"

    for name, summary in zip(name_list, summaries):
        row = f"{name:<{name_width}}"
        for metric in metrics:
            value = summary.get(metric, "N/A")
            val_str = format_number_string(value, precision)

            # Use string representation for alignment
            row += f" | {val_str:>{col_widths[metric]}}"
        output += f"{row}\n"

    return output

def print_summary(
    df: pd.DataFrame | pd.Series,
    show: bool = True,
    name: str = " ",
    precision: int = 3,
    extended: bool = False,
    sparse: bool = False,
):
    """
        Print statistical summary for a pandas DataFrame (all numeric columns) or a Series,
        as a single, neatly aligned table with simplified f-string formatting.

        The function calculates standard descriptive statistics (count, mean, std, min,
        max, quartiles) and, optionally, extended statistics (skewness, kurtosis, NaNs, zeros).

        Args:
            df (pd.DataFrame | pd.Series): 
                The input data to summarize. If a DataFrame, only numeric columns are processed.
            show (bool, optional): 
                If True, prints the generated summary table to the console. Defaults to True.
            name (str, optional):  DEPRECATED
                An optional title or identifier for the overall summary. Currently unused in 
                the implementation's output format but available for future use. Defaults to " ".
            precision (int, optional): 
                The number of decimal places to format the numeric statistics. Defaults to 3.
            extended (bool, optional): 
                If True, includes extended statistics like skewness, kurtosis
                in the summary. Defaults to False.
            sparse (bool, optional): 
                If True, attempts to convert the input DataFrame into a sparse, wide format
                using an inferred pivot before calculating the summary. This requires the 
                external 'get_sparse_df' function to be defined. Defaults to False.

        Returns:
            dict | None: A dictionary containing the summary statistics for the last column 
            or Series processed, or None if the input DataFrame is empty or contains no 
            numeric columns.
        
        Raises:
            (Implicit): May raise an error if `sparse=True` and the necessary 'get_sparse_df' 
            function is not available or fails due to unsuitable DataFrame structure.
    """
    if df.empty:
        return
    
    if sparse:
        df = get_sparse_df(df)

    summary_list = []
    name_list = []
    last_summary = None

    if isinstance(df, pd.Series):
        name_ser = df.name if df.name else "Series"
        last_summary = _calculate_summary_ser(ser=df, precision=precision, extended=extended)
        if last_summary:
            summary_list.append(last_summary)
            name_list.append(name_ser)

    elif isinstance(df, pd.DataFrame):
        # Only process numeric columns
        numeric_cols = df.select_dtypes(include=np.number).columns
        if numeric_cols.empty:
            print("❌ DataFrame contains no numeric columns for summary calculation.")
            return

        for col_name in numeric_cols:
            ser = df[col_name]
            summary = _calculate_summary_ser(ser=ser, precision=precision, extended=extended)
            if summary:
                summary_list.append(summary)
                name_list.append(str(col_name))
                last_summary = summary
        
        if not summary_list:
            print("❌ DataFrame contains no numeric columns to summarize.")
            return


    if show and summary_list:
        table_output = _format_summary_table(
            name_list,
            summary_list,
            precision,
            extended,
        )
        print(table_output)

    return last_summary
