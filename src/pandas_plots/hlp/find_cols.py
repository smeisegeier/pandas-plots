import importlib.metadata as md
import os
import platform
import re
from enum import Enum, auto
from io import BytesIO
from platform import python_version
from typing import List, Literal
import json
import uuid

import duckdb as ddb
import numpy as np
import pandas as pd
import requests
import scipy.stats
from matplotlib import pyplot as plt
from PIL import Image

def find_cols(all_cols: list[str], stubs: list[str] = None):
    """
    Find all columns in a list of columns that contain any of the given stubs.

    Parameters
    ----------
    all_cols : list[str]
        List of columns to search in.
    stubs : list[str]
        List of strings to search for in column names.

    Returns
    -------
    list[str]
        List of columns that contain any of the given stubs.
    """
    if all_cols is None or stubs is None:
        return "❌ empty lists"
    return [col for col in all_cols if any(match in col for match in stubs)]

def find_cols(all_cols: list[str], stubs: list[str] = None) -> list[str]:
    """
    Find all columns in a list of columns that contain any of the given stubs,
    preserving the order of stubs in the output.

    Parameters
    ----------
    all_cols : list[str]
        List of columns to search in.
    stubs : list[str], optional
        List of strings to search for in column names.

    Returns
    -------
    list[str]
        List of columns that contain any of the given stubs, ordered by stubs.
    """
    if all_cols is None or not stubs:
        print("❌ empty lists")
        return []
    
    result = []
    for stub in stubs:
        result.extend([col for col in all_cols if stub.lower() in col.lower()])
    
    return result


# * extend objects to enable chaining
pd.DataFrame.find_cols = find_cols