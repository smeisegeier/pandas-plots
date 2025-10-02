import duckdb as ddb
from IPython.display import display, HTML
import os

def descr_db(
    db: ddb.DuckDBPyRelation,
    caption: str = "db",
    use_preview: bool = True,
)->None:
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

    Returns
    -------
    None
    """

    # * ensure markdown is correctly rendered
    is_print = (os.getenv("RENDERER") in ('png', 'svg'))

    # * wide tables are not properly rendered in markdown
    width = 220 if is_print else 2000
    
    if is_print:
        display(HTML("<br>"))
    
    cols = ", ".join(db.columns)
    print(f'🗄️ {caption}\t{db.count("*").fetchone()[0]:_}, {db.columns.__len__()}\n\t("{cols}")')
    
    if use_preview:
        db.limit(3).show(max_width=width)
    return