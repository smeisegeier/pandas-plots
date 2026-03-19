import argparse
import os
import re

import dataframe_image as dfi

PATH_CHROME = "/Applications/Chromium.app/Contents/MacOS/Chromium"
# os.environ["BROWSER_PATH"] = PATH_CHROME


def remove_duckdb_table_header(markdown_filepath: str, start_token: str, stop_token: str) -> bool:
    """
    Processes a Markdown file to find a block defined by start and stop tokens.
    Within that block, looks for lines matching DuckDB table header pattern:
    | type1 | type2 | type3 |
    and replaces the type names with blanks, leaving the pipes intact.

    Args:
        markdown_filepath (str): Path to the Markdown file.
        start_token (str): The token marking the beginning of the block.
        stop_token (str): The token marking the end of the block.

    Returns:
        bool: True if changes were made, False otherwise.
    """
    # Comprehensive list of DuckDB data types (case-insensitive matching)
    DUCKDB_TYPES = {
        # Integer types
        "tinyint",
        "int1",
        "smallint",
        "int2",
        "short",
        "integer",
        "int4",
        "int",
        "signed",
        "bigint",
        "int8",
        "long",
        "hugeint",
        "utinyint",
        "usmallint",
        "uinteger",
        "ubigint",
        "uhugeint",
        # Numeric types
        "decimal",
        "numeric",
        "float",
        "float4",
        "real",
        "float8",
        "double",
        "bignum",
        # Text types
        "varchar",
        "char",
        "bpchar",
        "text",
        "string",
        # Binary types
        "blob",
        "bytea",
        "binary",
        "varbinary",
        "bit",
        "bitstring",
        # Boolean type
        "boolean",
        "bool",
        "logical",
        # Temporal types
        "date",
        "time",
        "timestamp",
        "datetime",
        "timestamptz",
        "interval",
        # Special types
        "uuid",
        "json",
        "null",
        # Nested types
        "array",
        "list",
        "map",
        "struct",
        "union",
    }

    # Pattern to match lines like: | varchar | int16 | binary |
    # Also supports box-drawing characters: │ varchar │ int16 │ binary │
    # Captures pipe-separated values with optional whitespace
    duckdb_type_pattern = re.compile(r"^(\s*[\|│])(.+?)([\|│]\s*)$")

    try:
        with open(markdown_filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        new_lines = []
        changes_made = False
        state = 0  # 0: Searching, 1: Inside block

        for line in lines:
            lstripped = line.lstrip()

            if state == 0:
                if lstripped.startswith(start_token):
                    state = 1
                new_lines.append(line)
            elif state == 1:
                if lstripped.startswith(stop_token):
                    state = 0
                    new_lines.append(line)
                else:
                    # Check if line matches DuckDB table header pattern
                    match = duckdb_type_pattern.match(line.rstrip())
                    if match:
                        # Extract the content between pipes
                        content = match.group(2)

                        # Check if any part between pipes is a DuckDB type (exact match)
                        # Split by both regular pipe and box-drawing pipe
                        parts = re.split(r"[\|│]", content)
                        has_duckdb_type = any(
                            stripped and stripped.lower() in DUCKDB_TYPES for stripped in (p.strip() for p in parts)
                        )

                        # Delete the whole line if at least one DuckDB type is found
                        if has_duckdb_type:
                            changes_made = True
                        else:
                            new_lines.append(line)
                    else:
                        new_lines.append(line)

        if changes_made:
            with open(markdown_filepath, "w", encoding="utf-8") as f:
                f.writelines(new_lines)

        return changes_made

    except FileNotFoundError:
        return False


def enclose_block_as_code(
    markdown_filepath: str, start_token: str, stop_token: str, language: str = "", remove_token_lines: bool = True
) -> bool:
    """
    Processes a Markdown file to find a block defined by single, unique start and stop tokens.
    It encloses the content *between* them in a Markdown code block, modifying the file in-place.

    Args:
        markdown_filepath (str): Path to the Markdown file.
        start_token (str): The token marking the beginning of the content block (must be line prefix).
        stop_token (str): The token marking the end of the content block (must be line prefix).
        language (str): The language tag for the Markdown code block..
        remove_token_lines (bool): If True (default), the lines containing the start and stop tokens
                                are removed from the final output file. If False, they are included
                                *inside* the resulting code block.

    Returns:
        bool: True if changes were made, False otherwise.
    """

    try:
        with open(markdown_filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        new_lines = []
        changes_made = False
        block_buffer = []
        just_enclosed_block = False  # New flag to track when a block was just processed

        state = 0  # 0: Searching, 1: Collecting

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
                        block_start_line_index = i  # Token line is the start
                    else:
                        # EXCLUDE TOKEN: Do not append line to new_lines, effectively removing it.
                        block_start_line_index = i + 1  # Content starts next line

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
                        block_end_line_index = i  # Token line is the end
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
                        just_enclosed_block = True  # Set flag to consume next blank lines
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

            with open(markdown_filepath, "w", encoding="utf-8") as f:
                f.write(final_content)

            # Output only the requested line numbers (1-based for the user)
            print(
                f"└ ✅ SUCCESS: Block enclosed from line {block_start_line_index + 1} to {block_end_line_index + 1}. Tokens were {'included' if not remove_token_lines else 'removed'}."
            )
            return True
        else:
            print(
                f"└ ℹ️ NO CHANGES: No block found between '{start_token}' and '{stop_token}' in: {markdown_filepath} or block already enclosed."
            )
            return False

    except FileNotFoundError:
        print(f"❌ ERROR: File not found at {markdown_filepath}")
        return False
    except Exception as e:
        print(f"❌ ERROR DURING PROCESSING: {e}")
        return False


def add_br_to_md(markdown_filepath, is_debug=False):
    """
    Processes a Markdown file line-by-line to insert the '<br>' tag before
    markdown headings (##, ###, ####, etc.) if not already preceded by '<br>'.

    Args:
        markdown_filepath (str): Path to the Markdown file.
        is_debug (bool): If True, logs insertion details and prints final result messages.

    Returns:
        bool: True if changes were made, False otherwise.
    """
    try:
        with open(markdown_filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        new_lines = []
        changes_made = False

        def is_md_heading(line):
            """Check if line is a markdown heading (##, ###, etc. but not #)"""
            stripped = line.strip()
            return stripped.startswith("##")

        def is_any_heading(line):
            """Check if line is any markdown heading (#, ##, ###, etc.)"""
            stripped = line.strip()
            return stripped.startswith("#")

        def last_non_empty_line(line_list):
            """Get the last non-empty stripped line from a list"""
            for i in range(len(line_list) - 1, -1, -1):
                stripped = line_list[i].strip()
                if stripped:
                    return stripped
            return None

        for line in lines:
            if is_md_heading(line):
                # Check if the last non-empty line before this heading is '<br>'
                last_text = last_non_empty_line(new_lines)
                if last_text != "<br>" and not is_any_heading(last_text):
                    # Add <br> before the heading
                    new_lines.append("\n<br>\n\n")
                    changes_made = True
                    if is_debug:
                        print(f"└ DEBUG: Inserted <br> before heading in {os.path.basename(markdown_filepath)}")
                new_lines.append(line)
            else:
                new_lines.append(line)

        # --- WRITE OUTPUT ---

        if changes_made:
            final_content = "".join(new_lines)
            with open(markdown_filepath, "w", encoding="utf-8") as f:
                f.write(final_content)

            # Print success message regardless of is_debug value
            print(f"└ ✅ SUCCESS: File successfully processed: {markdown_filepath}. Missing <br> tags inserted.")
            return True
        else:
            # Print no-change message regardless of is_debug value
            print(
                f"└ ℹ️ NO CHANGES: All target chunks already contained the line-separated <br> tag in: {markdown_filepath} or no targets found."
            )
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
        with open(markdown_filepath, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # 2. STEP: REMOVE HTML STYLE BLOCK
        style_pattern = re.compile(r"<style\s*.*?>.*?</style>", re.DOTALL | re.IGNORECASE)
        content = re.sub(style_pattern, "", content)

        # 3. STEP: ENCLOSE ASCII TABLES WITH CODE FENCES
        # content = enclose_ascii_table_in_code_block(content)

        # 4. STEP: CLEAN UP EXCESSIVE BLANK LINES
        # Replaces three or more consecutive blank lines with two.
        content = re.sub(r"\n\s*\n\s*\n", "\n\n", content)

        if content != original_content:
            # 5. Write the cleaned content back to the file
            with open(markdown_filepath, "w", encoding="utf-8") as f:
                content = content.strip()  # Final global strip before writing to prevent extra blank lines at EOF
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
        with open(markdown_filepath, "r", encoding="utf-8") as f:
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
    css_to_remove_pattern = r"\n" + css_to_remove_pattern

    # Use re.sub() to replace the unwanted block with an empty string.
    # re.DOTALL (re.S) ensures the pattern can match across multiple lines.
    cleaned_content = re.sub(css_to_remove_pattern, "", html_or_md_content, flags=re.DOTALL)

    # Write the cleaned content back to the same file
    try:
        with open(markdown_filepath, "w", encoding="utf-8") as f:
            f.write(cleaned_content)
        print(f"└ ✅ Successfully removed CSS rules and updated: {markdown_filepath}")
    except Exception as e:
        print(f"└ Error writing to file: {e}")


def scale_images(markdown_filepath: str):
    """
    Processes a Markdown file to scale images using HTML width attribute.

    Looks for SCALE comments like <!-- SCALE-60% --> or <!-- SCALE-800 -->,
    checks if the next non-empty line contains an image declaration ![png](path) or ![svg](path),
    and replaces both with an HTML <img> tag with the specified width.

    Patterns:
    - SCALE-60% -> width="60%"
    - SCALE-800 -> width="800"

    Args:
        markdown_filepath: Path to the Markdown file.

    Returns:
        bool: True if changes were made, False otherwise.
    """
    try:
        with open(markdown_filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        new_lines = []
        changes_made = False
        i = 0

        while i < len(lines):
            line = lines[i]

            # Check if current line is a SCALE comment <!-- SCALE-60% --> or <!-- SCALE-800 -->
            scale_match = re.match(r"^\s*<!--\s*SCALE-(\d+)(%)?\s*-->\s*$", line)

            if scale_match:
                scale_value = scale_match.group(1)  # e.g., "60", "800"
                has_percent = scale_match.group(2) is not None  # True if % suffix present

                # Look for the next non-empty line to check for image declaration
                img_line_idx = i + 1
                while img_line_idx < len(lines) and not lines[img_line_idx].strip():
                    img_line_idx += 1

                img_path = None

                if img_line_idx < len(lines):
                    img_line = lines[img_line_idx]
                    # Check for image pattern ![png](...) or ![svg](...)
                    img_pattern = re.match(r"^!\[(png|svg)\]\(([^)]+)\)\s*$", img_line)

                    if img_pattern:
                        img_path = img_pattern.group(2)  # path to image

                if img_path is not None:
                    # Build width attribute value
                    if has_percent:
                        width_attr = f"{scale_value}%"
                    else:
                        width_attr = scale_value

                    # Replace with HTML img tag
                    html_img = f'<img src="{img_path}" width="{width_attr}">\n'
                    new_lines.append(html_img)

                    # Skip both SCALE comment and image line
                    i = img_line_idx + 1
                    changes_made = True
                else:
                    # No image found after SCALE comment, keep original line
                    new_lines.append(line)
                    i += 1
            else:
                new_lines.append(line)
                i += 1

        if changes_made:
            with open(markdown_filepath, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            print(f"└ ✅ SUCCESS: Image scaling applied to: {markdown_filepath}")
            return True
        else:
            print(f"└ ℹ️ NO CHANGES: No scalable images found in: {markdown_filepath}")
            return False

    except FileNotFoundError:
        print(f"❌ ERROR: File not found at {markdown_filepath}")
        return False
    except Exception as e:
        print(f"❌ ERROR DURING PROCESSING: {e}")
        return False


def jupyter_to_md(
    path: str,
    output_dir: str = "./docs",
    no_input=True,
    execute=False,
    center_df=True,
    # chrome_path="/opt/homebrew/bin/chromium",
    # * change to ungoogled-chromium since chromium is depr
    chrome_path=PATH_CHROME,
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
        center_df (bool, optional): Whether to center the dataframes. Defaults to True.
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
        center_df=center_df,
        max_rows=None,
        max_cols=None,
        execute=execute,
        save_notebook=False,  # * don't save notebook, it will duplicate the file
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
    target_md_path = os.path.join(output_dir, root + ".md")

    # 3. remove style
    # remove_pandas_style_from_md(target_md_path)
    remove_css_style_from_md(target_md_path)

    # 4. add br
    add_br_to_md(target_md_path, is_debug=False)

    enclose_block_as_code(
        markdown_filepath=target_md_path,
        start_token="<!-- START_TOKEN_PYTHON -->",
        stop_token="<!-- END_TOKEN_PYTHON -->",
        language="python",
        remove_token_lines=True,
    )

    enclose_block_as_code(
        markdown_filepath=target_md_path,
        start_token="<!-- START_TOKEN -->",
        stop_token="<!-- END_TOKEN -->",
        language="",
        remove_token_lines=True,
    )
    enclose_block_as_code(
        markdown_filepath=target_md_path,
        start_token="┌──────",
        stop_token="└─────────",
        language="",
        remove_token_lines=False,
    )

    remove_duckdb_table_header(
        markdown_filepath=target_md_path,
        start_token="┌──────",
        stop_token="└─────────",
    )

    scale_images(target_md_path)


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
    parser.add_argument(
        "--no-execute",
        action="store_true",
        help="Do not execute notebook before conversion (default: False - executes by default)",
    )
    parser.add_argument(
        "--chrome-path",
        default="/opt/homebrew/bin/chromium",
        help="Path to Chrome/Chromium executable (default: /opt/homebrew/bin/chromium)",
    )

    args = parser.parse_args()

    # Convert no_execute to execute (invert the logic)
    execute = not args.no_execute

    jupyter_to_md(
        path=args.path,
        output_dir=args.output_dir,
        no_input=args.no_input,
        execute=execute,
        chrome_path=args.chrome_path,
    )


if __name__ == "__main__":
    main()
