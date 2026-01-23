import dataframe_image as dfi
import os
import argparse
import re

def enclose_block_as_code(markdown_filepath: str, start_token: str, stop_token: str, language: str = 'python', remove_token_lines: bool = True) -> bool:
    """
    Processes a Markdown file to find a block defined by single, unique start and stop tokens.
    It encloses the content *between* them in a Markdown code block, modifying the file in-place.
    
    Args:
        markdown_filepath (str): Path to the Markdown file.
        start_token (str): The token marking the beginning of the content block (must be line prefix).
        stop_token (str): The token marking the end of the content block (must be line prefix).
        language (str): The language tag for the Markdown code block. Defaults to 'python'.
        remove_token_lines (bool): If True (default), the lines containing the start and stop tokens
                                   are removed from the final output file. If False, they are included
                                   *inside* the resulting code block.

    Returns:
        bool: True if changes were made, False otherwise.
    """
    
    try:
        with open(markdown_filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        new_lines = []
        changes_made = False
        block_buffer = []
        just_enclosed_block = False # New flag to track when a block was just processed
        
        state = 0 # 0: Searching, 1: Collecting
        
        block_start_line_index = -1 
        block_end_line_index = -1   

        for i, line in enumerate(lines):
            # Use lstrip() for the check to ignore line indentation, but keep the raw 'line' 
            # for content collection to preserve internal indentation.
            lstripped = line.lstrip()
            
            # --- Blank Line Consumption (Highest Priority) ---
            if just_enclosed_block:
                if not line.strip():
                    # If we just enclosed a block and the current line is blank, consume it (skip append).
                    continue
                else:
                    # Non-blank line found, stop consuming and process the line as normal.
                    just_enclosed_block = False
            
            # --- State 0: Searching for Start (or processing after a block) ---
            if state == 0:
                if lstripped.startswith(start_token):
                    # Start found.
                    
                    if not remove_token_lines:
                        # INCLUDE TOKEN: Add the token line to the block buffer.
                        block_buffer.append(line)
                        block_start_line_index = i # Token line is the start
                    else:
                        # EXCLUDE TOKEN: Do not append line to new_lines, effectively removing it.
                        block_start_line_index = i + 1 # Content starts next line
                        
                    
                    state = 1
                else:
                    new_lines.append(line)
                continue

            # --- State 1: Collecting Content until Stop ---
            elif state == 1:
                
                if lstripped.startswith(stop_token):
                    # Stop found.
                    
                    if not remove_token_lines:
                        # INCLUDE TOKEN: Add the token line to the block buffer.
                        block_buffer.append(line)
                        block_end_line_index = i # Token line is the end
                    else:
                        # EXCLUDE TOKEN: The content ended on the previous line.
                        block_end_line_index = i - 1 

                    # 1. Check for idempotence using the raw buffer content
                    content_raw = "".join(block_buffer)
                    
                    if not content_raw.strip().startswith(f"```{language}"):
                        # Block is NOT enclosed. Time to clean and enclose.
                        
                        # Filter out empty/blank lines from buffer before joining
                        cleaned_buffer = [line for line in block_buffer if line.strip()]
                        content_to_enclose_cleaned = "".join(cleaned_buffer)
                        
                        # 2. Enclose the cleaned content
                        # Use .rstrip() to remove any final trailing newline inside the code block
                        code_block = f"\n```{language}\n{content_to_enclose_cleaned.rstrip()}\n```\n\n"
                        new_lines.append(code_block)
                        changes_made = True
                        just_enclosed_block = True # Set flag to consume next blank lines
                    else:
                        # Block IS enclosed. Extend raw content to new_lines.
                        new_lines.extend(block_buffer)
                    
                    # 3. Handle the stop token line itself (if removed, it's already consumed)
                    
                    # 4. Reset state and buffer
                    state = 0
                    block_buffer = []
                    continue
                
                # Standard collection (content between tokens)
                block_buffer.append(line)
                continue
                
        # --- FINAL POST-LOOP CHECK (EOF hit while in State 1) ---
        if state == 1:
            # Block started but stop token was not found (or EOF hit)
            content_raw = "".join(block_buffer)

            if not content_raw.strip().startswith(f"```{language}"):
                # Filter out empty/blank lines from buffer before joining
                cleaned_buffer = [line for line in block_buffer if line.strip()]
                content_to_enclose_cleaned = "".join(cleaned_buffer)
                
                # Use .rstrip() to remove any final trailing newline inside the code block
                code_block = f"\n```{language}\n{content_to_enclose_cleaned.rstrip()}\n```\n\n" 
                new_lines.append(code_block)
                changes_made = True
            else:
                new_lines.extend(block_buffer)
            
            if block_end_line_index == -1 and block_start_line_index != -1:
                 # If EOF hit, the end line is the last line processed.
                 block_end_line_index = len(lines) - 1 

        # --- WRITE OUTPUT ---
        
        if changes_made:
            final_content = "".join(new_lines)

            with open(markdown_filepath, 'w', encoding='utf-8') as f:
                f.write(final_content)
            
            # Output only the requested line numbers (1-based for the user)
            print(f"└ ✅ SUCCESS: Block enclosed from line {block_start_line_index + 1} to {block_end_line_index + 1}. Tokens were {'included' if not remove_token_lines else 'removed'}.")
            return True
        else:
            print(f"└ ℹ️ NO CHANGES: No block found between '{start_token}' and '{stop_token}' in: {markdown_filepath} or block already enclosed.")
            return False

    except FileNotFoundError:
        print(f"❌ ERROR: File not found at {markdown_filepath}")
        return False
    except Exception as e:
        print(f"❌ ERROR DURING PROCESSING: {e}")
        return False



def add_br_to_md(markdown_filepath, is_debug=False):
    """
    Processes a Markdown file line-by-line using a dynamic state machine 
    (NO REGEX) to insert the '<br>' tag immediately after the last list item 
    and before the subsequent arbitrary content, within chunks ending with '┌─'.
    
    Args:
        markdown_filepath (str): Path to the Markdown file.
        is_debug (bool): If True, logs insertion details and prints final result messages.
        
    Returns:
        bool: True if changes were made, False otherwise.
    """
    try:
        with open(markdown_filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        new_lines = []
        changes_made = False
        
        # State machine variables for reconstruction
        in_chunk = False
        last_list_line_content = None  # String content of the last list item line
        post_list_lines = []           # Lines between last list item and delimiter
        
        current_line_num = 0

        for line in lines:
            current_line_num += 1
            stripped = line.strip()
            is_list_marker = stripped.startswith('-') or stripped.startswith('*')
            
            
            if not in_chunk:
                # --- INITIAL STATE: Search for chunk start ---
                if is_list_marker:
                    # Found the start of a target chunk
                    in_chunk = True
                    last_list_line_content = line
                    post_list_lines = []
                else:
                    new_lines.append(line)
                continue
            
            # --- IN_CHUNK STATE ---
            
            # 1. Update Last List Item Found (If list item continues)
            if is_list_marker:
                # Flush previous list item and accumulated post-list lines directly to output, 
                # as they are now known to be non-insertion-point content.
                if last_list_line_content is not None:
                    new_lines.append(last_list_line_content)
                new_lines.extend(post_list_lines)

                # Track the new last list item
                last_list_line_content = line
                post_list_lines = []
                continue

            # 2. End Condition Found (Trigger Insertion or Flush)
            if '┌─' in stripped:
                
                # Check for idempotence: If <br> is already in the post-list content, bypass insertion.
                post_list_content = "".join(post_list_lines)
                if '<br>' in post_list_content:
                    # Flush the chunk without change
                    if last_list_line_content is not None:
                        new_lines.append(last_list_line_content)
                    new_lines.extend(post_list_lines)
                    new_lines.append(line)
                else:
                    # --- PERFORM INSERTION ---
                    
                    # A. Append the list line (without its trailing newline)
                    new_lines.append(last_list_line_content.rstrip('\n')) 
                    
                    # B. Insert the required tag (the full \n\n<br>\n\n structure)
                    new_lines.append('\n\n<br>\n\n')
                    
                    # C. Append the content between the list and the delimiter (stripped of leading \n)
                    text_content_stripped = post_list_content.lstrip('\n')
                    new_lines.append(text_content_stripped)
                    
                    # D. Append the closing delimiter line
                    new_lines.append(line)
                    
                    changes_made = True
                    if is_debug:
                        # Calculate insertion line for logging
                        insertion_line = current_line_num - len(post_list_lines)
                        print(f"└ DEBUG: INSERTED after Line {insertion_line} in file {os.path.basename(markdown_filepath)}")

                # Reset state
                in_chunk = False
                last_list_line_content = None
                post_list_lines = []
                continue

            # 3. Arbitrary Content (Collect post-list lines)
            post_list_lines.append(line)
            
        # --- FINAL FLUSH ---
        # If the file ended while still in a chunk, append the remaining buffered content.
        if in_chunk:
            if last_list_line_content is not None:
                new_lines.append(last_list_line_content)
            if post_list_lines:
                new_lines.extend(post_list_lines)
            
        # --- WRITE OUTPUT ---
        
        if changes_made:
            # Join lines and use f.write() for safer output when newlines have been manipulated
            final_content = "".join(new_lines)
            with open(markdown_filepath, 'w', encoding='utf-8') as f:
                f.write(final_content)
            
            # Print success message regardless of is_debug value
            print(f"└ ✅ SUCCESS: File successfully processed: {markdown_filepath}. Missing <br> tags inserted.")
            return True
        else:
            # Print no-change message regardless of is_debug value
            print(f"└ ℹ️ NO CHANGES: All target chunks already contained the line-separated <br> tag in: {markdown_filepath} or no targets found.")
            return False

    except FileNotFoundError:
        print(f"❌ ERROR: File not found at {markdown_filepath}")
        return False
    except Exception as e:
        print(f"❌ ERROR DURING PROCESSING: {e}")
        return False








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
            print(f"└ ✅ CLEANED: File successfully processed: {markdown_filepath}")
            return True
        else:
            print(f"└ ℹ️ NO CHANGES: No elements found to clean in: {markdown_filepath}")
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
        print(f"└ ✅ Successfully removed CSS rules and updated: {markdown_filepath}")
    except Exception as e:
        print(f"└ Error writing to file: {e}")



def jupyter_to_md(
    path: str,
    output_dir: str = "./docs",
    no_input=True,
    execute=False,
    # chrome_path="/opt/homebrew/bin/chromium",
    # * change to ungoogled-chromium since chromium is depr
    chrome_path='/Applications/Chromium.app/Contents/MacOS/Chromium',
):
    """
    Converts a Jupyter notebook into a Markdown file with embedded plotly digrams 
    and styled dataframes.  
    ⚠️ `execute=True` will force the tables as html output due to conversion processes

    Args:
        path (str): The path to the Jupyter notebook file.
        output_dir (str, optional): The directory where the Markdown file will be generated. Defaults to "./docs".
        no_input (bool, optional): Whether to remove input cells from the Markdown output. Defaults to False.
        execute (bool, optional): Whether to execute the notebook before conversion. Defaults to True.
        chrome_path (str, optional): The path to the Chrome executable. Defaults to "/opt/homebrew/bin/chromium".
        convert_tables_to_png (bool, optional): Whether to convert dataframes to PNGs using dataframe-image. Defaults to True.

    Returns:
        None
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # * if this isnt set, plotly digrams will not be rendered
    os.environ["RENDERER"] = "svg"
    
    if execute:
        print("⚠️ execute=True will force the tables as html output instead of png")

    # # 1. Build the base CLI command
    # command = [
    #     "dataframe_image",
    #     shlex.quote(path),  # Safely quote the notebook path
    #     "--to=markdown",
    #     f"--output-dir={shlex.quote(output_dir)}",
    #     f"--chrome-path={shlex.quote(chrome_path)}",
    #     "--table-conversion=chrome",
    #     # "--center_df",
    #     # "--max_rows=50",
    #     # "--max_cols=25",
    # ]

    # # 2. Add optional/conditional arguments
    # if execute:
    #     command.append("--execute=True")
        
    # if no_input:
    #     command.append("--no-input")
        
    # # Note: save_notebook=False, limit=None, document_name=None, 
    # # and latex_command=None are handled by default/don't exist in the CLI call.

    # # 3. Execute the command
    # try:
    #     print(f"Executing command: {' '.join(command)}")
    #     # Use subprocess.run for simple command execution
    #     result = subprocess.run(
    #         command,
    #         check=True,  # Raises CalledProcessError for non-zero exit codes
    #         capture_output=True, 
    #         text=True
    #     )
    #     # print("Conversion successful.")
    #     # print("Output:\n", result.stdout) # Uncomment for debug output
        
    # except subprocess.CalledProcessError as e:
    #     print(f"└ Error during CLI conversion (Exit Code {e.returncode}):")
    #     print("└ Stderr:\n", e.stderr)
    #     # You might want to reraise the exception or handle it here
    #     raise

    # * use python API - this wont convert tables to PNG!
    print(f"Converting {path} to Markdown using dataframe-image python API ..")
    dfi.convert(
        path,
        to="markdown",
        # use='latex',
        center_df=True,
        max_rows=50,
        max_cols=25,
        execute=execute,
        save_notebook=False,        # * don't save notebook, it will duplicate the file
        limit=None,
        document_name=None,
        table_conversion="chrome",
        chrome_path=chrome_path,
        latex_command=None,
        output_dir=output_dir,
        no_input=no_input,
    )

    # * reset RENDERER
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
    # add_br_to_md(target_md_path, is_debug=True)

    enclose_block_as_code(
        markdown_filepath=target_md_path,
        start_token="<!-- START_TOKEN -->",
        stop_token="<!-- END_TOKEN -->",
        language="python",
        remove_token_lines=True,
    )
    enclose_block_as_code(
        markdown_filepath=target_md_path,
        start_token="┌──────",
        stop_token="└─────────",
        language="python",
        remove_token_lines=False,
    )

    
    


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
