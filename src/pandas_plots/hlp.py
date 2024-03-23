import pandas as pd
import numpy as np
import scipy.stats

from io import BytesIO
from matplotlib import pyplot as plt
from PIL import Image
import requests
import re

from tenacity import retry

URL_REGEX = r"^(?:http|ftp)s?://"  # https://stackoverflow.com/a/1617386


def mean_confidence_interval(df, confidence=0.95):
    """
    Calculate the mean and confidence interval of the input dataframe.
    source: https://stackoverflow.com/questions/15033511/compute-a-confidence-interval-from-sample-data

    Parameters:
    df (array-like): The input dataframe.
    confidence (float, optional): The confidence level for the interval. Defaults to 0.95.

    Returns:
    tuple: A tuple containing the mean, interval, lower bound, and upper bound.
    """
    df = df_to_series(df)
    if df is None:
        return None
    a = 1.0 * np.array(df)
    n = len(a)
    mean, se = np.mean(a), scipy.stats.sem(a)
    # * calculate the margin of error for the confidence interval using the t-distribution with the specified confidence level.
    margin = se * scipy.stats.t.ppf((1 + confidence) / 2.0, n - 1)
    lower = mean - margin
    upper = mean + margin
    return mean, margin, lower, upper

    # # * Alternative
    # # from statistics import NormalDist
    # def confidence_interval(data, confidence=0.95):
    #     dist = NormalDist.from_samples(data)
    #     z = NormalDist().inv_cdf((1 + confidence) / 2.)
    #     h = dist.stdev * z / ((len(data) - 1) ** .5)
    #     return dist.mean - h, dist.mean + h


def df_to_series(df) -> pd.Series | None:
    """
    Converts a pandas DataFrame to a pandas Series.

    Parameters:
        df (pd.DataFrame): The DataFrame to be converted.

    Returns:
        pd.Series | None: The converted Series if successful, None otherwise.

    Raises:
        None

    Notes:
        - If the input `df` is already a Series, it is returned as is.
        - If the input `df` has more than 2 columns, an error message is printed and None is returned.
        - If the input `df` has 1 column, a new Series is created with the input column as the data and the input index as the index.
        - If the input `df` has 2 columns, the function checks which column is the index. If the first column is numeric, the second column is set as the data and the first column is set as the index. If the second column is numeric, the first column is set as the data and the second column is set as the index. If neither column is numeric, an error message is printed and None is returned.
        - The index and name of the resulting Series are set to the appropriate labels.
    """
    # * check if df is a series
    if isinstance(df, pd.Series):
        return df
    # * too many columns
    if len(df.columns) > 2:
        print("❌ df must have exactly 2 columns")
        return None
    # * df can have 1 column, proper index is assumed then
    elif len(df.columns) == 1:
        return pd.Series(index=df.index, data=df.iloc[:, 0].values, name=df.columns[0])
    else:
        # * check which column is the index
        if pd.api.types.is_numeric_dtype(df.iloc[:, 0]):
            _idx_col = df.iloc[:, 1]
            _data_col = df.iloc[:, 0]
        elif pd.api.types.is_numeric_dtype(df.iloc[:, 1]):
            _idx_col = df.iloc[:, 0]
            _data_col = df.iloc[:, 1]
        else:
            print("❌ df must have exactly 1 numeric column")
            return None
        s = pd.Series(
            index=_idx_col.values,
            data=_data_col.values,
        )
        # * set index and name to proper labels
        s.index.name = _idx_col.name
        s.name = _data_col.name
        return s


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


def wrap_text(
    text: str | list, max_items_in_line: int = 70, sep: bool = True, apo: bool = False
):
    """
    A function that wraps text into lines with a maximum number of items per line.

    Args:
        text (str | list): The input text or list of words to be wrapped.
        max_items_in_line (int): The maximum number of items allowed in each line.
        sep (bool, optional): Whether to include a comma separator between items. Defaults to True.
        apo (bool, optional): Whether to enclose each word in single quotes. Defaults to False.
    """

    # * check if text is string, then strip and build word list
    is_text = isinstance(text, str)
    if is_text:
        text = (
            text.replace(",", "")
            .replace("'", "")
            .replace("[", "")
            .replace("]", "")
            .split(" ")
        )

    # * start
    i = 0
    line = ""

    # * loop through words
    out = ""
    for word in text:
        apo_s = "'" if apo else ""
        sep_s = "," if sep and not is_text else ""
        word_s = f"{apo_s}{str(word)}{apo_s}{sep_s}"
        # * inc counter
        i = i + len(word_s)
        # * construct print line
        line = line + word_s + " "
        # * reset if counter exceeds limit
        if i >= max_items_in_line:
            out = out + line + "\n"
            line = ""
            i = 0
        # else:
    # * on short lists no reset happens, trigger manually
    out = line if not out else out
    # * cut last newline
    return f"[{out[:-1]}]"


def create_barcode_from_url(
    url: str,
    output_path: str | None = None,
    show_image: bool = False,
):
    WIDTH = 400
    HEIGHT = 400

    if not re.match(URL_REGEX, url):
        print("❌ Not a valid URL")
        return

    image = requests.get(
        f"https://chart.googleapis.com/chart?chs={WIDTH}x{HEIGHT}&cht=qr&chl={url}"
    )
    image.raise_for_status()

    # * write binary content to file
    if output_path:
        with open(output_path, "wb") as qr:
            qr.write(image.content)

    # * Load the image from the response content
    if show_image:
        img = Image.open(BytesIO(image.content))
        plt.imshow(img)
        # plt.axis('off')  # Turn off axis numbers
        plt.show()
