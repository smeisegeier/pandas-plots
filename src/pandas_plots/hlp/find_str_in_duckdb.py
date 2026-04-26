import duckdb
import pandas as pd

def find_str_in_duckdb(con: duckdb.DuckDBPyConnection, search_term: str, use_regex: bool = False):
    """
    Search for a given string in all tables of a DuckDB database.  
    ⚠️ regex: you must preface with `(?i)` to ignore case

    Args:
        con (duckdb.DuckDBPyConnection): The DuckDB connection object.
        search_term (str): The string to search for.
        use_regex (bool, optional): Whether to use regular expressions in the search. Defaults to False.

    Returns:
        None

    Prints:
        - The results of the search in a tabular format.
        - A message indicating that no matches were found if the search term does not appear in any table.

    Example:
        >>> con = duckdb.connect('my_database.db')
        >>> find_str_in_duckdb(con, 'example', use_regex=True)
    """
    tables = con.execute(
        "SELECT table_name FROM duckdb_tables ORDER BY table_name"
    ).fetchall()
    table_names = [t[0] for t in tables]

    all_results = []
    escaped = search_term.replace("'", "''")

    for table_name in table_names:
        cols = con.execute(
            "SELECT column_name FROM duckdb_columns WHERE table_name = ?", [table_name]
        ).fetchall()
        col_names = [c[0] for c in cols]
        if not col_names:
            continue

        if use_regex:
            count_clauses = [
                f'SUM(CASE WHEN regexp_matches("{col}"::VARCHAR, \'{escaped}\')'
                f' THEN 1 ELSE 0 END)::INTEGER AS "{col}"'
                for col in col_names
            ]
            sql_query = f'SELECT {", ".join(count_clauses)} FROM "{table_name}"'
            counts = con.execute(sql_query).df()
        else:
            count_clauses = [
                f'SUM(CASE WHEN "{col}"::VARCHAR ILIKE ? THEN 1 ELSE 0 END)::INTEGER AS "{col}"'
                for col in col_names
            ]
            sql_query = f'SELECT {", ".join(count_clauses)} FROM "{table_name}"'
            counts = con.execute(sql_query, [f'%{search_term}%'] * len(col_names)).df()

        result = counts.T
        result.columns = ['hit_count']
        result = result[result['hit_count'] > 0]
        if not result.empty:
            result.insert(0, 'table', table_name)
            all_results.append(result)

    mode = "regex" if use_regex else "string"
    print(f"results for {mode} search: {search_term}")
    if all_results:
        final = pd.concat(all_results)
        final.index.name = 'column'
        print(final.to_string())
    else:
        print(f"No matches found for '{search_term}' in any table.")


# find_str_in_duckdb(con, 'item')
# search_db(con, r'\d{4}', use_regex=True)