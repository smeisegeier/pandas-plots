def prepend_uv_header(target_script, toml_path):
    """
    Prepends a header to a target script which lists its dependencies.
    
    The header is in the format of a Python comment, with each dependency
    listed on a separate line. The header is prepended to the top of the
    target script, and the existing content of the script is left unchanged.
    
    Example
    ----------
    💡 Hint: this function should be paired with nbconvert like this
    ```python
    if is_ipynb():
        !uv run jupyter nbconvert --to python data-delivery.ipynb
        prepend_uv_header("data-delivery.py", "../../pyproject.toml")
    ```
    Parameters
    ----------
    target_script : str
        The path to the target script.
    toml_path : str
        The path to the toml file which lists the dependencies of the
        target script.
    """
    import tomllib
    from pathlib import Path
    
    if not toml_path.exists():
        raise FileNotFoundError(f"Required pyproject.toml not found at: {toml_path.resolve()}")

    # Get deps
    with open(toml_path, "rb") as f:
        deps = tomllib.load(f)["project"]["dependencies"]
    
    # Format header
    header = "# /// script\n# dependencies = [\n"
    header += "\n".join([f'#   "{d}",' for d in deps])
    header += "\n# ]\n# ///\n\n"
    
    # Read existing script content
    script_path = Path(target_script)
    content = script_path.read_text()
    
    # Write back with header at top
    script_path.write_text(header + content)
    print(f"✅ Prepended header, you can now use 'uv run {target_script}'")
    