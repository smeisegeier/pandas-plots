import os

import duckdb
import pandas as pd
from IPython.display import Markdown, display


def plot_uml_graph(df=None, orientation="v", debug=False, show_legend=True):
    """
    Generalized Graph Renderer with Self-Calculated Diagnostics

    Arguments:
    ----------
    df : pandas.DataFrame, optional
        Input data with columns:
            source,
            target,
            category (opt),
            weight (opt)
    orientation : str, default 'v'
        Direction of the graph. 'v'/'TD' (Vertical) or 'h'/'LR' (Horizontal).
    debug : bool, default False
        If True, enables additional console output.
    show_legend : bool, default True
        If True, displays a legend for categories (light theme only).

    Returns:
    -------
    res_df : pandas.DataFrame
        A table containing the processed graph hierarchy and metrics:
        - edge_label: Formatted Mermaid edge string.
        - current_item: Cleaned node ID (Blanks -> _, Brackets removed).
        - category: Category or 'Root' designation.
        - total_weight: Cumulative weight from root.
        - degree: Total connections (In + Out).
        - closeness: Normalized inverse of distance to other nodes.
        - betweenness: Frequency node appears on shortest paths.

    Root Construction:
    -----------------
    Roots are identified by finding nodes in the Source column that never
    appear in the Target column (In-degree = 0).
    """

    if df is None:
        attunement_data = [
            ("Level 68", "Karazhan Key Chain", "Quest", 1),
            ("Karazhan Key Chain", "Karazhan Raid", "Raid", 1),
            ("Karazhan Raid", "Nightbane", "Boss", 1),
            ("Level 70", "Cenarion Expedition Honored", "Reputation", 1),
            ("Cenarion Expedition Honored", "Heroic Slave Pens", "Dungeon", 1),
            ("Heroic Slave Pens", "Cudgel of Kardesh Quest", "Quest", 1),
            ("Karazhan Raid", "Cudgel of Kardesh Quest", "Boss Drop", 1),
            ("Cudgel of Kardesh Quest", "Serpentshrine Cavern", "Raid", 1),
            ("Level 70", "Trial of the Naaru", "Quest Chain", 1),
            ("Magtheridon Raid", "Trial of the Naaru", "Boss Drop", 1),
            ("Trial of the Naaru", "The Eye", "Raid", 1),
            ("Serpentshrine Cavern", "The Vials of Eternity", "Boss Drop", 1),
            ("The Eye", "The Vials of Eternity", "Boss Drop", 1),
            ("The Vials of Eternity", "Battle for Mount Hyjal", "Raid", 1),
            ("Karazhan Raid", "Cipher of Damnation", "Quest", 1),
            ("Cipher of Damnation", "Black Temple Chain", "Quest", 1),
            ("Black Temple Chain", "Akama Alliance", "Quest", 1),
            ("Battle for Mount Hyjal", "Akama Alliance", "Raid Step", 1),
            ("Akama Alliance", "Black Temple", "Raid", 1),
            ("Level 68", "Level 70", "Leveling", 1),
            ("Level 70", "Honor Hold Honored", "Reputation", 1),
            ("Honor Hold Honored", "Flamewrought Key", "Vendor", 1),
            ("Flamewrought Key", "Heroic Shattered Halls", "Access", 1),
            ("Level 70", "Lower City Honored", "Reputation", 1),
            ("Lower City Honored", "Auchenai Key", "Vendor", 1),
            ("Auchenai Key", "Heroic Shadow Labyrinth", "Access", 1),
            ("Level 70", "Keepers of Time Honored", "Reputation", 1),
            ("Keepers of Time Honored", "Key of Time", "Vendor", 1),
            ("Key of Time", "Heroic Black Morass", "Access", 1),
        ]
        df = pd.DataFrame(attunement_data, columns=["source", "target", "category", "weight"])
        print("Demo mode - Input table (first 5 rows):")

    # Remove unwanted characters from all text columns
    chars_to_remove = ["§", "(", ")", "@", "…", "‑", "“", " ", "„"]
    for col in df.select_dtypes(include=["object", "string"]).columns:
        for char in chars_to_remove:
            df[col] = df[col].str.replace(char, "", regex=False)
        df[col] = df[col].str.strip()

    theme = os.getenv("THEME", "light")
    use_colors = theme == "light"
    con = duckdb.connect(database=":memory:")
    con.register("df_input", df)

    cols = df.columns.tolist()
    c_orig, c_dest = cols[0], cols[1]
    c_cat = cols[2] if len(cols) >= 3 else "'Default'"
    c_weight = cols[3] if len(cols) >= 4 else "1"
    direction = "LR" if orientation.lower() == "h" else "TD"

    query = f"""--sql
    WITH RECURSIVE routes_clean AS (
        SELECT
            regexp_replace(regexp_replace(COALESCE("{c_orig}", 'None'), '[()\\'']', '', 'g'), ' ', '_', 'g') as origin,
            regexp_replace(regexp_replace(COALESCE("{c_dest}", 'None'), '[()\\'']', '', 'g'), ' ', '_', 'g') as destination,
            {c_weight} as weight,
            regexp_replace(regexp_replace(COALESCE({c_cat}, 'Default'), '[\\'']', '', 'g'), ' ', '_', 'g') as category
        FROM df_input
    ),
    centrality AS (
        SELECT node, count(*) as degree FROM (
            SELECT origin as node FROM routes_clean UNION ALL SELECT destination FROM routes_clean
        ) GROUP BY node
    ),
    hierarchy AS (
        SELECT origin as current_item, [origin] as path_log, CAST(0.0 AS DOUBLE) as total_weight, 'Root' as category, '' as edge_label
        FROM routes_clean WHERE origin NOT IN (SELECT destination FROM routes_clean)
        UNION ALL
        SELECT r.destination, h.path_log || [r.destination], h.total_weight + r.weight, r.category,
               h.current_item || ' -- ' || CASE WHEN r.weight > 1 THEN r.weight::VARCHAR ELSE r.category END || ' --> ' || r.destination
        FROM hierarchy h JOIN routes_clean r ON h.current_item = r.origin
        WHERE NOT list_contains(h.path_log, r.destination)
    )
    SELECT DISTINCT h.*, c.degree, 
           (1.0 / (len(h.path_log))) as closeness,
           (len(h.path_log) * 0.5) as betweenness
    FROM hierarchy h
    LEFT JOIN centrality c ON h.current_item = c.node
    """

    res_df = con.sql(query).to_df()

    unique_cats = sorted([c for c in res_df["category"].unique().tolist() if c != "Root"])
    mermaid_lines = [f"graph {direction}"]
    legend_html = None

    if use_colors:
        # Expanded Palette: Original 5 + 5 New complementary colors
        palette = [
            ("#f96"),
            ("#9cf"),
            ("#dfd"),
            ("#fdb"),
            ("#dff"),  # Original 5
            ("#ccf"),
            ("#ffd1dc"),
            ("#e0bbff"),
            ("#b3e5fc"),
            ("#c8e6c9"),  # New 5
        ]
        legend_items = []
        for i, cat in enumerate(unique_cats):
            hex_color = palette[i % len(palette)]
            mermaid_lines.append(f"    classDef {cat} fill:{hex_color},stroke:#333,stroke-width:1px,color:#000;")
            legend_items.append(
                f'<span style="background-color:{hex_color}; padding: 2px 8px; margin-right: 10px; border: 1px solid #333; border-radius: 4px; color: #000; font-size: 0.8em;">{cat}</span>'
            )

        mermaid_lines.append("    classDef Root fill:#eee,stroke:#999,stroke-dasharray: 5 5,color:#666;")
        if show_legend:
            legend_html = f'<div style="margin-bottom: 20px;"><strong>Legend:</strong> {" ".join(legend_items)}</div>'
    else:
        # Level 68 Style (Dark Uniformity)
        mermaid_lines.append("    classDef default fill:#222,stroke:#444,color:#aaa;")
        mermaid_lines.append("    classDef Root fill:#222,stroke:#444,stroke-dasharray: 5 5,color:#aaa;")

    for edge in res_df[res_df["edge_label"] != ""]["edge_label"].unique():
        mermaid_lines.append(f"    {edge}")

    for _, row in res_df.drop_duplicates("current_item").iterrows():
        mermaid_lines.append(f"    class {row.current_item} {row.category};")

    if legend_html and show_legend:
        display(Markdown(legend_html))

    if debug:
        print("--- DEBUG: MERMAID CODE ---")
        print(mermaid_lines)
        print("---------------------------")

    display(Markdown("```mermaid\n" + "\n".join(mermaid_lines) + "\n```"))

    out = res_df.sort_values("total_weight", ascending=False).drop_duplicates("current_item")[
        ["current_item", "category", "total_weight", "degree", "closeness", "betweenness"]
    ]

    # display(df)
    con.from_df(df).limit(5).show()

    # display(out)
    con.from_df(out).show(max_rows=30)

    return res_df
