# from IPython.display import display, HTML
import os

import duckdb as ddb


def descr_db(
    db: ddb.DuckDBPyRelation,
    caption: str = "db",
    use_preview: bool = True,
    width: int = 0,
) -> None:
    """
    Print a short description of the given duckdb relation.

    Parameters
    ----------
    db: ddb.DuckDBPyRelation
        The relation to be described
    caption: str, optional
        A caption to be printed left of the description. Defaults to "db".
    use_preview: bool, optional
        Whether to print a preview of the first 3 rows of the relation. Defaults to True.
    width: int, optional
        The maximum width of the table. Defaults to 0.

    Returns
    -------
    None
    """

    # * check if print is enabled
    is_print = os.getenv("RENDERER") in ("png", "svg")

    if width == 0:
        # * wide tables are not properly rendered in markdown
        width = 145 if is_print else 2000

    # if is_print:
    #     display(HTML("<br>"))

    cols = ", ".join(db.columns)
    print(f'🗄️ {caption}\t{db.count("*").fetchone()[0]:_}, {db.columns.__len__()}\n\t("{cols}")')

    if use_preview:
        db.limit(3).show(max_width=width)

    return
