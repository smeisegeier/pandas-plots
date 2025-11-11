import numbers
import numpy as np
import pandas as pd
from scipy import stats
from typing import Literal

from ..hlp.get_sparse_df import get_sparse_df


def _calculate_summary_ser(
    ser: pd.Series,
    precision: int = 2,
    extended: bool = False,
    sparse: bool = False,
):
    """Calculates the statistics for a single Series (helper function)."""

    def _format_int_with_underscores(n):
        return f"{n:_}"
    
    # 1. Counts
    original_total_count = len(ser)
    ser_cleaned = ser.dropna()
    cnt = len(ser_cleaned) # Non-missing count

    # 2. Present Share calculation (always calculate if not sparse)
    present_share_value = None
    
    if not sparse:
        present_count = cnt # cnt is the non-missing count
        
        if original_total_count > 0:
            # Non-Null Share (User requested content for the 'present' column)
            present_percent = int(present_count / original_total_count * 100) 
            formatted_present_count = _format_int_with_underscores(present_count)
            present_share_value = f"{formatted_present_count} ({present_percent}%)"
            
        else:
            present_share_value = "0 (N/A)"
    
    # 3. All-NaN check: Handle case where no values exist for stats but counts are present
    if ser_cleaned.empty:
        if original_total_count > 0 and not sparse:
            # If all NaNs (not sparse), the present share is 0 (0%)
            summary = {
                "count": original_total_count, # Total N
                # The 'missings' key holds the 'present count/share' value
                "missings": "0 (0%)", 
                "min": "N/A", "lower": "N/A", "q25": "N/A", "median": "N/A", 
                "mean": "N/A", "q75": "N/A", "upper": "N/A", "max": "N/A", 
                "std": "N/A", "cv": "N/A",
            }
            if extended:
                 summary.update({"sum": "N/A", "skew": "N/A", "kurto": "N/A"})
            return summary
        
        # If original_total_count is 0 or sparse mode (where count is 0), return None.
        return None 


    # --- Stats Calculation (using cleaned series) ---
    iqr_value = stats.iqr(ser_cleaned)
    q1 = round(stats.scoreatpercentile(ser_cleaned, 25), precision)
    q3 = round(stats.scoreatpercentile(ser_cleaned, 75), precision)
    min_val = round(ser_cleaned.min(), precision)
    med = round(ser_cleaned.median(), precision)
    
    # Calculate fences and apply to series to find actual min/max within fences
    upper = round(ser_cleaned[ser_cleaned <= q3 + 1.5 * iqr_value].max(), precision)
    lower = round(ser_cleaned[ser_cleaned >= q1 - 1.5 * iqr_value].min(), precision)
    
    mean = round(ser_cleaned.mean(), precision)
    std = round(ser_cleaned.std(), precision)

    cv = ser_cleaned.std() / ser_cleaned.mean() if ser_cleaned.mean() != 0 and ser_cleaned.std() != 0 else np.nan
    cv = round(cv, precision) if not np.isnan(cv) else "N/A"

    max_val = round(ser_cleaned.max(), precision)
    
    # Ensure lower and upper fences don't cut off min/max if they are not outliers
    lower = min_val if lower < min_val else lower
    upper = max_val if upper > max_val else upper

    summary = {
        # Keep 'count' key: len(df) if not sparse, else non-missing count.
        "count": original_total_count if not sparse else cnt, 
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

    # Insert present share into the 'missings' key if not sparse
    if not sparse:
        new_summary = {"count": summary["count"], "missings": present_share_value}
        
        # Add the rest of the keys (starting from 'min')
        for k, v in summary.items():
            if k != "count":
                new_summary[k] = v
        summary = new_summary


    if extended:
        sum_val = round(ser_cleaned.sum(), precision)
        skew = round(stats.skew(ser_cleaned.tolist()), precision)
        kurto = round(stats.kurtosis(ser_cleaned.tolist()), precision)
        summary["sum"] = sum_val
        summary["skew"] = skew
        summary["kurto"] = kurto

    return summary


def _format_summary_table(name_list: list[str], summaries: list[dict], precision: int, extended: bool, sparse: bool, total_df_count: int):
    """
    Formats the list of summaries into a table-like string with simplified formatting.
    All numbers are formatted using f"{{value:_.{precision}f}}" and then the decimal
    point is replaced by an underscore.
    
    The function now accepts 'total_df_count' to display in the header.
    """

    if not summaries or not name_list:
        return ""

    # Define base metrics list
    metrics = ["count", "min", "lower", "q25", "median", "mean", "q75", "upper", "max", "std", "cv"]
    
    if not sparse:
        # Remove the internal 'count' key (which holds N)
        metrics.remove("count")
        # The 'missings' key (which now holds the present count/share) is the first metric
        metrics.insert(0, "missings")
        
    if extended:
        # Include 'sum' and other extended metrics only if extended is True
        metrics.extend(["sum", "skew", "kurto"])

    def format_number_string(value, precision):
        if not isinstance(value, numbers.Number):
            # Handles 'N/A' and the formatted 'present count/share' string
            return str(value)
        if isinstance(value, (float, np.float32, np.float64)):
            val_str = f"{value:_.{precision}f}"
        elif isinstance(value, (int, np.int32, np.int64)):
            val_str = f"{value:_}"
        else:
            return str(value)

        return val_str

    # --- Calculation of widths ---
    name_col_label_base = "item" if sparse else "column" # Renamed header here

    # Format total count for display in the header
    formatted_total_count = f"(n = {total_df_count:_})"
    name_col_label = f"{name_col_label_base} {formatted_total_count}"
    
    name_width = max(len(name_col_label), max(len(n) for n in name_list))
    col_widths = {}

    for metric in metrics:
        value_strs = []
        for s in summaries:
            value = s.get(metric, "N/A")
            val_str = format_number_string(value, precision)
            value_strs.append(val_str)

        col_widths[metric] = max(len(metric), max(len(v) for v in value_strs))

    # --- Build the Table Header and Rows ---
    header = f"{name_col_label:<{name_width}}"
    separator = f"{'-' * name_width}"

    for metric in metrics:
        metric_label = metric
        # User requested: Rename 'missings' column label to 'present' when not sparse
        if not sparse and metric == "missings":
            metric_label = "present"
            
        header += f" | {metric_label:^{col_widths[metric]}}"
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
        max, quartiles) and, optionally, extended statistics (sum, skewness, kurtosis).

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
                If True, includes extended statistics like sum, skewness, kurtosis
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
    
    total_df_count = len(df) # Calculate total count before sparse conversion
    
    if sparse:
        df = get_sparse_df(df)

    summary_list = []
    name_list = []
    last_summary = None

    if isinstance(df, pd.Series):
        name_ser = df.name if df.name else "Series"
        last_summary = _calculate_summary_ser(ser=df, precision=precision, extended=extended, sparse=sparse)
        if last_summary:
            summary_list.append(last_summary)
            name_list.append(name_ser)

    elif isinstance(df, pd.DataFrame):
        numeric_cols = df.select_dtypes(include=np.number).columns
        if numeric_cols.empty:
            print("❌ DataFrame contains no numeric columns for summary calculation.")
            return

        for col_name in numeric_cols:
            ser = df[col_name]
            summary = _calculate_summary_ser(ser=ser, precision=precision, extended=extended, sparse=sparse)
            if summary:
                summary_list.append(summary)
                name_list.append(str(col_name))
                last_summary = summary

    if show and summary_list:
        table_output = _format_summary_table(
            name_list,
            summary_list,
            precision,
            extended,
            sparse,
            total_df_count, # Pass the total count
        )
        print(table_output)

    return last_summary