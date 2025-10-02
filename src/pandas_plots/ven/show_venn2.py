import os
from datetime import datetime as dt
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib_venn import venn2, venn2_circles
from ..helper import clean_set, create_details


def show_venn2(
    title: str,
    a_set: set,
    a_label: str,
    b_set: set,
    b_label: str,
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
    a_set = clean_set(a_set)
    b_set = clean_set(b_set)

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

    return create_details(venn, venn_details_keys, verbose, max_set_len, max_line_width)