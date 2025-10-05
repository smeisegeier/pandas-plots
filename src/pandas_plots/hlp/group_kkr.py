import pandas as pd
import numpy as np
import re
# from typing import List

def group_kkr(df: pd.DataFrame, kkr_col: str) -> pd.DataFrame:
    """
    Groups a DataFrame by a specified column and exactly one other non-numeric
    column, handles different formats in the grouping column, and ensures all
    predefined categories are present in the final output via a right join.

    Args:
        df (pd.DataFrame): The input DataFrame. It should contain the kkr_col,
                        exactly one other non-numeric column, and optionally a
                        single numeric weight column.
        kkr_col (str): The name of the column to group by. This column should
                    contain values that can be mapped to one of the 16
                    predefined categories.

    Returns:
        pd.DataFrame: A new DataFrame with columns [kkr_col, <other_col>, 'cnt'],
                    grouped, counted (or weighted), and joined with a master
                    list of kkr categories. The count column is 'cnt'.
    """
    # --- 1. Input Validation and Column Identification ---
    if kkr_col not in df.columns:
        raise ValueError(f"Column '{kkr_col}' not found in the DataFrame.")

    # Identify all columns other than the kkr_col
    other_cols = [c for c in df.columns if c != kkr_col]

    # Find the single non-numeric column (the 'type_col')
    type_cols = [
        c for c in other_cols 
        if not pd.api.types.is_numeric_dtype(df[c])
    ]

    # Find any numeric columns (potential 'weight_col')
    weight_cols = [
        c for c in other_cols 
        if pd.api.types.is_numeric_dtype(df[c])
    ]

    if len(type_cols) != 1:
        raise ValueError(
            "The DataFrame must contain exactly one other non-numeric column. "
            f"Found: {type_cols}"
        )
    
    # Extract the single column names from the lists
    other_col: str = type_cols[0]
    weight_col: str = weight_cols[0] if weight_cols else ''


    # --- 2. Data Preparation and Standardization ---
    df_processed = df.copy()

    def standardize_kkr_value(value) -> str | float:
        """Robustly standardizes kkr values by extracting the first integer."""
        # Mapping from integer code to standardized KKR string
        kkr_map = {
            1: '01-SH', 2: '02-HH', 3: '03-NI', 4: '04-HB', 5: '05-NW', 
            6: '06-HE', 7: '07-RP', 8: '08-BW', 9: '09-BY', 10: '10-SL', 
            11: '11-BE', 12: '12-BB', 13: '13-MV', 14: '14-SN', 15: '15-ST', 
            16: '16-TH'
        }
        
        match = re.search(r'\d+', str(value))
        if match:
            num = int(match.group(0))
            return kkr_map.get(num, np.nan)
        return np.nan

    # Apply the standardization
    df_processed[kkr_col] = df_processed[kkr_col].apply(standardize_kkr_value)
    
    # Remove rows that couldn't be mapped
    df_processed.dropna(subset=[kkr_col], inplace=True)

    # --- 3. Grouping and Aggregation ---
    group_by_cols = [kkr_col, other_col]

    if df_processed.empty:
        # Handle case where no rows are left after cleaning
        grouped_df = pd.DataFrame(columns=[kkr_col, other_col, 'cnt'])
    else:
        if weight_col:
            # Weighted count
            grouped_df = df_processed.groupby(group_by_cols).agg(
                cnt=(weight_col, 'sum')
            ).reset_index()
        else:
            # Simple count (using size() to count rows)
            grouped_df = df_processed.groupby(group_by_cols).size().reset_index(name='cnt')


    # --- 4. Right Join with Master List ---
    # The master list must be created based on the columns we want to keep
    # to facilitate the subsequent right join/merge.
    master_kkr_categories = [
        '01-SH', '02-HH', '03-NI', '04-HB', '05-NW', '06-HE', '07-RP', '08-BW', 
        '09-BY', '10-SL', '11-BE', '12-BB', '13-MV', '14-SN', '15-ST', '16-TH'
    ]
    
    # Create the master list DataFrame.
    # To correctly use the right join, we need a structure that ensures all
    # combinations of kkr_col and other_col are generated before merging,
    # or we need to merge in two steps. A one-step merge on only kkr_col 
    # will duplicate other_col values incorrectly.
    
    # Step 4a: Get all unique values from the other_col
    unique_other_cols = df_processed[other_col].unique()
    
    # Step 4b: Create a master grid of all KKR categories and unique other_col values
    if unique_other_cols.size == 0 and not grouped_df.empty:
        # This handles the case where the only data was dropped, but we need
        # the 'other_col' values from the original data if possible,
        # but since we processed df_processed, we use the grouped_df's unique
        # values if it's not empty.
        unique_other_cols = grouped_df[other_col].unique()
    elif unique_other_cols.size == 0 and grouped_df.empty:
        # If both are empty, we just use a placeholder for other_col to create
        # a DataFrame with all KKR categories and all 'cnt' as 0.
        master_df = pd.DataFrame({
            kkr_col: master_kkr_categories,
            other_col: [np.nan] * len(master_kkr_categories), # Placeholder
        })
    
    if unique_other_cols.size > 0:
        # Create a cartesian product of KKR categories and unique 'other_col' values
        master_df = pd.DataFrame({
            kkr_col: np.repeat(master_kkr_categories, len(unique_other_cols)),
            other_col: np.tile(unique_other_cols, len(master_kkr_categories))
        })
    

    # Perform the left merge (grouped_df LEFT master_df, so the 'master_df' 
    # structure is maintained). We use left merge on the master grid.
    result_df = pd.merge(
        master_df, grouped_df, on=[kkr_col, other_col], how='left'
    )
    
    # Replace NaN counts with 0
    result_df['cnt'] = result_df['cnt'].fillna(0)
    
    # Ensure 'cnt' is an integer if no weight column was used and counts are integers
    if not weight_col:
        result_df['cnt'] = result_df['cnt'].astype(int)

    # Reorder columns to the desired format
    final_cols = [kkr_col, other_col, 'cnt']
    result_df = result_df[final_cols]
    
    return result_df

