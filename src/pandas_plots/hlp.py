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

# from devtools import debug

URL_REGEX = r"^(?:http|ftp)s?://"  # https://stackoverflow.com/a/1617386

def mean_confidence_interval(data, confidence=0.95, use_median=False, n_bootstraps=1000):
    """
    Calculate the mean or median and confidence interval.
    For median, uses bootstrapping for a more robust confidence interval.

    Parameters:
    data (array-like): The input data.
    confidence (float, optional): The confidence level for the interval. Defaults to 0.95.
    use_median (bool, optional): If True, calculates median and its confidence interval. Defaults to False.
    n_bootstraps (int, optional): Number of bootstrap samples for median CI. Only used if use_median is True.

    Returns:
    tuple: A tuple containing the central value (mean or median), margin of error, lower bound, and upper bound.
    """
    data = to_series(data)
    if data is None or len(data) == 0:
        return np.nan, np.nan, np.nan, np.nan
    a = 1.0 * np.array(data)
    n = len(a)

    if use_median:
        if n < 2: # Cannot bootstrap with n < 2
            return np.median(a), np.nan, np.nan, np.nan

        bootstrapped_medians = []
        for _ in range(n_bootstraps):
            sample = np.random.choice(a, size=n, replace=True)
            bootstrapped_medians.append(np.median(sample))

        median = np.median(a)
        alpha = (1 - confidence) / 2
        lower_bound = np.percentile(bootstrapped_medians, alpha * 100)
        upper_bound = np.percentile(bootstrapped_medians, (1 - alpha) * 100)
        margin = (upper_bound - lower_bound) / 2 # Simple approximation for margin based on interval width
        return median, margin, lower_bound, upper_bound
    else:
        mean = np.mean(a)
        if n <= 1:
            return mean, np.nan, np.nan, np.nan
        se = scipy.stats.sem(a)
        margin = se * scipy.stats.t.ppf((1 + confidence) / 2.0, n - 1)
        return mean, margin, mean - margin, mean + margin


def to_series(df) -> pd.Series | None:
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

# * extend objects to enable chaining
pd.DataFrame.to_series = to_series
pd.Series.to_series = to_series


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
            # out = out + line + "\n"
            out = out + line.rstrip() + "  \n"
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
    """
    Add datetime columns to a given DataFrame.

    Adds the following columns to the given DataFrame:
        - YYYY: Year of date_column
        - MM: Month of date_column
        - Q: Quarter of date_column
        - YYYY-MM: Year-month of date_column
        - YYYYQ: Year-quarter of date_column
        - YYYY-WW: Year-week of date_column
        - DDD: Day of the week of date_column

    Args:
        df (pd.DataFrame): The DataFrame to add datetime columns to.
        date_column (str, optional): The column to base the added datetime columns off of. Defaults to None.

    Returns:
        pd.DataFrame: The DataFrame with the added datetime columns.
        This command can be chained.
    """
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

# * extend objects to enable chaining
pd.DataFrame.add_datetime_columns = add_datetime_columns


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
        "connection-helper",
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


