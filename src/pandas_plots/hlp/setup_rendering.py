import os

import matplotlib.pyplot as plt
from IPython import get_ipython

from ._ensure_kaleido_chrome import _ensure_kaleido_chrome


def setup_rendering(
    static: bool = True,
    apply_dark_theme: bool = False,
    to_pdf: bool = False,
):
    """
    **⚠️ font size override is not active**

    Set environment variables for rendering plots to markdown.

    Parameters
    ----------
    static : bool, default=True
        If True, targets static platforms (GitHub, GitLab) — SVG renderer, fixed font sizes.
        If False, targets interactive notebooks — dynamic Plotly renderer, adjustable font sizes.

    apply_dark_theme : bool, default=False
        If True, applies dark theme. This is not applied in conversion to markdown

    to_pdf : bool, default=False
        If True, targets PDF export — forces the SVG renderer and sets PDF=1,
        and overrides apply_dark_theme to always use the light theme (dark theme
        is not applied when rendering to PDF).

    Notes
    -----
    When static is True, the following environment variables are set:
        RENDERER: svg
        THEME: light
        DEBUG: 0
    When static is False, the following environment variables are reset:
        RENDERER: empty string -> ie. plotly dynamic notebook renderer
        FONT_SIZE_TH: 0
        FONT_SIZE_TD: 0
    When to_pdf is True, the following environment variables are set:
        RENDERER: svg
        PDF: 1
    """

    def apply_viz_settings():
        # 1. Standard Matplotlib settings (This works anywhere)
        """
        Apply higher dpi to png that should be svg but cant be rendered since matplotlib cannot be used as backend

        Notes
        -----
        The following settings are applied:

        1. Matplotlib settings:
            figure.dpi is set to 300
        2. IPython Magic settings:
            InlineBackend.figure_format is set to 'retina'
        """
        plt.rcParams["figure.dpi"] = 300

        # 2. IPython Magic settings (This needs the API call)
        ipython = get_ipython()
        if ipython:
            # This is the equivalent of %config InlineBackend.figure_format = 'retina'
            ipython.run_line_magic("config", "InlineBackend.figure_format = 'retina'")

    # * always have static output when called from converter
    static = True if os.getenv("OVERRIDE") == "1" else static
    
    if static:
        apply_viz_settings()
        os.environ["RENDERER"] = "svg"
        # os.environ['THEME']='light'
        os.environ["DEBUG"] = "0"
        # ? you cant set defaults here
        # os.environ['FONT_SIZE_TH']='12'
        # os.environ['FONT_SIZE_TD']='11'
    else:
        os.environ["RENDERER"] = ""
        os.environ["FONT_SIZE_TH"] = "0"
        os.environ["FONT_SIZE_TD"] = "0"

    # * when override is set, this code was called by converter execution -> dont change
    if os.getenv("OVERRIDE") != "1":
        if apply_dark_theme and not to_pdf:
            os.environ["THEME"] = "dark"
        else:
            os.environ["THEME"] = "light"

    if to_pdf:
        os.environ["RENDERER"] = "svg"
        os.environ["PDF"] = "1"
    else:
        os.environ.pop("PDF", None)

    # * svg rendering goes through kaleido, which needs a Chrome binary - make sure
    # * one is available (downloading it once if needed) instead of failing later
    if os.environ.get("RENDERER") == "svg":
        _ensure_kaleido_chrome()
