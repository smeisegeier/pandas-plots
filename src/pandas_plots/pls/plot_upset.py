from typing import Literal

import pandas as pd
from upsetplot import plot as upset


def plot_upset(
    data: pd.Series | pd.DataFrame,
    show_percentages: bool = True,
    sort_by: Literal["cardinality", "degree", "input", "-cardinality", "-degree", "-input"] = "cardinality",
    sort_categories_by: Literal["cardinality", "input", "-cardinality", "-input"] = "cardinality",
    orientation: Literal["horizontal", "vertical"] = "horizontal",
    include_false_subsets: bool = True,
    # include_empty_subsets: bool = False,
    size: int = 45,
    totals_plot_elements: int = 5,
    intersection_plot_elements: int = 5,
    max_degree: int = 30,
    min_subset_size: str = None,
    max_subset_size: str = None,
    max_subset_rank=30,
    # sum_over: str = None,
    show_n: bool = True,
) -> None:
    """
    Plot the upset plot of the given data.

    Uses this great package: https://github.com/jnothman/UpSetPlot

    Parameters:
    - data: a pandas Series or DataFrame
    - show_percentages: a boolean indicating whether to show percentages in the plot
    - sort_by: a Literal indicating the sorting order for the plot
    - sort_categories_by: a Literal indicating the sorting order for the categories
    - orientation: a Literal indicating the orientation of the plot
    - include_false_subsets: a boolean indicating whether to include false subsets in the plot
    - size: an integer indicating the size of each element in the plot
    - totals_plot_elements: an integer indicating the maximum number of elements to plot in the totals plot
    - intersection_plot_elements: an integer indicating the maximum number of elements to plot in the intersection plot
    - max_degree: an integer indicating the maximum degree of the subsets to plot
    - min_subset_size: a string indicating the minimum size of the subsets to plot (eg "10%")
    - max_subset_size: a string indicating the maximum size of the subsets to plot (eg "50%")
    - max_subset_rank: an integer indicating the maximum rank of the subsets to plot
    - show_n: a boolean indicating whether to show the number of elements in the plot

    Returns:
    None
    """
    # * 1. Check for correct data type first
    if not isinstance(data, (pd.Series, pd.DataFrame)):
        print("❌ Error: Data must be a pandas Series or DataFrame.")
        return

    n1 = len(data)

    # if not include_empty_subsets:
    #     data = data.dropna()
    # n2 = len(data)

    if not include_false_subsets:
        data = data[data.any(axis=1)]
    n3 = len(data)

    df_out = data.groupby(data.columns.to_list()).size()
    n4 = sum(df_out)

    n_str = (
        f"n = {n1:_}"
        # + (f" | n(nonempty) = {n2:_}" if not include_empty_subsets else "")
        + (f" | n(true) = {n3:_}" if not include_false_subsets else "")
        + (f" | n(nonempty) = {n4:_}" if n4 != n3 else "")
    )

    if show_n:
        print(n_str)

    _ = upset(
        df_out,
        orientation=orientation,
        show_counts=True,
        show_percentages=show_percentages,
        element_size=size,
        sort_by=sort_by,
        sort_categories_by=sort_categories_by,
        # include_empty_subsets=include_empty_subsets,
        totals_plot_elements=totals_plot_elements,
        intersection_plot_elements=intersection_plot_elements,
        max_degree=max_degree,
        # sum_over=sum_over,
        min_subset_size=min_subset_size,
        max_subset_size=max_subset_size,
        max_subset_rank=max_subset_rank,
    )