# --- Necessary Imports for Example Usage ---
# Already imported above, but placed here for full clarity if the function
# were copied separately.
# import pandas as pd
# import re
# import numpy as np

# --- Example Usage ---
if __name__ == '__main__':
    print("--- DEMO: Processing with a weighted count column ---")
    weighted_data = {
        'kkr_identifier': [1, '02-HH', '01-SH', '2', 4, '08'],
        'Type': ['X', 'Y', 'X', 'X', 'Y', 'A'],
        'Count': [15.5, 20.0, 5.0, 30.5, 10.0, 0.0] # float weights
    }
    df_with_weights = pd.DataFrame(weighted_data)

    print("\nOriginal DataFrame:")
    print(df_with_weights)
    
    print("\nProcessed Result (Weighted):")
    try:
        result_weighted = group_kkr(
            df=df_with_weights, 
            kkr_col='kkr_identifier', 
        )
        print(result_weighted)
    except ValueError as e:
        print(f"Error: {e}")

    print("\n" + "="*50 + "\n")

    print("--- DEMO: Processing with a simple row count ---")
    simple_data = {
        'kkr_identifier': [1, '02-HH', '01-SH', '2', '02-HH', 17, '01-SH', '14'], # 17 is unmappable
        'Type': ['X', 'Y', 'X', 'X', 'Y', 'Z', 'Y', 'X']
    }
    df_simple = pd.DataFrame(simple_data)

    print("\nOriginal DataFrame:")
    print(df_simple)
    
    print("\nProcessed Result (Simple Count):")
    try:
        result_simple = group_kkr(df=df_simple, kkr_col='kkr_identifier')
        print(result_simple)
    except ValueError as e:
        print(f"Error: {e}")
