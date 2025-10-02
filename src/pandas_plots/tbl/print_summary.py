# import warnings
# warnings.filterwarnings("ignore")

import math
import os
from collections import abc
from pathlib import Path
from typing import Literal, get_args
from IPython.display import display, HTML

import numpy as np
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
from scipy import stats
import dataframe_image as dfi

import duckdb as ddb

TOTAL_LITERAL = Literal[
    "sum", "mean", "median", "min", "max", "std", "var", "skew", "kurt"
]
KPI_LITERAL = Literal[
    "rag_abs", "rag_rel", "min_max_xy", "max_min_xy", "min_max_x", "max_min_x"
]

def print_summary(df: pd.DataFrame | pd.Series, show: bool = True, name: str=" ", precision: int=3):
    """
    Print statistical summary for a pandas DataFrame or Series.

    The function computes and prints various statistics for each numeric column in a DataFrame 
    or for a Series. Statistics include minimum, lower bound, 25th percentile (Q1), median, 
    mean, 75th percentile (Q3), upper bound, maximum, standard deviation, coefficient of variation, 
    sum, skewness, and kurtosis. The interquartile range (IQR) is used to compute the lower 
    and upper bounds, which are adjusted not to exceed the min and max of the data.
    
    df is being dropna() beforehand to ensure scipy results

    Args:
        df (Union[pd.DataFrame, pd.Series]): Input DataFrame or Series. Only numeric columns 
        in DataFrame are considered.
        show (bool, optional): Whether to print the summary. Defaults to True.
        name (str, optional): Prefix for the summary. Defaults to " ".
        precision (int, optional): Number of digits to round the results to. Defaults to 3.
    """
    if df.empty:
        return 

    # * drop NA to keep scipy sane
    df = df.dropna().copy()    

    # display(df)

    if isinstance(df, pd.DataFrame) and len(df.columns) == 1:
        df = df.to_series()
    
    pd.api.types.is_numeric_dtype(df) 


    if not (
        # * series must be numeric
        (isinstance(df, pd.Series)
            and pd.api.types.is_numeric_dtype(df)
        )
        or 
        # * df must have 2 columns str num
        (len(df.columns) == 2
            and (
                (pd.api.types.is_object_dtype(df.iloc[:, 0]))
                or (pd.api.types.is_bool_dtype(df.iloc[:, 0]))
                )
            and pd.api.types.is_numeric_dtype(df.iloc[:, 1])
        )
    ):
        print(f"❌ df must have 2 columns: [0] str or bool, [1] num, or be a series")
        return




    def print_summary_ser(ser: pd.Series, show: bool=True, name: str="", precision: int=3):
        # Calculate IQR and pass `rng=(25, 75)` to get the interquartile range
        iqr_value = stats.iqr(ser)

        # * drop NA to keep scipy sane
        ser.dropna(inplace=True)
        
        # * on empty series: return
        if ser.empty:
            print(f"{name} -> empty")
            return

        # Using the iqr function, we still calculate the bounds manually
        q1 = round(stats.scoreatpercentile(ser, 25), precision)
        q3 = round(stats.scoreatpercentile(ser, 75), precision)

        # Calculate upper bound directly
        min = round(ser.min(), precision)
        med = round(ser.median(), precision)
        upper = round(q3 + 1.5 * iqr_value, precision)
        lower = round(q1 - 1.5 * iqr_value, precision)
        mean = round(ser.mean(), precision)
        std = round(ser.std(), precision)
        cv = round(ser.std() / ser.mean(), precision)
        max = round(ser.max(), precision)
        sum = round(ser.sum(), precision)
        skew = round(stats.skew(ser.dropna().tolist()), precision)
        kurto = round(stats.kurtosis(ser.dropna().tolist()), precision)
        
        lower = min if lower < min else lower
        upper = max if upper > max else upper

        # * extra care for scipy metrics, these are very vulnarable to nan
        if show:
            print(
                f"""{name} -> min: {min:_} | lower: {lower:_} | q25: {q1:_} | median: {med:_} | mean: {mean:_} | q75: {q3:_} | upper: {upper:_} | max: {max:_} | std: {std:_} | cv: {cv:_} | sum: {sum:_} | skew: {skew} | kurto: {kurto}  """)

        summary = {
            "min": min,
            "lower": lower,
            "q25": q1,
            "median": med,
            "mean": mean,
            "q75": q3,
            "upper": upper,
            "max": max,
            "std": std,
            "cv": cv,
            "sum": sum,
            "skew": skew,
            "kurto": kurto
        }
        return summary

    if isinstance(df, pd.Series):
        # * print serie
        name = df.name if df.name else "series"
        print_summary_ser(ser=df, show=show, name=name, precision=precision)
        return

    if isinstance(df, pd.DataFrame):
        # * print for all values
        print(f"🟧 all data")
        name = df.columns[-1]
        summary = print_summary_ser(ser=df.iloc[:,1], show=show, name=name, precision=precision)

        print(f"🟧 boxes")
        # * print for each value
        for item in df.iloc[:,0].unique():
            # display(df[df.iloc[:,0] == item])
            print_summary_ser(ser=df[df.iloc[:,0] == item].iloc[:,1], show=show, name=item, precision=precision)

    return summary