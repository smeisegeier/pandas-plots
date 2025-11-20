import pandas as pd
import numpy as np
from typing import Optional

def group_kkr(df: pd.DataFrame, kkr_col: str) -> pd.DataFrame:
    """
    Groups and counts a DataFrame by kkr_col and other_col (row count only). 
    It preserves all non-zero counts and inserts zero-count placeholders 
    for missing KKR categories.

    FIX: Explicitly converts NaN in other_col to '<NA>' string *before* grouping.

    Args:
        df (pd.DataFrame): The input DataFrame.
        kkr_col (str): The name of the column containing the KKR items. 

    Returns:
        pd.DataFrame: A new DataFrame with columns [kkr_col, other_col, 'cnt'].
    """
    
    # Define constants
    NA_CATEGORY_STR = '<NA>'
    MASTER_KKR_CATEGORIES = [
        '01-SH', '02-HH', '03-NI', '04-HB', '05-NW', '06-HE', '07-RP', '08-BW', 
        '09-BY', '10-SL', '11-BE', '12-BB', '13-MV', '14-SN', '15-ST', '16-TH'
    ]

    # --- 1. Validation and Column Identification ---
    df_processed = df.copy() # Work on a copy
    if kkr_col not in df_processed.columns:
        raise ValueError(f"Column '{kkr_col}' not found in the DataFrame.")

    # Identify the single mandatory other_col
    other_cols_potential = [c for c in df_processed.columns if c != kkr_col]
    type_cols = [c for c in other_cols_potential if not pd.api.types.is_numeric_dtype(df_processed[c])]
    
    if len(type_cols) == 0:
        raise ValueError("The DataFrame must contain at least one other non-numeric column (other_col).")
    other_col: str = type_cols[0]
    
    # --- 2. CRITICAL FIX: Standardize other_col before Grouping ---
    # This prevents the '05-NW | NaN | 351' group from being dropped or misinterpreted.
    df_processed[other_col] = df_processed[other_col].fillna(NA_CATEGORY_STR)
    
    
    # --- 3. Grouping and Aggregation (Row Count Only) ---
    group_by_cols = [kkr_col, other_col]
    
    if df_processed.empty:
        grouped_df = pd.DataFrame(columns=[kkr_col, other_col, 'cnt'])
    else:
        # Simple row count (size())
        grouped_df = df_processed.groupby(group_by_cols).size().reset_index(name='cnt')
            
    # --- 4. Identify and Add Missing KKR Categories ---
    
    # Identify KKR categories present in the grouped data
    present_all_kkr = grouped_df[kkr_col].unique()
    present_master_kkr = [k for k in present_all_kkr if k in MASTER_KKR_CATEGORIES]
    
    # Identify KKR categories that are truly missing
    missing_kkr = [
        k for k in MASTER_KKR_CATEGORIES 
        if k not in present_master_kkr
    ]

    # Create placeholder rows for missing KKR (KKR, '<NA>', 0)
    if missing_kkr:
        missing_df = pd.DataFrame({
            kkr_col: missing_kkr,
            other_col: [NA_CATEGORY_STR] * len(missing_kkr),
            'cnt': [0] * len(missing_kkr)
        })
        missing_df['cnt'] = missing_df['cnt'].astype(int)

        result_df = pd.concat([grouped_df, missing_df], ignore_index=True)
    else:
        result_df = grouped_df.copy()
        
    # --- 5. Final Cleanup ---
    final_cols = [kkr_col, other_col, 'cnt']
    
    # Final type conversion and column order
    result_df['cnt'] = result_df['cnt'].astype(int)
        
    if not result_df.empty:
        result_df = result_df[final_cols]
        
    return result_df