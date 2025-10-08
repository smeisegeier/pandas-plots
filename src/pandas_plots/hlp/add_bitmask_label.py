import duckdb as ddb
import pandas as pd

def add_bitmask_label(
    data: pd.DataFrame | pd.Series | ddb.DuckDBPyRelation,
    bitmask_col: str,
    labels: list[str],
    separator: str = "|",
    zero_code: str = "-",
    keep_col: bool = True,
    con: ddb.DuckDBPyConnection = None,
) -> pd.DataFrame | ddb.DuckDBPyRelation:
    """
    adds a column to the data (DataFrame, Series, or DuckDB Relation) that resolves a bitmask column into human-readable labels.
    - bitmask_col must have been generated before. its value must be constructed as a bitmask, e.g:
    - a red, green, blue combination is rendered into binary 110, which means it has green and blue
    - its value is 6, which will resolved into "g|b" if the list ["r","g","b"] is given

    bitmask_col values with null are set to 0 to be processed.

    if the bitmask value is 0, it will be replaced with the zero_code.
    the method can be chained in pandas as well as in duckdb: df.add_bitmask_label(...)

    Parameters:
    - data (pd.DataFrame | pd.Series | duckdb.DuckDBPyRelation): Input data.
    - bitmask_col (str): The name of the column containing bitmask values (ignored if input is Series).
    - labels (list[str]): Labels corresponding to the bits, in the correct order.
    - separator (str): Separator for combining labels. Default is "|".
    - zero_code (str): Value to return for bitmask value 0. Default is "-".
    - keep_col (bool): If True, retains the bitmask column. If False, removes it. Default is True.
    - con (duckdb.Connection): DuckDB connection object. Required if data is a DuckDB Relation.

    Returns:
    - pd.DataFrame | duckdb.DuckDBPyRelation: The modified data with the new column added.
    """
    # * check possible input formats
    if isinstance(data, ddb.DuckDBPyRelation):
        if con is None:
            raise ValueError(
                "A DuckDB connection must be provided when the input is a DuckDB Relation."
            )
        data = data.df()  # * Convert DuckDB Relation to DataFrame

    if isinstance(data, pd.Series):
        bitmask_col = data.name if data.name else "bitmask"
        data = data.to_frame(name=bitmask_col)



    if not isinstance(data, pd.DataFrame):
        raise ValueError(
            "Input must be a pandas DataFrame, Series, or DuckDB Relation."
        )

    # ! null values cant be handled, so they are replaced with 0
    data[bitmask_col] = data[bitmask_col].fillna(0)

    # * get max allowed value by bitshift, eg for 4 labels its 2^4 -1 = 15
    max_allowable_value = (1 << len(labels)) - 1
    # * compare against max in col
    max_value_in_column = data[bitmask_col].max()
    if max_value_in_column > max_allowable_value:
        raise ValueError(
            f"The maximum value in column '{bitmask_col}' ({max_value_in_column}) exceeds "
            f"the maximum allowable value for {len(labels)} labels ({max_allowable_value}). "
            f"Ensure the number of labels matches the possible bitmask range."
        )

    # ? Core logic
    # * exit if 0
    def decode_bitmask(value):
        if value == 0:
            return zero_code
        # * iterate over each value as bitfield, on binary 1 fetch assigned label from [labels]
        return separator.join(
            [label for i, label in enumerate(labels) if value & (1 << i)]
        )

    label_col = f"{bitmask_col}_label"
    data[label_col] = data[bitmask_col].apply(decode_bitmask)

    # * drop value col if not to be kept
    if not keep_col:
        data = data.drop(columns=[bitmask_col])

    # * Convert back to DuckDB Relation if original input was a Relation
    if isinstance(data, pd.DataFrame) and con is not None:
        return con.from_df(data)

    return data


# * extend objects to enable chaining
pd.DataFrame.add_bitmask_label = add_bitmask_label
ddb.DuckDBPyRelation.add_bitmask_label = add_bitmask_label