def add_bitmask_label(
    data: pd.DataFrame | pd.Series | ddb.DuckDBPyRelation,
    bitmask_col: str,
    labels: list[str],
    separator: str = "|",
    zero_code: str = "-",
    keep_col: bool = True,
    con: ddb.DuckDBPyConnection = None,
) -> pd.DataFrame | ddb.DuckDBPyRelation:
    """
    adds a column to the data (DataFrame, Series, or DuckDB Relation) that resolves a bitmask column into human-readable labels.
    - bitmask_col must have been generated before. its value must be constructed as a bitmask, e.g:
    - a red, green, blue combination is rendered into binary 110, which means it has green and blue
    - its value is 6, which will resolved into "g|b" if the list ["r","g","b"] is given

    if the bitmask value is 0, it will be replaced with the zero_code.
    the method can be chained in pandas as well as in duckdb: df.add_bitmask_label(...)

    Parameters:
    - data (pd.DataFrame | pd.Series | duckdb.DuckDBPyRelation): Input data.
    - bitmask_col (str): The name of the column containing bitmask values (ignored if input is Series).
    - labels (list[str]): Labels corresponding to the bits, in the correct order.
    - separator (str): Separator for combining labels. Default is "|".
    - zero_code (str): Value to return for bitmask value 0. Default is "-".
    - keep_col (bool): If True, retains the bitmask column. If False, removes it. Default is True.
    - con (duckdb.Connection): DuckDB connection object. Required if data is a DuckDB Relation.

    Returns:
    - pd.DataFrame | duckdb.DuckDBPyRelation: The modified data with the new column added.
    """
    # * check possible input formats
    if isinstance(data, ddb.DuckDBPyRelation):
        if con is None:
            raise ValueError(
                "A DuckDB connection must be provided when the input is a DuckDB Relation."
            )
        data = data.df()  # * Convert DuckDB Relation to DataFrame

    if isinstance(data, pd.Series):
        bitmask_col = data.name if data.name else "bitmask"
        data = data.to_frame(name=bitmask_col)

    if not isinstance(data, pd.DataFrame):
        raise ValueError(
            "Input must be a pandas DataFrame, Series, or DuckDB Relation."
        )

    # * get max allowed value by bitshift, eg for 4 labels its 2^4 -1 = 15
    max_allowable_value = (1 << len(labels)) - 1
    # * compare against max in col
    max_value_in_column = data[bitmask_col].max()
    if max_value_in_column > max_allowable_value:
        raise ValueError(
            f"The maximum value in column '{bitmask_col}' ({max_value_in_column}) exceeds "
            f"the maximum allowable value for {len(labels)} labels ({max_allowable_value}). "
            f"Ensure the number of labels matches the possible bitmask range."
        )

    # ? Core logic
    # * exit if 0
    def decode_bitmask(value):
        if value == 0:
            return zero_code
        # * iterate over each value as bitfield, on binary 1 fetch assigned label from [labels]
        return separator.join(
            [label for i, label in enumerate(labels) if value & (1 << i)]
        )

    label_col = f"{bitmask_col}_label"
    data[label_col] = data[bitmask_col].apply(decode_bitmask)

    # * drop value col if not to be kept
    if not keep_col:
        data = data.drop(columns=[bitmask_col])

    # * Convert back to DuckDB Relation if original input was a Relation
    if isinstance(data, pd.DataFrame) and con is not None:
        return con.from_df(data)

    return data


# * extend objects to enable chaining
pd.DataFrame.add_bitmask_label = add_bitmask_label
ddb.DuckDBPyRelation.add_bitmask_label = add_bitmask_label


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


def add_measures_to_pyg_config(json_path: str, nodes: list[tuple[str, str]] = [("cnt_tum", "count(distinct z_tum_id)")], strict: bool = False) -> None:
    """
    Reads a pygwalker JSON config file, adds new measures from given nodes if not already present, and writes back to the file.

    Parameters
    ----------
    json_path : `str`
        The path to the pygwalker JSON config file.
    nodes : `list[tuple[str, str]]`, optional
        A list of tuples, where the first element in the tuple is the name of the measure and the second element is the SQL expression that defines the measure. Default is `[('cnt_tum', 'count(distinct z_tum_id)')]`.
    strict : `bool`, optional
        If True, raises an error if the file does not exist or if JSON parsing fails. If False, the function exits silently in such cases. Default is False.

    Returns
    -------
    None

    Example
    -------
    default: `add_measures_to_pyg_config('config.json', [('cnt_tum', 'count(distinct z_tum_id)')], strict=True)`
    
    usage: start pygwalker with empty config file but defined config path. make changes on the chart, save the config file. then run this function again - measures will be added
    """
    if not os.path.exists(json_path):
        if strict:
            raise FileNotFoundError(f"File not found: {json_path}")
        return

    try:
        with open(json_path, "r", encoding="utf-8") as file:
            config = json.load(file)
    except json.JSONDecodeError:
        if strict:
            raise
        return

    for node in nodes:
        fid = uuid.uuid4().hex
        
        # * Define the measure
        new_json_node = {
            "analyticType": "measure",
            "fid": f"{fid}",
            "name": f"{node[0]}",
            "semanticType": "quantitative",
            "computed": True,
            "aggName": "expr",
            "expression": {
                "op": "expr",
                "as": f"{fid}",
                "params": [{"type": "sql", "value": f"{node[1]}"}]
            }
        }

        # * Get the measures list
        measures = config.get("config", [{}])[0].get("encodings", {}).get("measures", [])

        # * Ensure the measure is present
        if not any(measure.get("name") == node[0] for measure in measures):
            measures.append(new_json_node)

    # * Write the updated JSON back to the file
    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(config, file, indent=2)



