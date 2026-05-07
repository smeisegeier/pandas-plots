import os
import re
import pandas as pd


def export_plot_data(df: pd.DataFrame, title: str | None = None, verbose: bool = False) -> pd.DataFrame:
    """
    Aggregates a DataFrame and exports it to ./data/<name>.csv. Chainable.

    Groups by all columns except the last. If the last column is numeric, sums its values;
    otherwise counts rows per group as 'cnt'.

    The filename defaults to output_{cell_execution_count}_0 (matching Jupyter's image naming).
    If title is provided, spaces become underscores and all characters except [a-zA-Z0-9_-] are removed.

    Args:
        df: Input DataFrame to aggregate and export.
        title: Optional filename stem. Spaces become underscores; special chars (except _ and -) are stripped.
                Defaults to None, which uses the Jupyter execution count for naming.
        verbose: If True, prints the exported filepath. Defaults to False.

    Returns:
        The original unmodified DataFrame (for chaining).
    """
    cols = df.columns.tolist()
    last_col = cols[-1]
    group_cols = cols[:-1]

    if pd.api.types.is_numeric_dtype(df[last_col]):
        if group_cols:
            result = df.groupby(group_cols, as_index=False)[last_col].sum()
        else:
            result = pd.DataFrame({last_col: [df[last_col].sum()]})
    else:
        if group_cols:
            result = df.groupby(group_cols, as_index=False).size().rename(columns={"size": "cnt"})
        else:
            result = pd.DataFrame({"cnt": [len(df)]})

    try:
        from IPython import get_ipython
        ipy = get_ipython()
        exec_count = ipy.execution_count if ipy is not None else 0
    except (ImportError, AttributeError):
        exec_count = 0

    if title is not None:
        name = re.sub(r"[^\w\s-]", "", title).strip()
        name = re.sub(r"\s+", "_", name)
        name = re.sub(r"[^\w-]", "", name)
    else:
        name = f"output_{exec_count}_0"

    os.makedirs("./data", exist_ok=True)
    filepath = f"./data/{name}.csv"
    result.to_csv(filepath, index=False)
    if verbose:
        print(f"💾 exported: {filepath}")

    return df
