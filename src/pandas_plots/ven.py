import os
from datetime import datetime as dt
# from typing import Literal
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib_venn import venn2, venn2_circles, venn3, venn3_circles

# * cleanse all variations of None
def _clean_set(_set: set) -> set:
    return _set - set([np.nan, None, ""])

# * process venn details
def _create_details(venn: dict, venn_details_keys: list, verbose: int, max_set_len: int, max_line_width: int):
    venn_details = {key: venn[key] for key in venn_details_keys}

    # * sort details by position (last item in tuple)
    venn_details = dict(sorted(venn_details.items(), key=lambda x: x[1][2]))

    # * set return string
    details = ""
    for venn_details_keys, v in venn_details.items():
        header = f'{venn_details_keys}[:{max_set_len}] --> {v[1]} --> len: {len(v[0])}\n{"-"*30}\n'
        print(header) if verbose > 0 else None
        details += header

        # * unpack tuple as string
        text = sorted(v[0])[:max_set_len].__str__()
        # * loop through chunks of n characters and print
        for i in range(0, len(text), max_line_width):
            chunk = text[i : i + max_line_width]
            print(f"{chunk}") if verbose > 0 else None
        print("\n") if verbose > 0 else None
        details += text + "\n" + "\n"

    # * create df from subsets
    df = (
        pd.DataFrame(venn["ab"][0], columns=["all"])
        .merge(
            pd.DataFrame(venn["a"][0], columns=[venn["a"][1]]),
            left_on="all",
            right_on=venn["a"][1],
            how="left",
        )
        .merge(
            pd.DataFrame(venn["b"][0], columns=[venn["b"][1]]),
            left_on="all",
            right_on=venn["b"][1],
            how="left",
        )
    )
    return df, details

