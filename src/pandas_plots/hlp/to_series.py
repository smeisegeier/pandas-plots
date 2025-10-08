
import pandas as pd

def to_series(df) -> pd.Series | None:
    """
    Converts a pandas DataFrame to a pandas Series.

    Parameters:
        df (pd.DataFrame): The DataFrame to be converted.

    Returns:
        pd.Series | None: The converted Series if successful, None otherwise.

    Raises:
        None

    Notes:
        - If the input `df` is already a Series, it is returned as is.
        - If the input `df` has more than 2 columns, an error message is printed and None is returned.
        - If the input `df` has 1 column, a new Series is created with the input column as the data and the input index as the index.
        - If the input `df` has 2 columns, the function checks which column is the index. If the first column is numeric, the second column is set as the data and the first column is set as the index. If the second column is numeric, the first column is set as the data and the second column is set as the index. If neither column is numeric, an error message is printed and None is returned.
        - The index and name of the resulting Series are set to the appropriate labels.
    """
    # * check if df is a series
    if isinstance(df, pd.Series):
        return df
    # * too many columns
    if len(df.columns) > 2:
        print("❌ df must have exactly 2 columns")
        return None
    # * df can have 1 column, proper index is assumed then
    elif len(df.columns) == 1:
        return pd.Series(index=df.index, data=df.iloc[:, 0].values, name=df.columns[0])
    else:
        # * check which column is the index
        if pd.api.types.is_numeric_dtype(df.iloc[:, 0]):
            _idx_col = df.iloc[:, 1]
            _data_col = df.iloc[:, 0]
        elif pd.api.types.is_numeric_dtype(df.iloc[:, 1]):
            _idx_col = df.iloc[:, 0]
            _data_col = df.iloc[:, 1]
        else:
            print("❌ df must have exactly 1 numeric column")
            return None
        s = pd.Series(
            index=_idx_col.values,
            data=_data_col.values,
        )
        # * set index and name to proper labels
        s.index.name = _idx_col.name
        s.name = _data_col.name
        return s

# * extend objects to enable chaining
pd.DataFrame.to_series = to_series
pd.Series.to_series = to_series