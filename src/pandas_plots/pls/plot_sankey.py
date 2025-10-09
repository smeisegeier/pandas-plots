import os
import pandas as pd
import plotly.graph_objects as go
import re

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
    Id with missing date/events are also shown.
    Percentages are (x% | y%). x is the share of all id in total, y is the share of all id on this step

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
                                IDs with only one event, including those with missing/invalid events.
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
                "",
                "",  # Tumor 7 (Missing dates)
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
                "",
                "",  # Tumor 7 (Missing events)
                "op",  # Tumor 8
                "op",  # Tumor 9
                "syst",  # Tumor 10
                "rad",  # Tumor 11
                "op",  # Tumor 12
            ],
        }
        df = pd.DataFrame(data_demo)
        print("--- Using demo data (data_demo) ---")
        # Print all lines of the DataFrame
        print(df.to_string())
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
    
    # Track the total number of IDs before any filtering
    total_unique_ids = df_processed[id_col_name].nunique()

    # --- Handle Missing Date/Event and Coerce to <NA> Event ---
    
    # 1. Flag rows with null/empty event names
    is_event_missing = (df_processed[event_col_name].isna()) | \
                    (df_processed[event_col_name].astype(str).str.strip() == '')

    # 2. Convert date column to datetime, coercing errors to NaT
    df_processed[date_col_name] = pd.to_datetime(df_processed[date_col_name], errors='coerce')
    
    # 3. Flag rows where date could not be parsed (NaT)
    is_date_missing = df_processed[date_col_name].isna()
    
    # 4. Create a unified flag for invalid records
    is_invalid_record = is_event_missing | is_date_missing

    # 5. For invalid records, set the event name to '<NA>' and the date to a high date
    # This keeps the record, ensuring the ID is counted, but marks it clearly.
    # The date is set to NaT for sequencing to work correctly later (it will be filtered out 
    # for overlap but grouped for first event).
    df_processed.loc[is_invalid_record, event_col_name] = '<NA>'
    # Set the date for invalid records back to NaT so they are not included in sorting/overlap checks
    df_processed.loc[is_invalid_record, date_col_name] = pd.NaT 

    # --- Now we only work with records that have valid IDs and event names (<NA> is now a valid name) ---
    df_processed = df_processed.dropna(subset=[id_col_name]).copy()
    
    # If no data remains after filtering, exit early
    if df_processed.empty:
        print("No valid data to plot after filtering.")
        return None

    # --- Handle overlap exclusion based on user selection (only applies to valid date records) ---
    overlap_title_part = ""
    
    # Temporarily filter out <NA> events for overlap checks, as they don't have a valid date
    df_overlap_check = df_processed[df_processed[event_col_name] != '<NA>'].copy()
    
    if exclude_overlap_id and not df_overlap_check.empty:
        overlapping_ids = (
            df_overlap_check.groupby([id_col_name, date_col_name])
            .size()
            .loc[lambda x: x > 1]
            .index.get_level_values(id_col_name)
            .unique()
        )
        # Exclude IDs from the main dataframe
        df_processed = df_processed[
            ~df_processed[id_col_name].isin(overlapping_ids)
        ].copy()
        overlap_title_part = ", overlap ids excluded"
    elif exclude_overlap_event and not df_overlap_check.empty:
        overlapping_event_set = set(
            df_overlap_check.groupby([id_col_name, date_col_name])
            .size()
            .loc[lambda x: x > 1]
            .index
        )
        # Exclude only the overlapping date-events from the main dataframe 
        # (excluding <NA> records since they don't have a valid date)
        df_processed = df_processed[
            ~df_processed[df_processed[event_col_name] != '<NA>'].set_index([id_col_name, date_col_name]).index.isin(
                overlapping_event_set
            )
        ].copy()
        overlap_title_part = ", overlap events excluded"

    # --- Sort: Valid Date records first, then <NA> records (which have NaT) ---
    # Sorting by date naturally puts NaT (our <NA> records) at the end, which is fine
    # because event_order is calculated *after* sorting.
    df_sorted = df_processed.sort_values(by=[id_col_name, date_col_name])

    # --- Performance Optimization: Use vectorized operations instead of loops ---
    # Recalculate sequences based on remaining valid and <NA> records
    df_sorted["event_order"] = df_sorted.groupby(id_col_name).cumcount() + 1

    if max_events_per_id is not None:
        df_sorted = df_sorted[df_sorted["event_order"] <= max_events_per_id]

    df_sorted["ordered_event_label"] = (
        "[" + df_sorted["event_order"].astype(str) + "] " + df_sorted[event_col_name]
    )

    # Filter out IDs that were left with no events after sequencing (e.g., if max_events=0)
    df_sorted = df_sorted.dropna(subset=['ordered_event_label'])
    
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
    
    # Add sort key to force <NA> to the end
    unique_labels_df["event_name_sort_key"] = unique_labels_df["event_name"].apply(
        lambda x: "~Z_NA_LAST" if x == "<NA>" else x
    )

    # Sort primarily by order number, and secondarily by the custom sort key
    unique_labels_df_sorted = unique_labels_df.sort_values(
        by=["event_order_num", "event_name_sort_key"]
    )
    
    unique_unformatted_labels_sorted = unique_labels_df_sorted["label"].tolist()

    label_to_index = {
        label: i for i, label in enumerate(unique_unformatted_labels_sorted)
    }

    # Calculate node counts and step totals for percentage calculation
    node_counts = df_sorted["ordered_event_label"].value_counts()
    
    # Add count information to the DataFrame for easier calculation
    unique_labels_df_sorted['node_count'] = unique_labels_df_sorted['label'].apply(
        lambda x: total_unique_ids if x == '[0] start' else node_counts.get(x, 0)
    )

    # Calculate the total count for each step (event_order_num)
    step_totals = unique_labels_df_sorted.groupby('event_order_num')['node_count'].sum()

    # Map the step total back to the DataFrame
    unique_labels_df_sorted['step_total'] = unique_labels_df_sorted['event_order_num'].map(step_totals)

    # --- Recalculate and format display_labels with (Total % | Step %) ---
    display_labels = []
    for index, row in unique_labels_df_sorted.iterrows():
        label = row['label']
        count = row['node_count']
        step_total = row['step_total']
        
        formatted_count = f"{count:,}".replace(",", "_")
        
        # 1. Total Percentage (relative to total_unique_ids)
        total_percentage = (count / total_unique_ids) * 100
        formatted_total_percentage = f"{int(round(total_percentage, 0))}%"
        
        # 2. Step Percentage (relative to step_total)
        if label == "[0] start":
            # Step 0 is the total start, so step percentage is 100%
            formatted_step_percentage = "100%"
        elif step_total > 0:
            step_percentage = (count / step_total) * 100
            formatted_step_percentage = f"{int(round(step_percentage, 0))}%"
        else:
            formatted_step_percentage = "0%"

        formatted_percentages = f"({formatted_total_percentage} | {formatted_step_percentage})"

        display_labels.append(f"{label} {formatted_count} {formatted_percentages}")
    # --- End of display_labels recalculation ---

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
        
        # Use a distinct color for links to/from <NA>
        if "<NA>" in source_l or "<NA>" in target_l:
            link_colors.append("rgba(255, 165, 0, 0.6)") # Orange for <NA> links
        elif source_l == "[0] start":
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
    chart_title += f", n={formatted_total_ids} id ({formatted_total_rows} events)"

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
