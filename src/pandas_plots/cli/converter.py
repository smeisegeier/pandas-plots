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

def conditional_br_replacer(match):
    """
    Replacement function for re.sub that conditionally inserts a <br> tag.
    
    It identifies the last line belonging to the list structure within the matched chunk 
    and inserts '\n\n<br>\n\n' immediately after it, ensuring the tag is placed 
    after all nested list elements and before the arbitrary subsequent text.
    """
    # G1: (\n|^) - Preceding context (newline or start of string)
    preceding_context = match.group(1)
    
    # G2: (\s*-\s*.*?) - The full block from list item start to ┌─
    full_chunk = match.group(2) 
    
    # G3: (┌─) - The closing delimiter
    closing_delimiter = match.group(3) 

    # 1. Check if the required tag (with guaranteed separation) is already present.
    # We check for any variation of <br> surrounded by at least one newline.
    if re.search(r'\n\s*<br>\s*\n', full_chunk):
        return match.group(0)

    # 2. Split G2 (full_chunk) into list_block and text_block by finding the end of the list.
    lines = full_chunk.splitlines(keepends=True)
    last_list_line_index = -1

    # Heuristic: A line belongs to the list structure if it starts with a hyphen/star. 
    # The list block is considered to end immediately when the first non-list-marker, 
    # non-blank line is encountered.
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        
        # Check for explicit list marker ('-', '*')
        is_list_marker = stripped.startswith('-') or stripped.startswith('*')
        
        if is_list_marker:
            last_list_line_index = i
        elif stripped == '':
            # Allow blank lines within the list block (e.g., between top-level items)
            continue
        else:
            # Found non-list marker, non-blank text (the arbitrary text 'lore ipsum').
            # List structure must have ended at the line pointed to by last_list_line_index.
            break

    # If no list lines were found (shouldn't happen based on the outer regex), return unchanged.
    if last_list_line_index == -1:
        return match.group(0)

    # Combine list lines (from start up to and including the last list line found)
    list_block = "".join(lines[:last_list_line_index + 1])
    # Combine text lines (from after the last list line)
    text_block = "".join(lines[last_list_line_index + 1:])

    # 3. Clean up newlines around the injection point for precise spacing.
    # Strip trailing newlines from list_block to add exactly two newlines.
    list_block = list_block.rstrip('\n')

    # Strip leading newlines from text_block (we will add exactly two newlines).
    text_block = text_block.lstrip('\n')

    # 4. Construct the new chunk: [List Block] + [\n\n<br>\n\n] + [Text Block]
    # The injection adds the necessary blank lines (two newlines before, two newlines after).
    new_chunk = list_block + '\n\n<br>\n\n' + text_block
    
    # Final construction: [Preceding Context] + [New Chunk] + [Delimiter]
    return preceding_context + new_chunk + closing_delimiter


def add_br_to_md(markdown_filepath):
    """
    Processes a Markdown file to find chunks starting with a list item ('-') 
    and ending with the duckdb table start ('┌─'). If the chunk does not 
    contain a line-separated '<br>' tag, it is inserted immediately after 
    the list line.
    """
    try:
        with open(markdown_filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        
        # Pattern to match the target chunk:
        # (\n|^)           -> Preceding newline or start of string (Group 1)
        # (\s*-\s*.*?)(┌─) -> The content starting with '-', non-greedy (.*?), up to '┌─' (Groups 2 & 3)
        
        pattern = re.compile(
            r'(\n|^)(\s*-\s*.*?)(┌─)', 
            re.DOTALL | re.MULTILINE
        )
        
        # Use the replacement function to conditionally insert the <br> tag
        new_content = re.sub(pattern, conditional_br_replacer, content)

        if new_content != original_content:
            # Write the modified content back to the file
            with open(markdown_filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✅ Successfully inserted missing line-separated <br> tags in: {markdown_filepath}")
            return True
        else:
            print(f"ℹ️ All target chunks already contained the line-separated <br> tag in: {markdown_filepath}")
            return False

    except FileNotFoundError:
        print(f"❌ Error: File not found at {markdown_filepath}")
    except Exception as e:
        print(f"❌ An error occurred: {e}")


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
        print(f"✅ Successfully removed CSS rules and updated: {markdown_filepath}")
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

    # 3. remove style
    # remove_pandas_style_from_md(target_md_path)
    remove_css_style_from_md(target_md_path)
    
    # 4. add br
    add_br_to_md(target_md_path)

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
