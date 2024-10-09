import pandas as pd
import numpy as np
import scipy.stats
import importlib.metadata as md
from platform import python_version
from typing import Literal, List

from enum import Enum, auto
import platform
import os

from io import BytesIO
from matplotlib import pyplot as plt
from PIL import Image
import requests
import re

# from devtools import debug

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
    text: str | list,
    max_items_in_line: int = 70,
    use_sep: bool = True,
    use_apo: bool = False,
):
    """
    A function that wraps text into lines with a maximum number of items per line.
    Important: enclose this function in a print() statement to print the text

    Args:
        text (str | list): The input text or list of words to be wrapped.
        max_items_in_line (int): The maximum number of items allowed in each line.
        use_sep (bool, optional): When list: Whether to include a comma separator between items. Defaults to True.
        use_apo (bool, optional): When list: Whether to enclose each word in single quotes. Defaults to False.
    Returns: the wrapped text
    """

    # * check if text is string
    is_text = isinstance(text, str)
    if is_text:
        # ! when splitting the text later by blanks, newlines are not correctly handled
        # * to detect them, they must be followed by a blank:
        pattern = r"(\n)(?=\S)"  # *forward lookup for newline w/ no blank
        # * add blank after these newlines
        new_text = re.sub(pattern, r"\1 ", text)
        text = new_text

        # * then strip and build word list
        text = (
            text.replace(",", "")
            .replace("'", "")
            .replace("[", "")
            .replace("]", "")
            # * use explicit blanks to prevent newline split
            .split(" ")
        )

    # * loop setup
    i = 0
    line = ""
    # * loop through words
    out = ""
    for word in text:
        apo_s = "'" if use_apo and not is_text else ""
        sep_s = "," if use_sep and not is_text else ""
        word_s = f"{apo_s}{str(word)}{apo_s}{sep_s}"
        # * inc counter
        i = i + len(word_s)
        # * construct print line
        line = line + word_s + " "
        # * reset if counter exceeds limit, or if word ends with newline
        if i >= max_items_in_line or str(word).endswith("\n"):
            out = out + line + "\n"
            line = ""
            i = 0
        # else:
    # * on short lists no line reset happens, so just print the line
    # * else add last line
    out = line if not out else out + line
    # * cut off last newline
    return f"[{out[:-1].strip()}]"


def create_barcode_from_url(
    url: str,
    output_path: str | None = None,
    show_image: bool = False,
):
    """
    Create a barcode from the given URL. Uses "QR Code" from DENSO WAVE INCORPORATED.

    Args:
        url (str): The URL to encode in the barcode.
        output_path (str | None, optional): The path to save the barcode image. Defaults to None.
        show_image (bool, optional): Whether to display the barcode image. Defaults to False.
    """
    WIDTH = 400
    HEIGHT = 400

    if not re.match(URL_REGEX, url):
        print("💡 Not a valid URL")

    image = requests.get(
        # f"https://chart.googleapis.com/chart?chs={WIDTH}x{HEIGHT}&cht=qr&chl={url}"
        f"https://api.qrserver.com/v1/create-qr-code/?size={WIDTH}x{HEIGHT}&data={url}"
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


def add_datetime_columns(df: pd.DataFrame, date_column: str = None) -> pd.DataFrame:
    df_ = df.copy()
    if not date_column:
        date_column = [
            col for col in df_.columns if pd.api.types.is_datetime64_any_dtype(df_[col])
        ][0]
    else:
        df_[date_column] = pd.to_datetime(df_[date_column])

    if not date_column or not pd.api.types.is_datetime64_any_dtype(df_[date_column]):
        print("❌ No datetime column found")
        return

    if [col for col in df_.columns if "YYYY-WW" in col]:
        print("❌ Added datetime columns already exist")
        return

    print(f"⏳ Adding datetime columns basing off of: {date_column}")

    df_["YYYY"] = df_[date_column].dt.year
    df_["MM"] = df_[date_column].dt.month
    df_["Q"] = df_[date_column].dt.quarter

    df_["YYYY-MM"] = df_[date_column].dt.to_period("M").astype(str)
    df_["YYYYQ"] = df_[date_column].dt.to_period("Q").astype(str)
    df_["YYYY-WW"] = (
        df_[date_column].dt.isocalendar().year.astype(str)
        + "-W"
        + df_[date_column].dt.isocalendar().week.astype(str).str.zfill(2)
    )
    df_["DDD"] = df_[date_column].dt.weekday.map(
        {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}
    )

    return df_


def show_package_version(
    packages: list[str] = None,
    sep: str = " | ",
    include_demo_packages: bool = True,
) -> None:
    """
    Display the versions of the specified packages.

    Parameters:
        packages (list[str], optional): A list of package names. Defaults to ["pandas","numpy","duckdb","pandas-plots", "connection_helper"].
        sep (str, optional): The separator to use when joining the package names and versions. Defaults to " | ".
        include_demo_packages: If True, inlude all demo packages

    Returns:
        None
    """
    # ! avoid empty list in signature, it will NOT be empty in runtime
    if packages is None:
        packages = []
    
    if not isinstance(packages, List):
        print(f"❌ A list of str must be provided")
        return
    demo = [
        "pandas",
        "numpy",
        "duckdb",
        "pandas-plots",
        "connection_helper",
    ]
    items = []
    items.append(f"🐍 {python_version()}")
    if include_demo_packages:
        packages.extend(demo)

    for item in packages:
        try:
            version = md.version(item)
            items.append(f"📦 {item}: {version}")
        except md.PackageNotFoundError:
            items.append(f"❌ {item}: Not found")
    out = sep.join(items).strip()
    print(out)
    return

class OperatingSystem(Enum):
    WINDOWS = auto()
    LINUX = auto()
    MAC = auto()


def get_os(is_os: OperatingSystem = None, verbose: bool = False) -> bool | str:
    """
    A function that checks the operating system and returns a boolean value based on the operating system to check.

    Parameters:
        is_os (OperatingSystem): The operating system to check against. Defaults to None.
        Values are
            - OperatingSystem.WINDOWS
            - OperatingSystem.LINUX
            - OperatingSystem.MAC

    Returns:
        bool: True if the desired operating system matches the current operating system, False otherwise. 
        str: Returns the current operating system (platform.system()) if is_os is None.
    """
    if verbose:
        print(
            f"💻 os: {os.name} | 🎯 system: {platform.system()} | 💽 release: {platform.release()}"
        )

    if is_os is None:
        return platform.system()

    if is_os == OperatingSystem.WINDOWS and platform.system() == "Windows":
        return True
    elif is_os == OperatingSystem.LINUX and platform.system() == "Linux":
        return True
    elif is_os == OperatingSystem.MAC and platform.system() == "Darwin":
        return True
    else:
        return False
