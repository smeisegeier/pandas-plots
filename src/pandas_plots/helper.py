import numpy as np
import pandas as pd
import plotly.express as px

from .const import OTHER_LABEL


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
        show_other (bool): Whether to include "(other)" for columns not in top_n_color. Defaults to False.
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
            aggregated_df.groupby("index")["value"].sum().sort_values(ascending=False)[: top_n_index or None].index
        )

    else:
        top_indexes = aggregated_df["index"].sort_values().unique()[: top_n_index or None]

    aggregated_df = aggregated_df[aggregated_df["index"].isin(top_indexes)]

    if sort_values_color:
        top_colors = (
            aggregated_df.groupby("col")["value"].sum().sort_values(ascending=False)[: top_n_color or None].index
        )
    else:
        top_colors = aggregated_df["col"].sort_values().unique()[: top_n_color or None]

    others_df = df[~df["col"].isin(top_colors)]
    aggregated_df = aggregated_df[aggregated_df["col"].isin(top_colors)]
    if show_other and top_n_color > 0 and not others_df.empty:
        other_agg = others_df.groupby(["index", "facet"], as_index=False)["value"].sum()
        other_agg["col"] = OTHER_LABEL
        other_agg = other_agg[["index", "col", "facet", "value"]]
        aggregated_df = pd.concat([aggregated_df, other_agg], ignore_index=True)
        top_colors = [*top_colors, OTHER_LABEL]

    if sort_values_facet:
        top_facets = (
            aggregated_df.groupby("facet")["value"].sum().sort_values(ascending=False)[: top_n_facet or None].index
        )
    else:
        top_facets = aggregated_df["facet"].sort_values().unique()[: top_n_facet or None]

    aggregated_df = aggregated_df[aggregated_df["facet"].isin(top_facets)]

    return aggregated_df


def assign_column_colors(columns, color_palette, null_label, first_col_grey=False, sort_columns=True):
    """
    Assigns colors to columns, with a special gray color for null values.

    Args:
        columns (list): List of column values.
        color_palette (str | list[str]): Name of the color palette or list of color codes.
            - 🎨 Plotly names: `D3`, `Pastel`, `Dark24`, `Light24`, `Plotly`
            - Example: `const.PALETTE_RKI1`, `const.PALETTE_RKI2`, `const.PALETTE_SANKEY_LINK`
        null_label (str): Label for null values.
        first_col_grey (bool): If True, assigns lightgray to the first column in the ordering.
        sort_columns (bool): If True, sorts columns alphabetically before assigning colors. Default is True for backward compatibility.

    Returns:
        dict: Mapping of column values to colors.
    """
    if isinstance(color_palette, list):
        palette = color_palette
    elif hasattr(px.colors.qualitative, color_palette):
        palette = getattr(px.colors.qualitative, color_palette)
    else:
        raise ValueError(f"Invalid color palette: {color_palette}")

    sorted_cols = sorted(columns) if sort_columns else columns
    colors = {}
    palette_index = 0
    for i, col in enumerate(sorted_cols):
        if (first_col_grey and i == 0) or col == null_label:
            colors[col] = "lightgray"
        else:
            colors[col] = palette[palette_index % len(palette)]
            palette_index += 1
    colors[null_label] = "lightgray"
    return colors


def set_caption(caption: str) -> str:
    return f"{' '.join(caption.split())}, " if caption else ""


def group_kkr(df: pd.DataFrame, kkr_col: str) -> pd.DataFrame:
    """
    Groups and counts a DataFrame by kkr_col and other_col (row count only).
    It preserves all non-zero counts and inserts zero-count placeholders
    for missing KKR categories.

    FIX: Explicitly converts NaN in other_col to '<NA>' string *before* grouping.

    Args:
        df (pd.DataFrame): The input DataFrame.
        kkr_col (str): The name of the column containing the KKR items.

    Returns:
        pd.DataFrame: A new DataFrame with columns [kkr_col, other_col, 'cnt'].
    """

    # Define constants
    NA_CATEGORY_STR = "(NA)"
    MASTER_KKR_CATEGORIES = [
        "01-SH",
        "02-HH",
        "03-NI",
        "04-HB",
        "05-NW",
        "06-HE",
        "07-RP",
        "08-BW",
        "09-BY",
        "10-SL",
        "11-BE",
        "12-BB",
        "13-MV",
        "14-SN",
        "15-ST",
        "16-TH",
    ]

    # --- 1. Validation and Column Identification ---
    df_processed = df.copy()  # Work on a copy
    if kkr_col not in df_processed.columns:
        raise ValueError(f"Column '{kkr_col}' not found in the DataFrame.")

    # Identify the single mandatory other_col
    other_cols_potential = [c for c in df_processed.columns if c != kkr_col]
    type_cols = [c for c in other_cols_potential if not pd.api.types.is_numeric_dtype(df_processed[c])]

    if len(type_cols) == 0:
        raise ValueError("The DataFrame must contain at least one other non-numeric column (other_col).")
    other_col: str = type_cols[0]

    # --- 2. CRITICAL FIX: Standardize other_col before Grouping ---
    # This prevents the '05-NW | NaN | 351' group from being dropped or misinterpreted.
    df_processed[other_col] = df_processed[other_col].fillna(NA_CATEGORY_STR)

    # --- 3. Grouping and Aggregation (Row Count Only) ---
    group_by_cols = [kkr_col, other_col]

    if df_processed.empty:
        grouped_df = pd.DataFrame(columns=[kkr_col, other_col, "cnt"])
    else:
        # Simple row count (size())
        grouped_df = df_processed.groupby(group_by_cols).size().reset_index(name="cnt")

    # --- 4. Identify and Add Missing KKR Categories ---

    # Identify KKR categories present in the grouped data
    present_all_kkr = grouped_df[kkr_col].unique()
    present_master_kkr = [k for k in present_all_kkr if k in MASTER_KKR_CATEGORIES]

    # Identify KKR categories that are truly missing
    missing_kkr = [k for k in MASTER_KKR_CATEGORIES if k not in present_master_kkr]

    # Create placeholder rows for missing KKR (KKR, '<NA>', 0)
    if missing_kkr:
        missing_df = pd.DataFrame(
            {kkr_col: missing_kkr, other_col: [NA_CATEGORY_STR] * len(missing_kkr), "cnt": [0] * len(missing_kkr)}
        )
        missing_df["cnt"] = missing_df["cnt"].astype(int)

        result_df = pd.concat([grouped_df, missing_df], ignore_index=True)
    else:
        result_df = grouped_df.copy()

    # --- 5. Final Cleanup ---
    final_cols = [kkr_col, other_col, "cnt"]

    # Final type conversion and column order
    result_df["cnt"] = result_df["cnt"].astype(int)

    if not result_df.empty:
        result_df = result_df[final_cols]

    return result_df
