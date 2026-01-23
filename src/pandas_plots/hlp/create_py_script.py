import argparse
import ipynbname
import subprocess
from . import is_ipynb, prepend_uv_header

def create_py_script(args_list: list, toml_path: str, write_py: bool = True):
    """
    Creates a .py script from a .ipynb file.
    - generates argument parsing off of a list of arguments
    - prepends a uv header to the .py script to enable execution per `uv run <filename>.py`
    - returns a tuple of the parsed arguments
    - if in ipynb, returns a tuple of the default values
    - so the function can be used in both .ipynb and .py scripts

    Parameters
    ----------
        args_list : list
            A list of tuples (arg_name, default_value, help_string)
        toml_path : str
            The path to the toml file which lists the dependencies of the
            target script.
        write_py : bool
            Whether to write the .py script

    Returns
    -------
        tuple
            A tuple of the parsed arguments

    Raises
    ------
        FileNotFoundError
            If the toml file is not found

    Example
    ----------
    ```python
args_list = [
        ('file_db', FILE_DB, 'Path to the DuckDB database file'),
        ('dataset_name', DATASET_NAME, 'Name of the dataset to process'),
        ('filter_tum', FILTER_TUM, 'SQL filter for tumor data')
]
file_db, dataset_name, filter_tum = create_py_script(args_list, "../../pyproject.toml")
    ```
    then use: `uv run <ipynb-filename>.py --help`
    """

    def get_dynamic_args(args_list):
        """
        Builds an ArgumentParser from a list of tuples and returns the parsed args.
        
        :param args_list: List of tuples (arg_name, default_value, help_string)
        :return: parsed arguments as a tuple
        """
        
        # * if in ipynb - return defaults, no param parsing allowed
        if is_ipynb():
            return tuple(default for name, default, help_text in args_list)

        # * if not in ipynb - parse
        parser = argparse.ArgumentParser(description='dynamic parser')

        # * add each paramt
        for name, default, help_text in args_list:
            # We assume string types for simplicity, but you can expand this
            parser.add_argument(
                f'--{name.replace("_", "-")}', 
                type=type(default) if default is not None else str,
                default=default,
                help=f'{help_text}. default: %(default)s'
            )
        args_obj = parser.parse_args()
        
        # * return parsed args as a tuple
        return tuple(getattr(args_obj, name) for name, default, help_text in args_list)

    # * 1) get dynamic args which are just the defaults if in ipynb
    out = get_dynamic_args(args_list)

    # * 2) if in ipynb
    if is_ipynb() and write_py:
        # * 2a) convert ipynb to py, get path of current ipynb
        nb_path = ipynbname.path().as_posix()
        # * use subprocess to run the terminal command safely
        cmd = ["uv", "run", "jupyter", "nbconvert", "--to", "python", nb_path]
        subprocess.run(cmd)

        # * 2b) after the .py is created, prepend uv header
        py_path = ipynbname.path().as_posix().replace(".ipynb", ".py")
        prepend_uv_header(py_path, toml_path)
    return out
