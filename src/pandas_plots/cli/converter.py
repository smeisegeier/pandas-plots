import dataframe_image as dfi
import os
import argparse


def jupyter_to_md(
    path: str,
    output_dir: str = "./docs",
    no_input=False,
    execute=True,  # Default to True, can be overridden with --no_execute
    chrome_path="/opt/homebrew/bin/chromium",
):
    # * ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # * if this isnt set, plotly digrams will not be rendered
    os.environ["RENDERER"] = "svg"

    # * suppress DEBUG output
    os.environ["DEBUG"] = "0"

    # * convert
    dfi.convert(
        path,
        to="markdown",
        # use='latex',
        # center_df=True,
        # max_rows=30,
        # max_cols=10,
        execute=execute,
        save_notebook=False,
        limit=None,
        document_name=None,
        table_conversion="chrome",
        chrome_path=chrome_path,
        latex_command=None,
        output_dir=output_dir,
        no_input=no_input,
    )

    # * reset
    os.environ["RENDERER"] = ""  # <None> does not work


# Keep the original function name as primary, alias if needed
def jupyter_2_md(*args, **kwargs):
    """Alias function with the name you want to use"""
    return jupyter_to_md(*args, **kwargs)


def test():
    """Example of a second CLI function with proper argument parsing"""
    parser = argparse.ArgumentParser(description="Another function in the CLI")
    parser.add_argument("path", help="Path to process")
    parser.add_argument("--output_dir", "-o", default="./output", help="Output directory (default: ./output)")

    args = parser.parse_args()
    print(f"Running another function on {args.path} with output to {args.output_dir}")
    # Add your second functionality here


def main():
    parser = argparse.ArgumentParser(description="Convert Jupyter notebooks to markdown")
    parser.add_argument("path", help="Path to the Jupyter notebook to convert")
    parser.add_argument("--output_dir", "-o", default="./docs", help="Output directory (default: ./docs)")
    parser.add_argument("--no_input", action="store_true", help="Exclude input cells in output (default: False)")
    parser.add_argument("--no_execute", action="store_true", help="Do not execute notebook before conversion (default: False - executes by default)")
    parser.add_argument("--chrome_path", default="/opt/homebrew/bin/chromium", 
                    help="Path to Chrome/Chromium executable (default: /opt/homebrew/bin/chromium)")
    
    args = parser.parse_args()
    
    # Convert no_execute to execute (invert the logic)
    execute = not args.no_execute
    
    jupyter_to_md(
        path=args.path,
        output_dir=args.output_dir,
        no_input=args.no_input,
        execute=execute,
        chrome_path=args.chrome_path
    )


if __name__ == "__main__":
    main()
