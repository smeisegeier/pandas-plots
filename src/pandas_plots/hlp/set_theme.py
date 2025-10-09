import os
from typing import Literal


def set_theme(theme: Literal["light", "dark"] = "light"):

    # * check if print is enabled
    if os.getenv("RENDERER") in ('png', 'svg'):
        os.environ['THEME'] = 'light'
    else:
        os.environ['THEME'] = theme
