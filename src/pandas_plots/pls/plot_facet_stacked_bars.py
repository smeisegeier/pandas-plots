import os
from pathlib import Path
from typing import Literal, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from ..hlp import *
from ..helper import set_caption, aggregate_data, assign_column_colors


def plot_facet_stacked_bars(
    df: pd.DataFrame,
    subplots_per_row: int = 4,
    top_n_index: int = 0,
    top_n_color: int = 0,
    top_n_facet: int = 0,
    null_label: str = "<NA>",
    subplot_size: int = 300,
    color_palette: str = "Plotly",
    caption: str = "",
    renderer: Optional[Literal["png", "svg", None]] = "png",
    annotations: bool = False,
    precision: int = 0,
    png_path: Optional[Path] = None,
    show_other: bool = False,
    sort_values: bool = True,
    sort_values_index: bool = False,
    sort_values_color: bool = False,
    sort_values_facet: bool = False,
    relative: bool = False,
    show_pct: bool = False,
) -> None:
    """
    A function to plot multiple (subplots_per_row) stacked bar charts, facetted by the third column, with the first column as the index and the second column as the colors.

    Parameters:
    - df (pd.DataFrame): Input DataFrame with 3 or 4 columns.
    - subplots_per_row (int): The number of subplots to display per row.
    - top_n_index (int): The number of top indexes to include in the chart. Default is 0, which includes all indexes.
    - top_n_color (int): The number of top colors to include in the chart. Default is 0, which includes all colors.
    - top_n_facet (int): The number of top facets to include in the chart. Default is 0, which includes all facets.
    - null_label (str): The label to use for null values. Default is "<NA>".
    - subplot_size (int): The size of each subplot in pixels. Default is 300.
    - color_palette (str): The name of the color palette to use. Default is "Plotly".
    - caption (str): An optional string indicating the caption for the chart.
    - renderer (str): The output format. Default is "png".
    - annotations (bool): Whether to include annotations on the chart. Default is False.
    - precision (int): The number of decimal places to round the values to. Default is 0.
    - png_path (str): The path to save the chart to, if provided.
    - show_other (bool): Whether to include "<other>" for columns not in top_n_color. Default is False.
    - sort_values (bool): Whether to sort the values in the chart. Default is True.
    - sort_values_index (bool): Whether to sort the index column. Default is False.
    - sort_values_color (bool): Whether to sort the color column. Default is False.
    - sort_values_facet (bool): Whether to sort the facet column. Default is False.
    - relative (bool): Whether to show the bars as relative values (0-1 range). Default is False.
    - show_pct (bool): Whether to show the annotations as percentages. Default is False.

    Returns: None
    """
    # ENFORCE show_pct RULES ---
    if not relative:
        # If bars are absolute, annotations MUST be absolute
        if show_pct:
            print("Warning: 'show_pct' cannot be True when 'relative' is False. Setting 'show_pct' to False.")
            show_pct = False
    #

    try:
        precision = int(precision)
    except (ValueError, TypeError):
        print(f"Warning: 'precision' received as {precision} (type: {type(precision)}). Defaulting to 0.")
        precision = 0

    df_copy = df.copy()

    if not (df_copy.shape[1] == 3 or df_copy.shape[1] == 4):
        raise ValueError("Input DataFrame must have 3 or 4 columns.")

    original_column_names = df_copy.columns.tolist()

    if df_copy.shape[1] == 3:
        df_copy.columns = ["index", "col", "facet"]
        df_copy["value"] = 1
    elif df_copy.shape[1] == 4:
        df_copy.columns = ["index", "col", "facet", "value"]

    n = df_copy["value"].sum()
    original_rows = len(df_copy)

    aggregated_df = aggregate_data(  # Assumes aggregate_data is accessible
        df_copy,
        top_n_index,
        top_n_color,
        top_n_facet,
        null_label,
        show_other=show_other,
        sort_values_index=sort_values_index,
        sort_values_color=sort_values_color,
        sort_values_facet=sort_values_facet,
    )

    aggregated_df["index"] = aggregated_df["index"].astype(str)
    aggregated_df["col"] = aggregated_df["col"].astype(str)
    aggregated_df["facet"] = aggregated_df["facet"].astype(str)

    # --- Store original 'value' for annotations before potential scaling ---
    aggregated_df["annotation_value"] = aggregated_df["value"].copy()
    # ----------------------------------------------------------------------

    if relative:
        # This transforms the bar heights (value column) to percentages (0-1 range)
        aggregated_df["value"] = aggregated_df.groupby(["facet", "index"])["value"].transform(lambda x: x / x.sum())

    category_orders = {}

    if sort_values_index:
        sum_by_index = aggregated_df.groupby("index")["value"].sum().sort_values(ascending=False)
        category_orders["index"] = sum_by_index.index.tolist()

    if sort_values_color:
        sum_by_col = aggregated_df.groupby("col")["value"].sum().sort_values(ascending=False)
        category_orders["col"] = sum_by_col.index.tolist()

    if sort_values_facet:
        sum_by_facet = aggregated_df.groupby("facet")["value"].sum().sort_values(ascending=False)
        category_orders["facet"] = sum_by_facet.index.tolist()

    columns_for_color = sorted(aggregated_df["col"].unique().tolist())
    column_colors_map = assign_column_colors(
        columns_for_color, color_palette, null_label
    )  # Assumes assign_column_colors is accessible

    #  Prepare the text series for annotations with 'show_pct' control
    if annotations:
        if show_pct:
            # When show_pct is True, use the scaled 'value' column (0-1) and format as percentage
            formatted_text_series = aggregated_df["value"].apply(lambda x: f"{x:.{precision}%}".replace(".", ","))
        else:
            # When show_pct is False, use the 'annotation_value' (original absolute) and format as absolute
            formatted_text_series = aggregated_df["annotation_value"].apply(
                lambda x: f"{x:_.{precision}f}".replace(".", ",")
            )
    else:
        formatted_text_series = None
    # - - - -

    fig = px.bar(
        aggregated_df,
        x="index",
        y="value",
        color="col",
        facet_col="facet",
        facet_col_wrap=subplots_per_row,
        barmode="stack",
        color_discrete_map=column_colors_map,
        category_orders=category_orders,
        text=formatted_text_series,
        text_auto=False,
        # height=subplot_size * (-(-len(aggregated_df["facet"].unique()) // subplots_per_row)),
        title=f"{caption} {original_column_names[0]}, {original_column_names[1]}, {original_column_names[2]}",
    )

    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

    fig.update_xaxes(matches=None)
    for axis in fig.layout:
        if axis.startswith("xaxis"):
            fig.layout[axis].showticklabels = True

    template = "plotly_dark" if os.getenv("THEME") == "dark" else "plotly"

    layout_updates = {
        "title_text": f"{caption} "
        f"{'TOP ' + str(top_n_index) + ' ' if top_n_index > 0 else ''}[{original_column_names[0]}] "
        f"{'TOP ' + str(top_n_color) + ' ' if top_n_color > 0 else ''}[{original_column_names[1]}] "
        f"{'TOP ' + str(top_n_facet) + ' ' if top_n_facet > 0 else ''}[{original_column_names[2]}] "
        f", n={original_rows:_} ({n:_})",
        "showlegend": True,
        "template": template,
        # "width": subplot_size * subplots_per_row,
    }

    if relative:
        layout_updates["yaxis_range"] = [0, 1.1]
        layout_updates["yaxis_tickformat"] = ".0%"

    fig.update_layout(**layout_updates)

    if relative:
        fig.update_yaxes(tickformat=".0%")

    fig.update_layout(
        width=subplot_size * subplots_per_row,
        height=subplot_size * (-(-len(aggregated_df["facet"].unique()) // subplots_per_row)),
    )

    if png_path:
        png_path = Path(png_path)
        fig.write_image(str(png_path))

    fig.show(
        renderer=renderer or os.getenv("RENDERER"),
        width=subplot_size * subplots_per_row,
        height=subplot_size * (-(-len(aggregated_df["facet"].unique()) // subplots_per_row)),
    )

    return