def show_venn3(
    title: str,
    a_set: set,
    a_label: str,
    b_set: set,
    b_label: str,
    c_set: set,
    c_label: str,
    max_set_len: int = 100,
    max_line_width: int = 120,
    alpha: float = 0.7,
    size: int = 15,
    show_percent_values: bool = True,
    verbose: int = 0,
) -> pd.DataFrame:
    """
    Generates a Venn diagram with three sets and returns a DataFrame with the subsets.

    Args:
        title (str): The title of the Venn diagram.
        a_set (set): The first set.
        a_label (str): The label for the first set.
        b_set (set): The second set.
        b_label (str): The label for the second set.
        c_set (set): The third set.
        c_label (str): The label for the third set.
        max_set_len (int, optional): The maximum number of elements to display for each set. Defaults to 100.
        max_line_width (int, optional): The maximum width of each line when displaying set elements. Defaults to 120.
        alpha (float, optional): The transparency of the plot. Defaults to 0.7.
        size (int, optional): The size of the plot. Defaults to 15.
        show_percent_values (bool, optional): Whether to display the percentage values in the subset labels. Defaults to True.
        verbose (int, optional): Verbosity level.
            0: silent
            1: print details

    Returns:
        pd.DataFrame: A DataFrame containing the subsets of the three sets.
        str: Details of the Venn diagram

    """

    # * set theme
    plt.style.use("dark_background" if os.environ.get("THEME") == "dark" else "classic")

    # * dropna, this is not optional since it may raise errors in set operations
    a_set = _clean_set(a_set)
    b_set = _clean_set(b_set)
    c_set = _clean_set(c_set)

    # * load dict
    venn = {
        "a": (a_set, a_label, 1),
        "b": (b_set, b_label, 2),
        "c": (c_set, c_label, 3),
    }

    # * create set math
    venn.update(
        {
            # * item
            "Abc": (
                # * set
                venn["a"][0] - venn["b"][0] - venn["c"][0],
                # * label
                f"{venn['a'][1]} - {venn['b'][1]} - {venn['c'][1]}",
                # * position
                16,
            ),
            "aBc": (
                venn["b"][0] - venn["a"][0] - venn["c"][0],
                f"{venn['b'][1]} - {venn['a'][1]} - {venn['c'][1]}",
                17,
            ),
            "ABc": (
                (venn["a"][0] & venn["b"][0]) - venn["c"][0],
                f"({venn['a'][1]} & {venn['b'][1]}) - {venn['c'][1]}",
                18,
            ),
            "abC": (
                venn["c"][0] - venn["a"][0] - venn["b"][0],
                f"{venn['c'][1]} - {venn['a'][1]} - {venn['b'][1]}",
                19,
            ),
            "AbC": (
                (venn["a"][0] & venn["c"][0]) - venn["b"][0],
                f"({venn['a'][1]} & {venn['c'][1]}) - {venn['b'][1]}",
                20,
            ),
            "aBC": (
                (venn["b"][0] & venn["c"][0]) - venn["a"][0],
                f"({venn['b'][1]} & {venn['c'][1]}) - {venn['a'][1]}",
                21,
            ),
            "ABC": (
                (venn["a"][0] & venn["b"][0] & venn["c"][0]),
                f"({venn['a'][1]} & {venn['b'][1]} & {venn['c'][1]})",
                22,
            ),
            "ab": (venn["a"][0] | venn["b"][0], f"{venn['a'][1]} | {venn['b'][1]}", 4),
            "bc": (venn["b"][0] | venn["c"][0], f"{venn['b'][1]} | {venn['c'][1]}", 5),
            "ac": (venn["a"][0] | venn["c"][0], f"{venn['a'][1]} | {venn['c'][1]}", 6),
            "abc": (
                venn["a"][0] | venn["b"][0] | venn["c"][0],
                f"{venn['a'][1]} | {venn['b'][1]} | {venn['c'][1]}",
                23,
            ),
            "Ab": (venn["a"][0] - venn["b"][0], f"{venn['a'][1]} - {venn['b'][1]}", 7),
            "aB": (venn["b"][0] - venn["a"][0], f"{venn['b'][1]} - {venn['a'][1]}", 8),
            "Ac": (venn["a"][0] - venn["c"][0], f"{venn['a'][1]} - {venn['c'][1]}", 9),
            "aC": (venn["c"][0] - venn["a"][0], f"{venn['c'][1]} - {venn['a'][1]}", 10),
            "Bc": (venn["b"][0] - venn["c"][0], f"{venn['b'][1]} - {venn['c'][1]}", 11),
            "bC": (venn["c"][0] - venn["b"][0], f"{venn['c'][1]} - {venn['b'][1]}", 12),
            "AB": (venn["a"][0] & venn["b"][0], f"{venn['a'][1]} & {venn['b'][1]}", 13),
            "AC": (venn["a"][0] & venn["c"][0], f"{venn['a'][1]} & {venn['c'][1]}", 14),
            "BC": (venn["b"][0] & venn["c"][0], f"{venn['b'][1]} & {venn['c'][1]}", 15),
        }
    )

    # * (Abc, aBc, ABc, abC, AbC, aBC, ABC)
    subsets = (
        len(venn["Abc"][0]),
        len(venn["aBc"][0]),
        len(venn["ABc"][0]),
        len(venn["abC"][0]),
        len(venn["AbC"][0]),
        len(venn["aBC"][0]),
        len(venn["ABC"][0]),
    )

    # * plot params
    plt.figure(figsize=(size, size))
    plt.title(f"{title} | {dt.date(dt.now())}")

    # * include %?
    if show_percent_values:
        subset_label_formatter = lambda x: f'{x}({x/len(venn["abc"][0]):.0%})'
    else:
        subset_label_formatter = lambda x: f"{x}"

    venn3(
        subsets=subsets,
        set_labels=(
            # * label(len)
            f"a: {venn['a'][1]}({len(venn['a'][0])})",
            f"b: {venn['b'][1]}({len(venn['b'][0])})",
            f"c: {venn['c'][1]}({len(venn['c'][0])})",
        ),
        set_colors=("orange", "blue", "green"),
        alpha=alpha,
        subset_label_formatter=subset_label_formatter,
    )

    venn3_circles(
        subsets=subsets,
        # linestyle='dashed',
        linewidth=0.7,
    )

    # * define subset for summary
    venn_summary = {key: venn[key] for key in (["abc", "ab", "ac", "bc"])}

    # * print summary
    for venn_details_keys, v in venn_summary.items():
        print(f"{venn_details_keys} --> {v[1]} --> len: {len(v[0])}")

    # * show venn diagram
    plt.show()

    # * define subset for details
    venn_details_keys = sorted(set(venn.keys()) - set(["abc", "ab", "ac", "bc"]))

    return _create_details(venn, venn_details_keys, verbose, max_set_len, max_line_width)


