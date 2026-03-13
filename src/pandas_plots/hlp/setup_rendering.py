import os


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
        FONT_SIZE_TH: 7
        FONT_SIZE_TD: 5
    When render is False, the following environment variables are reset:
        RENDERER: empty string -> ie. plotly dynamic notebook renderer
        FONT_SIZE_TH: 0
        FONT_SIZE_TD: 0
    """
    if render:
        os.environ["RENDERER"] = "svg"
        os.environ['THEME']='light'
        os.environ['DEBUG']='0'
        os.environ['FONT_SIZE_TH']='0'
        os.environ['FONT_SIZE_TD']='0'
    else:
        os.environ["RENDERER"] = ""
        os.environ['FONT_SIZE_TH']="0"
        os.environ['FONT_SIZE_TD']="0"