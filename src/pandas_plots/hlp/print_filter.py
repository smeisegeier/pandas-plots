from IPython.display import Markdown, display


def print_filter(
    filter: str,
    show_as_details: bool = False,
) -> None:
    """
    Prints a filter string to the console, optionally formatted as a details HTML tag.

    Args:
        filter (str): The filter string to print.
        show_as_details (bool, optional): If True, formats the filter string as a details HTML tag. Defaults to False.
    """
    
    # # * override details block if rendering aims towards pdf
    # if os.getenv("RENDERER") in ('png', 'svg'):
    #     show_as_details = False
    
    
    cleaned_filter = (filter
        .replace("--sql", "")
        # * remove multiple newlines, looks ugly
        .replace("\n\n", "\n")
    )
    
    if show_as_details:
        display(Markdown(f"<details>\n<summary>filter-sql</summary>\n\n```sql\n{cleaned_filter}\n```\n\n</details>"))
    else:
        display(Markdown("<!-- START_TOKEN -->"))
        print("-- filter-sql")
        print(cleaned_filter)
        display(Markdown("<!-- END_TOKEN -->"))

    return
