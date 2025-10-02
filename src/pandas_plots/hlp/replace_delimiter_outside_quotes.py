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

def replace_delimiter_outside_quotes(
    input: str, delimiter_old: str = ",", delimiter_new: str = ";", quotechar: str = '"'
):
    """
    Replace the old delimiter with the new delimiter outside of quotes in the input string.

    Args:
        input (str): The input string
        delimiter_old (str): The old delimiter to be replaced
        delimiter_new (str): The new delimiter to replace the old delimiter
        quotechar (str): The character used to denote quotes

    Returns:
        str: The modified string with the delimiters replaced
    """
    outside_quotes = True
    output = ""
    # * loop through input and toggle inside/outside status
    for char in input:
        if char == quotechar:
            outside_quotes = not outside_quotes
        elif outside_quotes and char == delimiter_old:
            char = delimiter_new
        output += char
    return output