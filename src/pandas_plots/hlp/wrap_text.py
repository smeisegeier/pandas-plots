import re



def wrap_text(
    text: str | list,
    max_items_in_line: int = 70,
    use_sep: bool = True,
    use_apo: bool = False,
):
    """
    A function that wraps text into lines with a maximum number of items per line.
    Important: enclose this function in a print() statement to print the text

    Args:
        text (str | list): The input text or list of words to be wrapped.
        max_items_in_line (int): The maximum number of items allowed in each line.
        use_sep (bool, optional): When list: Whether to include a comma separator between items. Defaults to True.
        use_apo (bool, optional): When list: Whether to enclose each word in single quotes. Defaults to False.
    Returns: the wrapped text
    """

    # * check if text is string
    is_text = isinstance(text, str)
    if is_text:
        # ! when splitting the text later by blanks, newlines are not correctly handled
        # * to detect them, they must be followed by a blank:
        pattern = r"(\n)(?=\S)"  # *forward lookup for newline w/ no blank
        # * add blank after these newlines
        new_text = re.sub(pattern, r"\1 ", text)
        text = new_text

        # * then strip and build word list
        text = (
            text.replace(",", "")
            .replace("'", "")
            .replace("[", "")
            .replace("]", "")
            # * use explicit blanks to prevent newline split
            .split(" ")
        )

    # * loop setup
    i = 0
    line = ""
    # * loop through words
    out = ""
    for word in text:
        apo_s = "'" if use_apo and not is_text else ""
        sep_s = "," if use_sep and not is_text else ""
        word_s = f"{apo_s}{str(word)}{apo_s}{sep_s}"
        # * inc counter
        i = i + len(word_s)
        # * construct print line
        line = line + word_s + " "
        # * reset if counter exceeds limit, or if word ends with newline
        if i >= max_items_in_line or str(word).endswith("\n"):
            # out = out + line + "\n"
            out = out + line.rstrip() + "  \n"
            line = ""
            i = 0
        # else:
    # * on short lists no line reset happens, so just print the line
    # * else add last line
    out = line if not out else out + line
    # * cut off last newline
    return f"[{out[:-1].strip()}]"
