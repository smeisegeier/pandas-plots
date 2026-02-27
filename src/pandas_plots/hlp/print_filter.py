from IPython.display import Markdown, display


def print_filter(
    filter: str,
) -> None:
    display(Markdown("<!-- START_TOKEN -->"))
    print("# filter")
    print(filter.replace("--sql", ""))
    display(Markdown("<!-- END_TOKEN -->"))
    return
