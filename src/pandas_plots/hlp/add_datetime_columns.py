
import pandas as pd

def add_datetime_columns(df: pd.DataFrame, date_column: str = None) -> pd.DataFrame:
    """
    Add datetime columns to a given DataFrame.

    Adds the following columns to the given DataFrame:
        - YYYY: Year of date_column
        - MM: Month of date_column
        - Q: Quarter of date_column
        - YYYY-MM: Year-month of date_column
        - YYYYQ: Year-quarter of date_column
        - YYYY-WW: Year-week of date_column
        - DDD: Day of the week of date_column

    Args:
        df (pd.DataFrame): The DataFrame to add datetime columns to.
        date_column (str, optional): The column to base the added datetime columns off of. Defaults to None.

    Returns:
        pd.DataFrame: The DataFrame with the added datetime columns.
        This command can be chained.
    """
    df_ = df.copy()
    if not date_column:
        date_column = [
            col for col in df_.columns if pd.api.types.is_datetime64_any_dtype(df_[col])
        ][0]
    else:
        df_[date_column] = pd.to_datetime(df_[date_column])

    if not date_column or not pd.api.types.is_datetime64_any_dtype(df_[date_column]):
        print("❌ No datetime column found")
        return

    if [col for col in df_.columns if "YYYY-WW" in col]:
        print("❌ Added datetime columns already exist")
        return

    print(f"⏳ Adding datetime columns basing off of: {date_column}")

    df_["YYYY"] = df_[date_column].dt.year
    df_["MM"] = df_[date_column].dt.month
    df_["Q"] = df_[date_column].dt.quarter

    df_["YYYY-MM"] = df_[date_column].dt.to_period("M").astype(str)
    df_["YYYYQ"] = df_[date_column].dt.to_period("Q").astype(str)
    df_["YYYY-WW"] = (
        df_[date_column].dt.isocalendar().year.astype(str)
        + "-W"
        + df_[date_column].dt.isocalendar().week.astype(str).str.zfill(2)
    )
    df_["DDD"] = df_[date_column].dt.weekday.map(
        {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}
    )

    return df_

# * extend objects to enable chaining
pd.DataFrame.add_datetime_columns = add_datetime_columns