def get_tum_details(z_tum_id: str, con: ddb.DuckDBPyConnection) -> None:
    """
    Prints the details of a specific tumor to the console.
    Needs con to clinical cancer data
    v2.3

    Args:
        z_tum_id (str): The ID of the tumor to retrieve details for.
        con (dbr.DuckDB): A DuckDB connection object.

    Returns:
        None
    """
    print("pat")
    (con.sql(f"""--sql
        select
                z_pat_id,
                z_sex,
                z_age,
                z_ag05,
                Verstorben,
                Geburtsdatum,
                Geburtsdatum_Genauigkeit,
                DatumVitalstatus,
                DatumVitalstatus_Genauigkeit,
        from Patient
        join Tumor on Patient.oBDS_RKIPatientId = Tumor.z_pat_id
        where z_tum_id = '{z_tum_id}'
        order by z_tum_order
        """)
        .show()
    )
    print("tod")
    (con.sql(f"""--sql
        select  TodesursacheId,
                Code,
                Version,
                IsGrundleiden,
        from Todesursache tu
        join Tumor on tu.oBDS_RKIPatientId = Tumor.z_pat_id
        where z_tum_id = '{z_tum_id}'
        """)
        .show()
    )

    print("tum1")
    (con.sql(f"""--sql
        select  z_kkr_label,
                z_icd10,
                Diagnosedatum,
                Diagnosedatum_Genauigkeit,
                z_tum_op_count,
                z_tum_st_count,
                z_tum_sy_count,
                z_tum_fo_count,
                z_first_treatment,
                z_first_treatment_after_days,
        from Tumor
        where z_tum_id = '{z_tum_id}'
        order by z_tum_order
        """)
        .show()
    )

    print("tum2")
    (con.sql(f"""--sql
        select
                z_event_order,
                z_events,
                Anzahl_Tage_Diagnose_Tod,
                z_period_diag_death_day,
                DatumPSA,
                z_period_diag_psa_day,
                z_last_tum_status,
                z_class_hpv,
                z_tum_order,
        from Tumor
        where z_tum_id = '{z_tum_id}'
        order by z_tum_order
        """)
        .show()
    )

    print("op")
    (con.sql(f"""--sql
        select * exclude (z_kkr)
        from OP
        where z_tum_id = '{z_tum_id}'
        order by z_op_order
        """)
        .project("* exclude (z_tum_id)")
        .show()
    )

    print("ops")
    (con.sql(f"""--sql
        select * exclude (z_kkr)
        from OPS
        where z_tum_id = '{z_tum_id}'
        """)
        .project("* exclude (z_tum_id)")
        .show()
    )

    print("st")
    (con.sql(f"""--sql
        select * exclude (z_kkr)
        from ST
        where z_tum_id = '{z_tum_id}'
        """)
        .project("* exclude (z_tum_id)")
        .show()
    )

    print("be")
    (con.sql(f"""--sql
        select * exclude (z_kkr)
        from Bestrahlung
        where z_tum_id = '{z_tum_id}'
        order by z_bestr_order
        """)
        .project("* exclude (z_tum_id)")
        .show()
    )

    print("app")
    (con.sql(f"""--sql
        select * exclude (z_kkr)
        from Applikationsart
        where z_tum_id = '{z_tum_id}'
        """)
        .project("* exclude (z_tum_id)")
        .show()
    )

    print("syst")
    (con.sql(f"""--sql
        select * exclude (z_kkr)
        from SYST
        where z_tum_id = '{z_tum_id}'
        order by z_syst_order
        """)
        .project("* exclude (z_tum_id)")
        .show()
    )

    print("fo")
    (con.sql(f"""--sql
        select *
        from Folgeereignis
        where z_tum_id = '{z_tum_id}'
        order by z_fo_order
        """)
        .project("* exclude (z_tum_id, z_kkr)")
        .show()
    )

    print("fo_tnm")
    (con.sql(f"""--sql
        select *
        from Folgeereignis_TNM
        where z_tum_id = '{z_tum_id}'
        """)
        .project("* exclude (z_tum_id, z_kkr)")
        .show()
    )

    print("fo_fm")
    (con.sql(f"""--sql
        select * exclude (z_kkr)
        from Folgeereignis_Fernmetastase
        where z_tum_id = '{z_tum_id}'
        """)
        .project("* exclude (z_tum_id)")
        .show()
    )

    print("fo_weitere")
    (con.sql(f"""--sql
        select * exclude (z_kkr)
        from Folgeereignis_WeitereKlassifikation
        where z_tum_id = '{z_tum_id}'
        """)
        .project("* exclude (z_tum_id)")
        .show()
    )

    print("diag_fm")
    (con.sql(f"""--sql
        select * exclude (z_kkr)
        from Diagnose_Fernmetastase
        where z_tum_id = '{z_tum_id}'
        """)
        .project("* exclude (z_tum_id)")
        .show()
    )

    print("diag_weitere")
    (con.sql(f"""--sql
        select * exclude (z_kkr)
        from Diagnose_WeitereKlassifikation
        where z_tum_id = '{z_tum_id}'
        """)
        .project("* exclude (z_tum_id)")
        .show()
    )
