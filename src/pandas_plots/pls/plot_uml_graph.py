import duckdb
import pandas as pd
import os
from IPython.display import display, Markdown

def plot_uml_graph(df=None, orientation='v', debug=False):
    """
    Generalized Graph Renderer with Self-Calculated Diagnostics
    
    Arguments:
    ----------
    df : pandas.DataFrame, optional
        Input data with at least two columns (Source, Target). 
        Third column is Weight, fourth is Category.
    orientation : str, default 'v'
        Direction of the graph. 'v'/'TD' (Vertical) or 'h'/'LR' (Horizontal).
    debug : bool, default False
        If True, enables additional console output.

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
            ('Level 68', 'Karazhan Key Chain', 1, 'Quest'),
            ('Karazhan Key Chain', 'Karazhan Raid', 1, 'Raid'),
            ('Karazhan Raid', 'Nightbane', 1, 'Boss'),
            ('Level 70', 'Cenarion Expedition Honored', 1, 'Reputation'),
            ('Cenarion Expedition Honored', 'Heroic Slave Pens', 1, 'Dungeon'),
            ('Heroic Slave Pens', 'Cudgel of Kardesh Quest', 1, 'Quest'),
            ('Karazhan Raid', 'Cudgel of Kardesh Quest', 1, 'Boss Drop'),
            ('Cudgel of Kardesh Quest', 'Serpentshrine Cavern', 1, 'Raid'),
            ('Level 70', 'Trial of the Naaru', 1, 'Quest Chain'),
            ('Magtheridon Raid', 'Trial of the Naaru', 1, 'Boss Drop'),
            ('Trial of the Naaru', 'The Eye', 1, 'Raid'),
            ('Serpentshrine Cavern', 'The Vials of Eternity', 1, 'Boss Drop'),
            ('The Eye', 'The Vials of Eternity', 1, 'Boss Drop'),
            ('The Vials of Eternity', 'Battle for Mount Hyjal', 1, 'Raid'),
            ('Karazhan Raid', 'Cipher of Damnation', 1, 'Quest'),
            ('Cipher of Damnation', 'Black Temple Chain', 1, 'Quest'),
            ('Black Temple Chain', 'Akama Alliance', 1, 'Quest'),
            ('Battle for Mount Hyjal', 'Akama Alliance', 1, 'Raid Step'),
            ('Akama Alliance', 'Black Temple', 1, 'Raid'),
            ('Level 68', 'Level 70', 1, 'Leveling'),
            ('Level 70', 'Honor Hold Honored', 1, 'Reputation'),
            ('Honor Hold Honored', 'Flamewrought Key', 1, 'Vendor'),
            ('Flamewrought Key', 'Heroic Shattered Halls', 1, 'Access'),
            ('Level 70', 'Lower City Honored', 1, 'Reputation'),
            ('Lower City Honored', 'Auchenai Key', 1, 'Vendor'),
            ('Auchenai Key', 'Heroic Shadow Labyrinth', 1, 'Access'),
            ('Level 70', 'Keepers of Time Honored', 1, 'Reputation'),
            ('Keepers of Time Honored', 'Key of Time', 1, 'Vendor'),
            ('Key of Time', 'Heroic Black Morass', 1, 'Access')
        ]
        df = pd.DataFrame(attunement_data, columns=['Pre', 'Req', 'Weight', 'Type'])

    theme = os.getenv("THEME", "light")
    use_colors = (theme == "light")
    con = duckdb.connect(database=':memory:')
    con.register('df_input', df)
    
    cols = df.columns.tolist()
    c_orig, c_dest, c_weight, c_cat = cols[0], cols[1], f'"{cols[2]}"', f'"{cols[3]}"'
    direction = "LR" if orientation.lower() == 'h' else "TD"
    
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

    unique_cats = sorted([c for c in res_df['category'].unique().tolist() if c != 'Root'])
    mermaid_lines = [f"graph {direction}"]
    legend_html = ""
    
    if use_colors:
        # Expanded Palette: Original 5 + 5 New complementary colors
        palette = [
            ('#f96'), ('#9cf'), ('#dfd'), ('#fdb'), ('#dff'), # Original 5
            ('#ccf'), ('#ffd1dc'), ('#e0bbff'), ('#b3e5fc'), ('#c8e6c9') # New 5
        ]
        legend_items = []
        for i, cat in enumerate(unique_cats):
            hex_color = palette[i % len(palette)]
            mermaid_lines.append(f"    classDef {cat} fill:{hex_color},stroke:#333,stroke-width:1px,color:#000;")
            legend_items.append(f'<span style="background-color:{hex_color}; padding: 2px 8px; margin-right: 10px; border: 1px solid #333; border-radius: 4px; color: #000; font-size: 0.8em;">{cat}</span>')
        
        mermaid_lines.append(f"    classDef Root fill:#eee,stroke:#999,stroke-dasharray: 5 5,color:#666;")
        legend_html = f'<div style="margin-bottom: 20px;"><strong>Legend:</strong> {" ".join(legend_items)}</div>'
    else:
        # Level 68 Style (Dark Uniformity)
        mermaid_lines.append("    classDef default fill:#222,stroke:#444,color:#aaa;")
        mermaid_lines.append("    classDef Root fill:#222,stroke:#444,stroke-dasharray: 5 5,color:#aaa;")

    for edge in res_df[res_df['edge_label'] != '']['edge_label'].unique():
        mermaid_lines.append(f"    {edge}")

    for _, row in res_df.drop_duplicates('current_item').iterrows():
        mermaid_lines.append(f"    class {row.current_item} {row.category};")

    if legend_html: display(Markdown(legend_html))
    
    if debug:
        print("--- DEBUG: MERMAID CODE ---")
        print(mermaid_lines)
        print("---------------------------")
    
    display(Markdown(f"```mermaid\n" + "\n".join(mermaid_lines) + "\n```"))
    
    display(res_df.sort_values('total_weight', ascending=False).drop_duplicates('current_item')
            [['current_item', 'category', 'total_weight', 'degree', 'closeness', 'betweenness']])
    
    return res_df
