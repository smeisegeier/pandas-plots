import pandas as pd
import re


def remove_pii(
    series: pd.Series,
    verbose: bool = True,
    logging: bool = False,
    custom_regex="",
) -> pd.Index:
    """
    Remove personally identifiable information (PII) from the given column.

    Parameters:
    - series: A pandas Series representing a column in a DataFrame.
    - verbose: If True, print pii items
    - logging: If True, write pii items into the file .pii.log
    - custom_regex: Regex that is injected into detection

    Returns:
    - index object with indexes of all pii items
    
    Remarks:
    - df.drop(axis=0, index=result, inplace=True)
    """

    # * reject empty columns
    assert len(series) > 0

    col = series.copy()

    # * na must be dropped to ensure processsing
    col.dropna(inplace=True)

    # * find terms
    _terms = frozenset(["lösch", "herr", "frau", "strasse", "klinik"])
    idx_terms = col[
        col.str.contains(
            "|".join(_terms),
            case=False,
            regex=True,
        )
    ].index

    # # * optional: search for terms in whole df
    # df.apply(lambda row: row.astype(str).str.contains('test', case=False, regex=True).any(), axis=1)

    # # * find dates
    ptr_date = r"\d{2}\.\d{2}\.\d{4}"
    idx_date = col[col.str.contains(ptr_date, regex=True)].index

    # * dr
    ptr_dr = r"[D|d][R|r]\. | Fr\. | Hr\. | PD "
    idx_dr = col[col.str.contains(ptr_dr, regex=True)].index

    # * custom
    idx_custom = (
        col[col.str.contains(custom_regex, regex=True)].index
        if custom_regex
        else pd.Index([])
    )

    idx_all = idx_terms.union(idx_date).union(idx_dr).union(idx_custom)

    if verbose:
        # print(f"found: {idx_dr.__len__()} dr | {idx_date.__len__()} date | {idx_terms.__len__()} terms")
        print(f"found {idx_all.__len__():_} pii items:")
        print(col.loc[idx_all].tolist())

    if logging:  # Assuming logging is defined and has the correct value
        data = col.loc[idx_all]  # Assuming col and idx_all are defined
        with open(".pii.log", "w") as f:
            # ! when using str(), it will give only a summary!
            f.write(data.to_string(index=True))

    return idx_all
