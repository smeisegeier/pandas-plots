import os
import matplotlib.pyplot as plt
from IPython import get_ipython

def setup_rendering(render: bool = False):
    """
    **⚠️ font size override is not active**

    Set environment variables for rendering plots to markdown.
    If set to False, font size in tables can be adjusted.
    If set to True, font size is fixed to match with markdown output

    Parameters
    ----------
    render : bool, default=False
        If True, environment variables are set for rendering plots to markdown.
        If False, environment variables are reset to default values.

    Notes
    -----
    When render is True, the following environment variables are set:
        RENDERER: svg
        THEME: light
        DEBUG: 0
        FONT_SIZE_TH: 9
        FONT_SIZE_TD: 8
    When render is False, the following environment variables are reset:
        RENDERER: empty string -> ie. plotly dynamic notebook renderer
        FONT_SIZE_TH: 0
        FONT_SIZE_TD: 0
    """



    def apply_viz_settings():
        # 1. Standard Matplotlib settings (This works anywhere)
        """
        Apply higher dpi to png that shopuld be svg but cant be rendered since matplotlib cannot be used as backend

        Notes
        -----
        The following settings are applied:

        1. Matplotlib settings:
            figure.dpi is set to 300
        2. IPython Magic settings:
            InlineBackend.figure_format is set to 'retina'
        """
        plt.rcParams['figure.dpi'] = 300
        
        # 2. IPython Magic settings (This needs the API call)
        ipython = get_ipython()
        if ipython:
            # This is the equivalent of %config InlineBackend.figure_format = 'retina'
            ipython.run_line_magic('config', "InlineBackend.figure_format = 'retina'")

    if render:
        apply_viz_settings()
        os.environ["RENDERER"] = "svg"
        os.environ['THEME']='light'
        os.environ['DEBUG']='0'
        # ? you cant set defaults here
        # os.environ['FONT_SIZE_TH']='12'
        # os.environ['FONT_SIZE_TD']='11'
    else:
        os.environ["RENDERER"] = ""
        os.environ['FONT_SIZE_TH']="0"
        os.environ['FONT_SIZE_TD']="0"
