import pandas as pd
import numpy as np
import re
from typing import Optional

def group_kkr(df: Optional[pd.DataFrame] = None, kkr_col: Optional[str] = None) -> pd.DataFrame:
    """
    Groups a DataFrame by a specified column and exactly one other non-numeric
    column, handles different formats in the grouping column, and ensures all
    predefined categories (plus a new 'NA_Unmappable' category) are present 
    in the final output via a right join.

    If called without arguments (i.e., group_kkr()), it runs a demonstration.

    Args:
        df (Optional[pd.DataFrame]): The input DataFrame. If None, the demo runs.
        kkr_col (Optional[str]): The name of the column to group by. Required 
                                if df is provided.

    Returns:
        pd.DataFrame: A new DataFrame with columns [kkr_col, <other_col>, 'cnt'],
                    grouped, counted (or weighted), and joined with a master
                    list of kkr categories, or the result of the demo.
    """
    # Define the custom string for unmappable/NA values
    NA_CATEGORY = '<NA>'

    # --- DEMO EXECUTION ---
    if df is None:
        print("--- DEMO: Executing group_kkr() without arguments ---")
        
        print("\n--- DEMO 1: Processing with a weighted count column (NA values kept) ---")
        weighted_data = {
            'kkr_identifier': [1, '02-HH', '01-SH', '2', 4, '08', 'Unmappable', np.nan],
            'Type': ['X', 'Y', 'X', 'X', 'Y', 'A', 'X', 'Y'],
            'Count': [15.5, 20.0, 5.0, 30.5, 10.0, 0.0, 5.0, 10.0]
        }
        df_with_weights = pd.DataFrame(weighted_data)

        print("\nOriginal DataFrame (includes unmappable/NA values):")
        print(df_with_weights)
        
        print("\nProcessed Result (Weighted, includes 'NA_Unmappable' group):")
        try:
            # Recursive call with demo data
            result_weighted = group_kkr(
                df=df_with_weights, 
                kkr_col='kkr_identifier', 
            )
            print(result_weighted.sort_values(by=['kkr_identifier', 'Type']).head(25))
        except ValueError as e:
            print(f"Error: {e}")

        print("\n" + "="*50 + "\n")

        print("--- DEMO 2: Processing with a simple row count (NA values kept) ---")
        simple_data = {
            'kkr_identifier': [1, '02-HH', '01-SH', '2', '02-HH', 17, '01-SH', '14', None, '00'],
            'Type': ['X', 'Y', 'X', 'X', 'Y', 'Z', 'Y', 'X', 'Y', 'Z']
        }
        df_simple = pd.DataFrame(simple_data)

        print("\nOriginal DataFrame (includes unmappable/NA values):")
        print(df_simple)
        
        print("\nProcessed Result (Simple Count, includes 'NA_Unmappable' group):")
        try:
            # Recursive call with demo data
            result_simple = group_kkr(df=df_simple, kkr_col='kkr_identifier')
            print(result_simple.sort_values(by=['kkr_identifier', 'Type']).head(25))
        except ValueError as e:
            print(f"Error: {e}")
            
        # Return an empty DataFrame or the last demo result (for type consistency)
        # Choosing the latter is more informative if the user is expecting a return value
        return result_simple 

    # --- REGULAR FUNCTION EXECUTION STARTS HERE ---
    
    # Ensure kkr_col is provided if df is not None
    if kkr_col is None:
        raise ValueError("The 'kkr_col' argument must be provided when supplying a DataFrame.")
    
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

    def standardize_kkr_value(value) -> str:
        """Robustly standardizes kkr values by extracting the first integer."""
        # Mapping from integer code to standardized KKR string
        kkr_map = {
            1: '01-SH', 2: '02-HH', 3: '03-NI', 4: '04-HB', 5: '05-NW', 
            6: '06-HE', 7: '07-RP', 8: '08-BW', 9: '09-BY', 10: '10-SL', 
            11: '11-BE', 12: '12-BB', 13: '13-MV', 14: '14-SN', 15: '15-ST', 
            16: '16-TH'
        }
        
        # Check for standard pandas NA values first
        if pd.isna(value):
            return NA_CATEGORY

        match = re.search(r'\d+', str(value))
        if match:
            try:
                num = int(match.group(0))
                return kkr_map.get(num, NA_CATEGORY)
            except ValueError:
                return NA_CATEGORY
        return NA_CATEGORY

    # Apply the standardization
    df_processed[kkr_col] = df_processed[kkr_col].apply(standardize_kkr_value)
    
    # --- 3. Grouping and Aggregation ---
    group_by_cols = [kkr_col, other_col]

    if df_processed.empty:
        grouped_df = pd.DataFrame(columns=[kkr_col, other_col, 'cnt'])
    else:
        # Note on NA in other_col: If 'other_col' has NA values, pandas 
        # groupby will include them as a group by default.
        if weight_col:
            # Weighted count
            grouped_df = df_processed.groupby(group_by_cols).agg(
                cnt=(weight_col, 'sum')
            ).reset_index()
        else:
            # Simple count (using size() to count rows)
            grouped_df = df_processed.groupby(group_by_cols).size().reset_index(name='cnt')


    # --- 4. Right Join with Master List ---
    master_kkr_categories = [
        '01-SH', '02-HH', '03-NI', '04-HB', '05-NW', '06-HE', '07-RP', '08-BW', 
        '09-BY', '10-SL', '11-BE', '12-BB', '13-MV', '14-SN', '15-ST', '16-TH',
        NA_CATEGORY 
    ]
    
    # Step 4a: Get all unique values from the other_col
    unique_other_cols = df_processed[other_col].unique()
    
    # Step 4b: Create a master grid
    if unique_other_cols.size == 0:
        master_df = pd.DataFrame({
            kkr_col: master_kkr_categories,
            other_col: [np.nan] * len(master_kkr_categories),
        })
    else:
        master_df = pd.DataFrame({
            kkr_col: np.repeat(master_kkr_categories, len(unique_other_cols)),
            other_col: np.tile(unique_other_cols, len(master_kkr_categories))
        })
    

    # Perform the left merge
    result_df = pd.merge(
        master_df, grouped_df, on=[kkr_col, other_col], how='left'
    )
    
    # Replace NaN counts with 0
    result_df['cnt'] = result_df['cnt'].fillna(0)
    
    if not weight_col:
        result_df['cnt'] = result_df['cnt'].astype(int)

    # Reorder columns
    final_cols = [kkr_col, other_col, 'cnt']
    result_df = result_df[final_cols]
    
    return result_df
