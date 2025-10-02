import numpy as np
import pandas as pd
import plotly.express as px

# * cleanse all variations of None
def clean_set(_set: set) -> set:
    return _set - set([np.nan, None, ""])


# * process venn details
def create_details(
    venn: dict,
    venn_details_keys: list,
    verbose: int,
    max_set_len: int,
    max_line_width: int,
):
    venn_details = {key: venn[key] for key in venn_details_keys}

    # * sort details by position (last item in tuple)
    venn_details = dict(sorted(venn_details.items(), key=lambda x: x[1][2]))

    # * set return string
    details = ""
    for venn_details_keys, v in venn_details.items():
        header = f"{venn_details_keys}[:{max_set_len}] --> {v[1]} --> len: {len(v[0])}\n{'-' * 30}\n"
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



def aggregate_data(
    df: pd.DataFrame,
    top_n_index: int,
    top_n_color: int,
    top_n_facet: int,
    null_label: str,
    show_other: bool = False,
    sort_values_index: bool = False,
    sort_values_color: bool = False,
    sort_values_facet: bool = False,
) -> pd.DataFrame:
    """
    Aggregates the data, ensuring each combination of 'index', 'col', and 'facet' is unique with summed 'value'.

    Args:
        df (pd.DataFrame): Input DataFrame.
        top_n_index (int): top N values of the first column to keep. 0 means take all.
        top_n_color (int): top N values of the second column to keep. 0 means take all.
        top_n_facet (int): top N values of the third column to keep. 0 means take all.
        null_label (str): Label for null values.
        show_other (bool): Whether to include "<other>" for columns not in top_n_color. Defaults to False.
        sort_values (bool): Whether to sort values in descending order based on group sum. Defaults to False.

    Returns:
        pd.DataFrame: Aggregated and filtered dataset (but not sorted!)
    """

    for col in ["index", "col", "facet"]:  # Skip 'value' column (numeric)
        df[col] = df[col].fillna(null_label)

    # Aggregate data to ensure unique combinations
    aggregated_df = df.groupby(["index", "col", "facet"], as_index=False)["value"].sum()

    # * Reduce data based on top_n parameters
    if sort_values_index:
        top_indexes = (
            aggregated_df.groupby("index")["value"]
            .sum()
            .sort_values(ascending=False)[: top_n_index or None]
            .index
        )

    else:
        top_indexes = (
            aggregated_df["index"].sort_values().unique()[: top_n_index or None]
        )

    aggregated_df = aggregated_df[aggregated_df["index"].isin(top_indexes)]

    if sort_values_color:
        top_colors = (
            aggregated_df.groupby("col")["value"]
            .sum()
            .sort_values(ascending=False)[: top_n_color or None]
            .index
        )
    else:
        top_colors = aggregated_df["col"].sort_values().unique()[: top_n_color or None]

    others_df = df[~df["col"].isin(top_colors)]
    aggregated_df = aggregated_df[aggregated_df["col"].isin(top_colors)]
    if show_other and top_n_color > 0 and not others_df.empty:
        other_agg = others_df.groupby(["index", "facet"], as_index=False)["value"].sum()
        other_agg["col"] = "<other>"
        other_agg = other_agg[["index", "col", "facet", "value"]]
        aggregated_df = pd.concat([aggregated_df, other_agg], ignore_index=True)
        top_colors = [*top_colors, "<other>"]

    if sort_values_facet:
        top_facets = (
            aggregated_df.groupby("facet")["value"]
            .sum()
            .sort_values(ascending=False)[: top_n_facet or None]
            .index
        )
    else:
        top_facets = (
            aggregated_df["facet"].sort_values().unique()[: top_n_facet or None]
        )

    aggregated_df = aggregated_df[aggregated_df["facet"].isin(top_facets)]

    return aggregated_df



def assign_column_colors(columns, color_palette, null_label):
    """
    Assigns colors to columns, with a special gray color for null values.

    Args:
        columns (list): List of column values.
        color_palette (str): Name of the color palette.
        null_label (str): Label for null values.

    Returns:
        dict: Mapping of column values to colors.
    """
    if hasattr(px.colors.qualitative, color_palette):
        palette = getattr(px.colors.qualitative, color_palette)
    else:
        raise ValueError(f"Invalid color palette: {color_palette}")

    colors = {col: palette[i % len(palette)] for i, col in enumerate(sorted(columns))}
    colors[null_label] = "lightgray"
    return colors

def set_caption(caption: str) -> str:
    return f"#{' '.join(caption.split())}, " if caption else ""
