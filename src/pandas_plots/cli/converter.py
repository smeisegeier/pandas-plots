import dataframe_image as dfi
import os
import argparse
import re

def enclose_ascii_table_in_code_block(content):
    """
    Searches for blocks that start with '┌' and end with '└', 
    and encloses the entire block with Markdown code fences (```).
    
    Args:
        content (str): The full text content of the Markdown document.

    Returns:
        str: The cleaned content.
    """
    
    # The regular expression uses:
    # 1. re.DOTALL: Allows '.' to match across newlines (for the content in between).
    # 2. re.MULTILINE: Allows '^' and '$' to match the start and end of each line.
    
    # Search Pattern (FIXED for multi-match reliability):
    # (\s*┌.*?^\s*└[^\n]*)   -> Group 1: Captures the entire table block, starting with ┌, 
    #                            non-greedily (.*?) up to the └ line, and then captures 
    #                            content on that line, stopping BEFORE the line's newline.
    # (\n|$)                  -> Group 2: Captures the necessary newline (\n) after the └ line 
    #                            or the end of the string ($), forcing the match to terminate.
    pattern = re.compile(
        r'(\s*┌.*?^\s*└[^\n]*)(\n|$)',
        re.DOTALL | re.MULTILINE
    )
    
    # Replacement Pattern:
    # Inserts newlines and fences, preserving the captured table block (\1) and 
    # the trailing newline (\2).
    replacement = r'\n\n\n\t\t```\1\n\t\t```\n\n\2'
    # replacement = r'\n\n```\1\n```\n\2'
    
    new_content = re.sub(pattern, replacement, content)
    
    return new_content


def remove_pandas_style_from_md(markdown_filepath):
    """
    Removes the default Pandas HTML style block, cleans up excessive blank lines,
    and encloses recognized ASCII tables with Markdown code fences.
    """
    try:
        # 1. Read the file content
        with open(markdown_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content 
        
        # 2. STEP: REMOVE HTML STYLE BLOCK
        style_pattern = re.compile(r'<style\s*.*?>.*?</style>', re.DOTALL | re.IGNORECASE)
        content = re.sub(style_pattern, '', content)

        # 3. STEP: ENCLOSE ASCII TABLES WITH CODE FENCES
        # content = enclose_ascii_table_in_code_block(content)

        # 4. STEP: CLEAN UP EXCESSIVE BLANK LINES
        # Replaces three or more consecutive blank lines with two.
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        
        if content != original_content:
            # 5. Write the cleaned content back to the file
            with open(markdown_filepath, 'w', encoding='utf-8') as f:
                content = content.strip() # Final global strip before writing to prevent extra blank lines at EOF
                f.write(content)
            print(f"✅ CLEANED: File successfully processed: {markdown_filepath}")
            return True
        else:
            print(f"ℹ️ NO CHANGES: No elements found to clean in: {markdown_filepath}")
            return False

    except FileNotFoundError:
        print(f"❌ ERROR: File not found at {markdown_filepath}")
        return False
    except Exception as e:
        print(f"❌ ERROR DURING PROCESSING: {e}")
        return False

def remove_css_style_from_md(markdown_filepath: str):
    """
    Reads a file (assumed to contain Markdown/HTML content), removes two 
    specific, problematic CSS rules from the embedded <style> block, and 
    overwrites the file with the cleaned content(these are printed as plain text in pdf)

    The removed rules are:
    1. .dataframe tbody tr th { vertical-align: top; }
    2. .dataframe thead th { text-align: right; }

    Args:
        markdown_filepath: The path to the file (e.g., a .md or .html file) 
                           to be read and overwritten.
    """
    try:
        # Read the entire file content
        with open(markdown_filepath, 'r', encoding='utf-8') as f:
            html_or_md_content = f.read()
    except FileNotFoundError:
        print(f"Error: File not found at {markdown_filepath}")
        return

    # Define the block of CSS you want to remove.
    css_to_remove_pattern = re.escape("""
    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }""")

    # The pattern must start with the newline and indentation *before* the first rule
    css_to_remove_pattern = r'\n' + css_to_remove_pattern

    # Use re.sub() to replace the unwanted block with an empty string.
    # re.DOTALL (re.S) ensures the pattern can match across multiple lines.
    cleaned_content = re.sub(css_to_remove_pattern, '', html_or_md_content, flags=re.DOTALL)

    # Write the cleaned content back to the same file
    try:
        with open(markdown_filepath, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        print(f"Successfully removed CSS rules and updated: {markdown_filepath}")
    except Exception as e:
        print(f"Error writing to file: {e}")



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
        use='latex',
        # center_df=True,
        max_rows=50,
        max_cols=25,
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
    # remove_pandas_style_from_md(target_md_path)
    remove_css_style_from_md(target_md_path)

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
