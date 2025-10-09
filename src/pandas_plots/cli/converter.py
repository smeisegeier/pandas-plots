import dataframe_image as dfi
import os
import argparse
import re

def remove_pandas_style_from_md(markdown_filepath):
    """
    Removes the default Pandas HTML style block and cleans up excessive 
    blank lines from a Markdown file.
    
    This function targets the <style> block often included by Pandas
    and compresses three or more consecutive blank lines into two.
    """
    try:
        # 1. Read the file content
        with open(markdown_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content # Keep original content to check for changes

        # 2. REMOVE STYLE BLOCK
        # Regular expression to find any <style>...</style> block.
        style_pattern = re.compile(
            r'<style\s*.*?>.*?</style>',
            re.DOTALL | re.IGNORECASE
        )
        content = re.sub(style_pattern, '', content)

        
        # 3. CLEAN EXCESS BLANK LINES
        # Replace two or more blank lines (which may contain whitespace) 
        # with just a single blank line (\n\n).
        # We search for \n followed by zero or more spaces (\s*) and another \n, 
        # repeated at least twice.
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        

        if content != original_content:
            # 4. Write the cleaned content back to the file
            with open(markdown_filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ SUCCESS: Cleaned style blocks and excess blank lines in: {markdown_filepath}")
            return True
        else:
            print(f"ℹ️ NO CHANGES: No style blocks or excessive blank lines found in: {markdown_filepath}")
            return False

    except FileNotFoundError:
        print(f"❌ ERROR: File not found at {markdown_filepath}")
        return False
    except Exception as e:
        print(f"❌ AN ERROR OCCURRED: {e}")
        return False


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
    
    # * remove style block
    # 1. Get the filename without its original extension
    root = os.path.splitext(os.path.basename(path))[0]

    # 2. Construct the full path using the correct .md extension
    target_md_path = os.path.join(output_dir, root + '.md')

    # 3. Call the function
    remove_pandas_style_from_md(target_md_path)

# * Keep the original function name as primary, alias if needed
def jupyter_2_md(*args, **kwargs):
    return jupyter_to_md(*args, **kwargs)

def j2md(*args, **kwargs):
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
    parser.add_argument("--output-dir", "-o", default="./docs", help="Output directory (default: ./docs)")
    parser.add_argument("--no-input", action="store_true", help="Exclude input cells in output (default: False)")
    parser.add_argument("--no-execute", action="store_true", help="Do not execute notebook before conversion (default: False - executes by default)")
    parser.add_argument("--chrome-path", default="/opt/homebrew/bin/chromium", 
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
