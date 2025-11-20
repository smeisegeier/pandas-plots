import duckdb

def get_duckdb_filter_n(con=None, query=None, filters=None, debug=False, max_bar_length=30, distinct_metric=None):
    """
    Executes a series of cascading queries on a DuckDB connection,
    calculates row counts (or distinct counts of a specified metric) and percentages, 
    and optionally visualizes them using a right-aligned ASCII scale.

    Args:
        con: A duckdb.DuckDBPyConnection object. If None, runs in example mode.
        query (str): The initial query string (e.g., "from TBL" or "select * from TBL").
        filters (list of tuples): A list of tuples, where each tuple is
                                (filter_string, caption_string).
        debug (bool): If True, prints the generated SQL queries instead of executing them.
        max_bar_length (int): The length of the ASCII bar (default is 30). 
                            If set to 0, the bars are hidden.
        distinct_metric (str): If set (e.g., 'user_id'), the function calculates 
                            COUNT(DISTINCT <distinct_metric>) instead of COUNT(*).
    """
    # --- Flag to track if the connection was created here ---
    connection_is_ephemeral = False
    
    # Determine if bars should be shown based on the argument
    show_bars = max_bar_length > 0
    
    # --- Bar Constants and Formatting ---
    BLOCK_FILLED = "█" 
    BLOCK_EMPTY = "░"  
    BOX_CORNER = "└" 
    
    # --- Example Mode Setup ---
    if con is None:
        print("Running in **Example Mode** (No arguments provided).")
        print("---")
        connection_is_ephemeral = True 
        
        # Create an in-memory database for the example with a large dataset (100,000)
        con = duckdb.connect(':memory:')
        con.execute("""
            CREATE TABLE users (
                id INTEGER,        -- Unique ID
                user_id INTEGER,   -- User ID (non-unique, e.g., 30% are repeated)
                age INTEGER,
                status VARCHAR,
                region VARCHAR
            );
        """)
        EXAMPLE_COUNT = 100000
        UNIQUE_USER_COUNT = 70000
        con.execute(f"""
            INSERT INTO users 
            SELECT 
                i, 
                CASE WHEN i <= {UNIQUE_USER_COUNT} THEN i ELSE i - 10000 END,
                CASE WHEN i <= {EXAMPLE_COUNT * 0.3} THEN 25 WHEN i <= {EXAMPLE_COUNT * 0.7} THEN 45 ELSE 60 END, 
                CASE WHEN i % 3 = 0 THEN 'inactive' ELSE 'active' END, 
                CASE WHEN i <= {EXAMPLE_COUNT * 0.5} THEN 'east' ELSE 'west' END 
            FROM range(1, {EXAMPLE_COUNT + 1}) tbl(i);
        """)

        # Set distinct_metric for example to demonstrate its functionality
        if distinct_metric is None:
            distinct_metric = 'user_id' # Default to distinct count in example
        
        query = "from users" 
        filters = [
            ("age > 30", "Over 30"),                     
            ("age < 50", "30-50 Range"),                 
            ("status = 'active'", "Active Status"),       
            ("region = 'west'", "Western Active 30-50"), 
        ]
        print(f"Example Initial Query: {query}")
        print("---")
    # --- End Example Mode Setup ---

    # Define the COUNT clause based on the distinct_metric argument (using its final state from setup)
    if distinct_metric:
        count_clause = f"count(DISTINCT {distinct_metric})"
        count_label = f"counts: distinct {distinct_metric}"
    else:
        count_clause = "count(*)"
        count_label = "counts: rows"

    # --- Print the Metric/Count Label ---
    print(count_label)
    print("---")

    if filters is None or not filters:
        print("Error: Filters list is empty. Cannot continue.")
        return

    # --- Pre-process the user query for use as a subquery ---
    if not query.strip().lower().startswith('select'):
        base_query_source = f"SELECT * {query}"
    else:
        base_query_source = query

    # --- Initial Row Count (100% Base) ---
    base_query = f"SELECT {count_clause} FROM ({base_query_source})"
    
    if debug:
        print(f"**DEBUG** Base Query (100%): {base_query}")
        return

    base_count = con.execute(base_query).fetchone()[0]
    
    # --- Calculate Alignment Widths ---
    
    # 1. Find the maximum length of the descriptive caption text
    max_caption_len = max(len(caption_str or filter_str) for filter_str, caption_str in filters)
    
    # Filter prefix is '└ [Caption]:'
    MAX_LEFT_TEXT_WIDTH = max_caption_len + len(f" {BOX_CORNER} []:")
    
    # 2. Determine the fixed width for the percentage/count display. 
    formatted_base_count_val = f"n = {base_count:,}".replace(",", "_")
    WIDTH_COUNT_PART = len(formatted_base_count_val)
    WIDTH_PERCENT = len("(100.0%)")
    
    # --- Print Initial Row Count (100% Base) ---
    
    n_part = f"n = {base_count:,}".replace(",", "_")
    initial_percent = "(100.0%)"
    
    if show_bars:
        initial_line_bar = BLOCK_FILLED * max_bar_length
    else:
        initial_line_bar = ""
        
    # Padding needed between n_part and initial_percent
    padding_needed = MAX_LEFT_TEXT_WIDTH + WIDTH_COUNT_PART - len(n_part)
    
    print(
        f"{n_part}"                                     # Start immediately at the beginning of the line
        f"{' ' * padding_needed}"                       # Pad up to the start of the percentage block
        f" {initial_percent}"                           # Space + Percent
        f" "                                            # Space before bar
        f"{initial_line_bar}"
    )

    # --- Cascading Filters Logic ---
    current_where_clause = ""
    
    for filter_idx, (filter_str, caption_str) in enumerate(filters):
        # SQL Execution
        if current_where_clause:
            current_where_clause += f" AND ({filter_str})"
        else:
            current_where_clause = f"({filter_str})"
            
        # Use the configured count_clause here
        full_query = f"SELECT {count_clause} FROM ({base_query_source}) WHERE {current_where_clause}"
        
        if debug:
            print(f"**DEBUG** Filter Query #{filter_idx+1}: {full_query}")
            continue

        current_count = con.execute(full_query).fetchone()[0]
        
        # 4. Determine the caption
        caption = caption_str if caption_str else filter_str
        
        # 5. Calculate bar/padding (only if showing bars)
        if show_bars:
            if base_count == 0:
                bar_length_filled = 0
            else:
                bar_length_filled = int((current_count / base_count) * max_bar_length)
            
            bar_length_empty = max_bar_length - bar_length_filled
            bar = BLOCK_EMPTY * bar_length_empty + BLOCK_FILLED * bar_length_filled
        else:
            bar = ""

        # 6. Format the output strings
        formatted_count_val = f"n = {current_count:,}".replace(",", "_")
        percentage = f"({(current_count / base_count) * 100:.1f}%)"
        
        # 7. Construct the final line with alignment
        
        # Left Text: NEW FORMAT '└ [Caption]:'
        left_text = f"{BOX_CORNER} [{caption}]:"
        caption_padding_width = MAX_LEFT_TEXT_WIDTH - len(left_text)
        
        # Count/Percent Block, padded to fixed widths
        count_padded = f"{formatted_count_val:>{WIDTH_COUNT_PART}}"
        percent_padded = f"{percentage:>{WIDTH_PERCENT}}"
        
        # Total line assembly: [Left Text] [Count] [Percent] [Bar]
        final_line = (
            f"{left_text}{' ' * caption_padding_width}"  # Filter prefix aligned to MAX_LEFT_TEXT_WIDTH
            f"{count_padded} {percent_padded} "         
            f"{bar}"                                    
        )
        
        print(final_line)

    # Clean up the connection ONLY if it was created inside this function (in example mode)
    if connection_is_ephemeral: 
         con.close()