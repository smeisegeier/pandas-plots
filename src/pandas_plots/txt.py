def wrap(text: str | list, max_items_in_line: int=70, sep:bool=True, apo: bool=False):
    """
    A function that wraps text into lines with a maximum number of items per line.
    
    Args:
        text (str | list): The input text or list of words to be wrapped.
        max_items_in_line (int): The maximum number of items allowed in each line.
        sep (bool, optional): Whether to include a comma separator between items. Defaults to True.
        apo (bool, optional): Whether to enclose each word in single quotes. Defaults to False.
    """

    # * check if text is string, then strip and build word list
    is_text=isinstance(text, str)
    if is_text:
        text = (text
                .replace(",", "")
                .replace("'", "")
                .replace("[", "")
                .replace("]", "")
                .split(" ")
                )

    # * start
    i = 0
    line = ""

    # * loop through words
    out=""
    for word in text:
        apo_s="'" if apo else ""
        sep_s="," if sep and not is_text else ""
        word_s=f'{apo_s}{str(word)}{apo_s}{sep_s}'
        # * inc counter
        i = i + len(word_s)
        # * construct print line
        line = line + word_s + " "
        # * reset if counter exceeds limit
        if i >= max_items_in_line:
            out=out + line + "\n"
            line = ""
            i = 0
        # else:
    # * on short lists no reset happens, trigger manually
    out = line if not out else out
    # * cut last newline
    return f"[{out[:-1]}]"