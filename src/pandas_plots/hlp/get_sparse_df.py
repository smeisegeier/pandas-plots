import pandas as pd
from typing import Optional

def get_sparse_df(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Pivots a DataFrame to a sparse wide format by inferring the columns
    and creating a unique sequence index within each group.
    
    DataFrame must have one non-numeric column for pivoting
    and one numeric column for values.
    
    The numeric values of the categorical items will be transformed to seperate column.
    They can now be compared in a single df.
    
    """
    
    # Infer Columns
    non_numeric_cols = df.select_dtypes(exclude=['number', 'datetime']).columns
    if non_numeric_cols.empty:
        print("Error: No non-numeric column found for pivoting.")
        return None
    col_to_pivot = non_numeric_cols[0]
    
    numeric_cols = df.select_dtypes(include=['number']).columns
    if numeric_cols.empty:
        print("Error: No numeric column found for values.")
        return None
    val_column = numeric_cols[0]

    # Display inferred columns (no markdown here)
    # print(f"Inferred Pivot Column: '{col_to_pivot}'")
    # print(f"Inferred Value Column: '{val_column}'")

    # Core Pivoting Logic
    df_copy = df[[col_to_pivot, val_column]].copy()

    # Create a unique, sequential index within each group.
    df_copy['sequence'] = df_copy.groupby(col_to_pivot).cumcount()

    # Perform the pivot without aggregation, using 'sequence' as the index.
    pivoted_df = df_copy.pivot(
        index='sequence',
        columns=col_to_pivot,
        values=val_column
    )

    # Clean up the index name.
    pivoted_df.index.name = f'{val_column}_sequence'
    
    return pivoted_df

if __name__ == "__main__":
    
    # Create a small, artificial sample DataFrame
    sample_data = {
        'Borough': ['Manhattan', 'Queens', 'Manhattan', 'Bronx', 'Queens', 'Manhattan', 'Bronx', 'Queens'],
        'Distance': [1.5, 5.1, 0.8, 3.2, 2.5, 1.4, 7.8, 4.0],
        'ID': [101, 102, 103, 104, 105, 106, 107, 108]
    }
    df_sample = pd.DataFrame(sample_data)
    
    # --- Print Original DataFrame in Markdown ---
    print("Original Sample DataFrame:")
    print(df_sample)
    print("\n")
    
    # --- Get Sparse DataFrame ---
    print("Sparse Pivoted DataFrame using inferred columns:")
    sparse_df = get_sparse_df(df_sample)

    # --- Print Sparse DataFrame in Markdown ---
    if sparse_df is not None:
        # Using to_markdown() here is necessary to generate the markdown table output.
        print(sparse_df)
        print(sparse_df.describe().T)
        print(sparse_df.columns)
