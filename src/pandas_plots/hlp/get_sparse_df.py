import pandas as pd
from typing import Optional

def get_sparse_df(df: Optional[pd.DataFrame] = None) -> Optional[pd.DataFrame]:
    """
    Pivots a DataFrame to a sparse wide format by inferring the columns
    and creating a unique sequence index within each group.
    
    DataFrame must have one non-numeric column for pivoting
    and one numeric column for values.
    
    The numeric values of the categorical items will be transformed to seperate column.
    They can now be compared in a single df.
    
    If called with no DataFrame (i.e., df=None), it shows a sample use case.
    
    """
    
    if df is None:
        # Logic for when the function is called with no arguments (df=None)
        
        # 1. Create a small, artificial sample DataFrame
        sample_data = {
            'Borough': ['Manhattan', 'Queens', 'Manhattan', 'Bronx', 'Queens', 'Manhattan', 'Bronx', 'Queens'],
            'Distance': [1.5, 5.1, 0.8, 3.2, 2.5, 1.4, 7.8, 4.0],
            'ID': [101, 102, 103, 104, 105, 106, 107, 108]
        }
        df_sample = pd.DataFrame(sample_data)
        
        print("## 📊 Sample Data & Explanation")
        print("---")
        
        print("### Original Sample DataFrame")
        print("This data represents various measurements (like 'Distance') grouped by a category ('Borough').")
        print("The goal is to restructure the data so that the 'Distance' values for each 'Borough' are in separate, comparable columns.")
        # Using df.to_string() to avoid dependency on 'tabulate'
        print(df_sample.to_string(index=False))
        print("\n")
        
        # 2. Get Sparse DataFrame
        print("### Sparse Pivoted DataFrame")
        # Call the function recursively with the sample data
        sparse_df = get_sparse_df(df_sample)
        
        # 3. Print Sparse DataFrame and Explanation
        if sparse_df is not None:
            print("The data has been **pivoted**:")
            print("* The non-numeric column **'Borough'** is used to create the new column names ('Bronx', 'Manhattan', 'Queens').")
            print("* The numeric column **'Distance'** provides the values for the new columns.")
            print("* A new index (**'Distance_sequence'**) is created to align the measurements within each 'Borough' group, allowing comparison of the 1st, 2nd, 3rd, etc., measurement across boroughs.")
            print("* `NaN` values appear where a borough has fewer measurements than others.")
            # Using df.to_string() to avoid dependency on 'tabulate'
            print(sparse_df.to_string())
            
            print("\n**Summary Statistics:**")
            # Using df.to_string() to avoid dependency on 'tabulate'
            print(sparse_df.describe().T.to_string())
            
        return sparse_df # Return the result of the sample run
    
    # --- Actual Function Logic Starts Here (if df is not None) ---
    
    # Infer Columns
    non_numeric_cols = df.select_dtypes(exclude=['number', 'datetime']).columns
    if non_numeric_cols.empty:
        print("Error: No non-numeric column found for pivoting.")
        return None
    col_to_pivot = non_numeric_cols[0]
    
    numeric_cols = df.select_dtypes(include=['number']).columns
    # We take the first numeric column found.
    if numeric_cols.empty:
        print("Error: No numeric column found for values.")
        return None
    val_column = numeric_cols[0]

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