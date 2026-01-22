def is_ipynb() -> bool:
    """
    Checks if the current code is running in an IPython environment.

    Returns:
        bool: True if the current code is running in an IPython environment, False otherwise.
    """
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            return True
        return False
    except ImportError:
        return False
