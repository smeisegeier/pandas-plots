from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
import re
from ..hlp import *


def plot_sankey(
    df=None,
    max_events_per_id=None,
    height=None,
    width=None,
    exclude_overlap_id=False,
    exclude_overlap_event=False,
    renderer=None,
    show_start_node=True,
    font_size=10,
):
    """
    Generates a Sankey diagram from a Pandas DataFrame, assuming the column order is:
    1. ID (string or integer)
    2. Date (date, datetime, or string convertible to numeric)
    3. Event Name (string)

    Nodes represent the order of events (e.g., "[1] op", "[2] syst").
    A default demo is shown if no DataFrame is provided.

    Args:
        df (pd.DataFrame, optional): A Pandas DataFrame containing the event data.
                        Expected column order: ID, Date, Event.
        max_events_per_id (int, optional): The maximum number of events to display for each ID.
                                        If None, all events for each ID will be used.
        height (int, optional): The height of the plot in pixels.
        width (int, optional): The width of the plot in pixels.
        exclude_overlap_id (bool): If True, excludes any IDs that have multiple events on the same date.
                                This takes precedence over `exclude_overlap_event`.
        exclude_overlap_event (bool): If True, only excludes the specific events that fall on the same date,
                                    retaining other non-overlapping events for that ID.
        renderer (str, optional): The renderer to use for displaying the plot. Options include
                                'browser', None, 'json', 'png', 'svg', 'jpeg', 'webp', or 'pdf'.
                                If None, plotly's default renderer is used.
        show_start_node (bool): If True, adds a visual 'start' node and links all
                                first events to it. This is useful for visualizing
                                IDs with only one event.
        font_size (int): The font size of the labels in the plot.
    """
    # --- Example Usage with Enlarged Pandas DataFrame if no DataFrame is provided ---
    if df is None:
        data_demo = {  # Renamed to data_demo for clarity
            "tumor-id": [
                "1",
                "1",
                "1",
                "1",
                "1",
                "2",
                "2",
                "2",
                "2",
                "3",
                "3",
                "3",
                "3",
                "4",
                "4",
                "4",
                "5",
                "5",
                "6",
                "6",
                "7",
                "7",
                "8",
                "9",
                "10",
                "11",
                "12",
            ],
            "diagnosis date": [
                "2020-01-01",
                "2021-02-01",
                "2022-03-01",
                "2023-04-01",
                "2024-05-01",  # Tumor 1
                "2010-01-01",
                "2011-02-01",
                "2012-03-01",
                "2013-04-01",  # Tumor 2
                "2015-01-01",
                "2016-02-01",
                "2017-03-01",
                "2018-04-01",  # Tumor 3
                "2005-01-01",
                "2006-02-01",
                "2007-03-01",  # Tumor 4
                "2019-01-01",
                "2020-02-01",  # Tumor 5
                "2021-01-01",
                "2022-02-01",  # Tumor 6
                "2014-01-01",
                "2015-02-01",  # Tumor 7
                "2025-01-01",  # Tumor 8 (single event)
                "2025-02-01",  # Tumor 9 (single event)
                "2025-03-01",  # Tumor 10 (single event)
                "2025-04-01",  # Tumor 11 (single event)
                "2025-05-01",  # Tumor 12 (single event)
            ],
            "treatment": [
                "op",
                "syst",
                "op",
                "rad",
                "op",  # Tumor 1
                "syst",
                "st",
                "op",
                "rad",  # Tumor 2
                "op",
                "rad",
                "syst",
                "op",  # Tumor 3
                "st",
                "syst",
                "op",  # Tumor 4
                "op",
                "rad",  # Tumor 5
                "syst",
                "op",  # Tumor 6
                "st",
                "rad",  # Tumor 7
                "op",  # Tumor 8
                "op",  # Tumor 9
                "syst",  # Tumor 10
                "rad",  # Tumor 11
                "op",  # Tumor 12
            ],
        }
        df = pd.DataFrame(data_demo)
        print("--- Using demo data (data_demo) ---")
        print(df.head().to_string())  # Print first 5 rows of the DataFrame prettily
        print("-----------------------------------")

    # --- Simplified Column Recognition based on index ---
    id_col_name = df.columns[0]
    date_col_name = df.columns[1]
    event_col_name = df.columns[2]

    df_processed = df.copy()

    # --- Aggregate the data to remove duplicate rows before processing ---
    df_processed = df_processed.drop_duplicates(
        subset=[id_col_name, date_col_name, event_col_name]
    )

    try:
        df_processed[date_col_name] = pd.to_datetime(df_processed[date_col_name])
    except (ValueError, TypeError):
        print(
            f"Error: Could not convert column '{date_col_name}' to a valid date format."
        )
        return None

    # --- Handle overlap exclusion based on user selection ---
    overlap_title_part = ""
    if exclude_overlap_id:
        overlapping_ids = (
            df_processed.groupby([id_col_name, date_col_name])
            .size()
            .loc[lambda x: x > 1]
            .index.get_level_values(id_col_name)
            .unique()
        )
        df_processed = df_processed[
            ~df_processed[id_col_name].isin(overlapping_ids)
        ].copy()
        overlap_title_part = ", overlap ids excluded"
    elif exclude_overlap_event:
        overlapping_event_set = set(
            df_processed.groupby([id_col_name, date_col_name])
            .size()
            .loc[lambda x: x > 1]
            .index
        )
        df_processed = df_processed[
            ~df_processed.set_index([id_col_name, date_col_name]).index.isin(
                overlapping_event_set
            )
        ].copy()
        overlap_title_part = ", overlap events excluded"

    df_sorted = df_processed.sort_values(by=[id_col_name, date_col_name])

    # --- Performance Optimization: Use vectorized operations instead of loops ---
    df_sorted["event_order"] = df_sorted.groupby(id_col_name).cumcount() + 1

    if max_events_per_id is not None:
        df_sorted = df_sorted[df_sorted["event_order"] <= max_events_per_id]

    df_sorted["ordered_event_label"] = (
        "[" + df_sorted["event_order"].astype(str) + "] " + df_sorted[event_col_name]
    )

    if df_sorted.empty:
        print("No valid data to plot after filtering.")
        return None

    # Use a vectorized shift operation to create source and target columns
    df_sorted["source_label"] = df_sorted.groupby(id_col_name)[
        "ordered_event_label"
    ].shift(1)
    df_with_links = df_sorted.dropna(subset=["source_label"]).copy()

    # Create the start node and links if enabled
    if show_start_node:
        first_events = df_sorted.groupby(id_col_name).first().reset_index()
        first_events["source_label"] = "[0] start"
        df_with_links = pd.concat(
            [
                first_events[["source_label", "ordered_event_label"]],
                df_with_links[["source_label", "ordered_event_label"]],
            ],
            ignore_index=True,
        )

    link_counts = (
        df_with_links.groupby(["source_label", "ordered_event_label"])
        .size()
        .reset_index(name="value")
    )

    # Get all unique nodes for the labels and sorting
    all_labels = pd.concat(
        [link_counts["source_label"], link_counts["ordered_event_label"]]
    ).unique()
    unique_labels_df = pd.DataFrame(all_labels, columns=["label"])
    unique_labels_df["event_order_num"] = (
        unique_labels_df["label"].str.extract(r"\[(\d+)\]").astype(float).fillna(0)
    )
    unique_labels_df["event_name"] = (
        unique_labels_df["label"].str.extract(r"\] (.*)").fillna("start")
    )
    unique_labels_df_sorted = unique_labels_df.sort_values(
        by=["event_order_num", "event_name"]
    )
    unique_unformatted_labels_sorted = unique_labels_df_sorted["label"].tolist()

    label_to_index = {
        label: i for i, label in enumerate(unique_unformatted_labels_sorted)
    }

    # Calculate total unique IDs for percentage calculation
    total_unique_ids = df_processed[id_col_name].nunique()

    display_labels = []
    node_counts = df_sorted["ordered_event_label"].value_counts()
    for label in unique_unformatted_labels_sorted:
        if label == "[0] start":
            count = total_unique_ids
        else:
            count = node_counts.get(label, 0)

        percentage = (count / total_unique_ids) * 100
        formatted_count = f"{count:,}".replace(",", "_")
        formatted_percentage = f"({int(round(percentage, 0))}%)"

        display_labels.append(f"{label} {formatted_count} {formatted_percentage}")

    # Map sources and targets to indices
    sources = link_counts["source_label"].map(label_to_index).tolist()
    targets = link_counts["ordered_event_label"].map(label_to_index).tolist()
    values = link_counts["value"].tolist()

    # Define a color palette for links
    color_palette = [
        "rgba(255, 99, 71, 0.6)",
        "rgba(60, 179, 113, 0.6)",
        "rgba(65, 105, 225, 0.6)",
        "rgba(255, 215, 0, 0.6)",
        "rgba(147, 112, 219, 0.6)",
        "rgba(0, 206, 209, 0.6)",
        "rgba(255, 160, 122, 0.6)",
        "rgba(124, 252, 0, 0.6)",
        "rgba(30, 144, 255, 0.6)",
        "rgba(218, 165, 32, 0.6)",
    ]
    start_link_color = "rgba(128, 128, 128, 0.6)"

    link_colors = []
    link_type_to_color = {}
    color_index = 0
    for i, row in link_counts.iterrows():
        source_l = row["source_label"]
        target_l = row["ordered_event_label"]
        if source_l == "[0] start":
            link_colors.append(start_link_color)
        else:
            source_event_name = re.search(r"\] (.*)", source_l).group(1)
            target_event_name = re.search(r"\] (.*)", target_l).group(1)
            link_type = (source_event_name, target_event_name)

            if link_type not in link_type_to_color:
                link_type_to_color[link_type] = color_palette[
                    color_index % len(color_palette)
                ]
                color_index += 1
            link_colors.append(link_type_to_color[link_type])

    formatted_total_ids = f"{total_unique_ids:,}".replace(",", "_")
    total_rows = len(df_processed)
    formatted_total_rows = f"{total_rows:,}".replace(",", "_")

    chart_title = f"[{id_col_name}] over [{event_col_name}]"
    if max_events_per_id is not None:
        chart_title += f", top {max_events_per_id} events"
    chart_title += overlap_title_part
    chart_title += f", n={formatted_total_ids} ({formatted_total_rows})"

    fig = go.Figure(
        data=[
            go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=display_labels,
                    color="blue",
                    align="left",
                ),
                link=dict(
                    source=sources, target=targets, value=values, color=link_colors
                ),
            )
        ]
    )


    fig.update_layout(title_text=chart_title, font_size=font_size, width=width, height=height)
    fig.show(renderer=renderer or os.getenv("RENDERER"), width=width, height=height)