def show_venn2(
    title: str,
    a_set: set,
    a_label: str,
    b_set: set,
    b_label: str,
    # theme: Literal["light", "dark"] = "dark",
    max_set_len: int = 100,
    max_line_width: int = 120,
    alpha: float = 0.7,
    size: int = 15,
    show_percent_values: bool = True,
    verbose: int = 0,
) -> pd.DataFrame:
    """
    Generates a Venn diagram with two sets and returns a DataFrame with the subsets.

    Args:
        title (str): The title of the Venn diagram.
        a_set (set): The first set.
        a_label (str): The label for the first set.
        b_set (set): The second set.
        b_label (str): The label for the second set.
        max_set_len (int, optional): The maximum number of elements to display for each set. Defaults to 100.
        max_line_width (int, optional): The maximum width of each line when displaying set elements. Defaults to 120.
        alpha (float, optional): The transparency of the plot. Defaults to 0.7.
        size (int, optional): The size of the plot. Defaults to 15.
        show_percent_values (bool, optional): Whether to display the percentage values in the subset labels. Defaults to True.
        verbose (int, optional): Verbosity level.
            0: silent
            1: print details

    Returns:
        pd.DataFrame: A DataFrame containing the subsets of the three sets.
        str: Details of the Venn diagram
    """

    # * set theme
    plt.style.use("dark_background" if os.environ.get("THEME") == "dark" else "classic")

    # * dropna, this is not optional since it may raise errors in set operations
    a_set = _clean_set(a_set)
    b_set = _clean_set(b_set)

    # * load dict
    venn = {
        "a": (a_set, a_label, 1),
        "b": (b_set, b_label, 2),
    }

    # * create set math
    venn.update(
        {
            # * item
            "Ab": (
                # * set
                venn["a"][0] - venn["b"][0],
                # * label
                f"{venn['a'][1]} - {venn['b'][1]}",
                # * position
                16,
            ),
            "aB": (venn["b"][0] - venn["a"][0], f"{venn['b'][1]} - {venn['a'][1]}", 17),
            "AB": (
                (venn["a"][0] & venn["b"][0]),
                f"({venn['a'][1]} & {venn['b'][1]})",
                22,
            ),
            "ab": (venn["a"][0] | venn["b"][0], f"{venn['a'][1]} | {venn['b'][1]}", 22),
        }
    )

    subsets = (
        len(venn["Ab"][0]),
        len(venn["aB"][0]),
        len(venn["AB"][0]),
    )

    # * plot params
    plt.figure(figsize=(size, size))
    plt.title(f"{title} | {dt.date(dt.now())}")

    # * include %?
    if show_percent_values:
        subset_label_formatter = lambda x: f'{x}({x/len(venn["ab"][0]):.0%})'
    else:
        subset_label_formatter = lambda x: f"{x}"

    venn2(
        subsets=subsets,
        set_labels=(
            # * label(len)
            f"a: {venn['a'][1]}({len(venn['a'][0])})",
            f"b: {venn['b'][1]}({len(venn['b'][0])})",
        ),
        set_colors=("orange", "blue", "green"),
        alpha=alpha,
        subset_label_formatter=subset_label_formatter,
    )

    venn2_circles(
        subsets=subsets,
        # linestyle='dashed',
        linewidth=0.7,
    )

    # * define subset for summary
    venn_summary = {key: venn[key] for key in (["ab"])}

    # * print summary
    for venn_details_keys, v in venn_summary.items():
        print(f"{venn_details_keys} --> {v[1]} --> len: {len(v[0])}")

    # * show venn diagram
    plt.show()

    # * define subset for details
    venn_details_keys = sorted(set(venn.keys()) - set(["ab"]))

    return _create_details(venn, venn_details_keys, verbose, max_set_len, max_line_width)
