"""
pandas-plots main module.
"""

import os

os.environ["BROWSER_PATH"] = "/Applications/Chromium.app/Contents/MacOS/Chromium"

# Import modules
from . import const, hlp, pls, tbl

__all__ = ["const", "hlp", "pls", "tbl"]
