import argparse
import os
import re
import shutil
import subprocess
from typing import Literal

import dataframe_image as dfi
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

# * change to ungoogled-chromium since chromium is depr
PATH_CHROME = "/Applications/Chromium.app/Contents/MacOS/Chromium"
# os.environ["BROWSER_PATH"] = PATH_CHROME


def _remove_duckdb_table_header(markdown_filepath: str, start_token: str, stop_token: str) -> bool:
    """
    Processes a Markdown file to find a block defined by start and stop tokens.
    Removes line 3 (the type header line) within each block.

    Structure assumed:
    - Line 1: start_token
    - Line 2: column headers
    - Line 3: type headers (to be removed)
    - Line 4+: data rows and separators

    Args:
        markdown_filepath (str): Path to the Markdown file.
        start_token (str): The token marking the beginning of the block.
        stop_token (str): The token marking the end of the block.

    Returns:
        bool: True if changes were made, False otherwise.
    """
    try:
        with open(markdown_filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        new_lines = []
        changes_made = False
        state = 0  # 0: Searching, 1: Found start_token, 2: Found header line

        for line in lines:
            lstripped = line.lstrip()

            if state == 0:
                if lstripped.startswith(start_token):
                    state = 1
                new_lines.append(line)
            elif state == 1:
                # This is line 2 (header line) - keep it and move to state 2
                state = 2
                new_lines.append(line)
            elif state == 2:
                # This is line 3 (type line) - skip it
                changes_made = True
                if lstripped.startswith(stop_token):
                    state = 0
                    new_lines.append(line)
                else:
                    state = 0
            else:
                new_lines.append(line)

        if changes_made:
            with open(markdown_filepath, "w", encoding="utf-8") as f:
                f.writelines(new_lines)

        return changes_made

    except FileNotFoundError:
        return False


def _enclose_block_as_code(
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


def _add_br_to_md(markdown_filepath, is_debug=False):
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


def _remove_css_style_from_md(markdown_filepath: str):
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


def _scale_images(markdown_filepath: str):
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


def _cleanse_for_pdf(markdown_filepath: str) -> bool:
    try:
        with open(markdown_filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        new_lines = [line for line in lines if not re.match(r"^> \[!.*\]", line)]
        if len(new_lines) != len(lines):
            with open(markdown_filepath, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            print(f"└ ✅ SUCCESS: Callout lines removed from: {markdown_filepath}")
            return True
        else:
            print(f"└ ℹ️ NO CHANGES: No callout lines found in: {markdown_filepath}")
            return False

    except FileNotFoundError:
        print(f"❌ ERROR: File not found at {markdown_filepath}")
        return False
    except Exception as e:
        print(f"❌ ERROR DURING PROCESSING: {e}")
        return False


_GERMAN_REPLACEMENTS: list[tuple[str, str]] = [
    ("Table of contents", "Inhalt"),
]


def _apply_german_translations(markdown_filepath: str) -> bool:
    try:
        with open(markdown_filepath, "r", encoding="utf-8") as f:
            content = f.read()

        original = content
        for source, target in _GERMAN_REPLACEMENTS:
            content = content.replace(source, target)

        if content != original:
            with open(markdown_filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"└ ✅ SUCCESS: German translations applied to: {markdown_filepath}")
            return True
        else:
            print(f"└ ℹ️ NO CHANGES: No translatable text found in: {markdown_filepath}")
            return False

    except FileNotFoundError:
        print(f"❌ ERROR: File not found at {markdown_filepath}")
        return False
    except Exception as e:
        print(f"❌ ERROR DURING PROCESSING: {e}")
        return False


def _fix_toc_for_gitlab(markdown_filepath):
    if not os.path.exists(markdown_filepath):
        print(f"Error: File '{markdown_filepath}' not found.")
        return

    # Read the original content
    with open(markdown_filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Pattern 1: Headers like `## <a id='...'></a>[text](#toc0_)`
    # Moves anchor to the line below and uses name attribute
    pattern_headers = r"^(#+)\s*<a\s+(?:id|name)=['\"](.*?)['\"]\s*>\s*</a>\s*\[(.*?)\]\(#toc0_\)"
    replacement_headers = r"\1 [\3](#toc0_)\n<a name='\2'></a>"
    content = re.sub(pattern_headers, replacement_headers, content, flags=re.MULTILINE)

    # Pattern 2: Bold text like `**Table of contents**<a id='...'></a>`
    # Moves anchor to the line below and uses name attribute
    pattern_bold = r"\*\*(.*?)\*\*\s*<a\s+(?:id|name)=['\"](.*?)['\"]\s*>\s*</a>"
    replacement_bold = r"**\1**\n<a name='\2'></a>"
    content = re.sub(pattern_bold, replacement_bold, content)

    # Overwrite the original file
    with open(markdown_filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"└ ✅ SUCCESS: File '{markdown_filepath}' has been updated for GitLab.")


def _apply_system_theming(markdown_filepath: str) -> bool:
    """
    Scans a Markdown file for ![alt](image) and <img src="..."> tags and replaces each
    with a <picture> element that selects between light and dark variants via
    prefers-color-scheme, provided a matching dark image exists in _files_dark/.
    Extra attributes (e.g. width) on <img> tags are preserved.
    """
    try:
        with open(markdown_filepath, "r", encoding="utf-8") as f:
            content = f.read()

        md_dir = os.path.dirname(os.path.abspath(markdown_filepath))
        original_content = content

        def _picture_block(src: str, alt: str, extra_attrs: str) -> str | None:
            if "_files/" not in src or "_files_dark/" in src:
                return None
            dark_src = src.replace("_files/", "_files_dark/", 1)
            if not os.path.exists(os.path.join(md_dir, dark_src)):
                return None
            img_tag = f'<img alt="{alt}" src="{src}"{extra_attrs}>'
            return (
                f"<picture>\n"
                f'  <source media="(prefers-color-scheme: dark)" srcset="{dark_src}">\n'
                f'  <source media="(prefers-color-scheme: light)" srcset="{src}">\n'
                f"  {img_tag}\n"
                f"</picture>"
            )

        _ALT_TOKEN = r"<!-- ALT_TEXT:(.*?)-->"
        _OPT_ALT_LEAD = r"(?:" + _ALT_TOKEN + r"\s*)?"
        _OPT_ALT_TRAIL = r"(?:\s*" + _ALT_TOKEN + r")?"

        def replace_md_image(match: re.Match) -> str:
            # groups: 1=leading token, 2=md alt, 3=src, 4=trailing token
            alt_from_token = match.group(1) or match.group(4)
            md_alt, src = match.group(2), match.group(3)
            alt = alt_from_token.strip() if alt_from_token else md_alt
            return _picture_block(src, alt, "") or f"![{md_alt}]({src})"

        def replace_html_img(match: re.Match) -> str:
            # groups: 1=leading token, 2=src, 3=rest attrs, 4=trailing token
            alt_from_token = match.group(1) or match.group(4)
            src = match.group(2)
            rest = match.group(3).strip()
            extra = f" {rest}" if rest else ""
            if alt_from_token is not None:
                alt = alt_from_token.strip()
            else:
                alt_match = re.search(r'alt="([^"]*)"', rest)
                alt = alt_match.group(1) if alt_match else ""
            # remove alt from extra_attrs to avoid duplication
            extra = re.sub(r'\s*alt="[^"]*"', "", extra)
            orig_img = f'<img src="{src}"{" " + rest if rest else ""}>'
            return _picture_block(src, alt, extra) or orig_img

        def replace_picture(match: re.Match) -> str:
            # groups: 1=leading token, 2=full <picture>…</picture>, 3=trailing token
            alt_from_token = match.group(1) or match.group(3)
            if alt_from_token is None:
                return match.group(0)
            alt = alt_from_token.strip()
            return re.sub(r'alt="[^"]*"', f'alt="{alt}"', match.group(2), count=1)

        content = re.sub(
            _OPT_ALT_LEAD + r"!\[([^\]]*)\]\(([^)]+)\)" + _OPT_ALT_TRAIL,
            replace_md_image,
            content,
        )
        content = re.sub(
            _OPT_ALT_LEAD + r'<img src="([^"]+)"([^>]*)>' + _OPT_ALT_TRAIL,
            replace_html_img,
            content,
        )
        # patch alt in already-converted <picture> elements
        content = re.sub(
            _OPT_ALT_LEAD + r"(<picture>.*?</picture>)" + _OPT_ALT_TRAIL,
            replace_picture,
            content,
            flags=re.DOTALL,
        )

        if content != original_content:
            with open(markdown_filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"└ ✅ SUCCESS: GitHub theming applied to: {markdown_filepath}")
            return True
        else:
            print(f"└ ℹ️ NO CHANGES: No themeable images found in: {markdown_filepath}")
            return False

    except FileNotFoundError:
        print(f"❌ ERROR: File not found at {markdown_filepath}")
        return False
    except Exception as e:
        print(f"❌ ERROR DURING PROCESSING: {e}")
        return False


def _reconcile_dark_filenames(light_dir: str, dark_dir: str) -> None:
    """
    Renames files in dark_dir to match light_dir where cell index and extension agree
    but the output index within the cell differs (e.g. output_8_8.svg → output_8_7.svg).
    Only renames when there is exactly one candidate on each side for a given cell+ext pair.
    """
    if not os.path.isdir(light_dir) or not os.path.isdir(dark_dir):
        return

    # Build map: (cell_index, ext) -> filename  for each side
    def _index_files(directory):
        result: dict[tuple[str, str], str] = {}
        for fname in os.listdir(directory):
            m = re.match(r"^(output_(\d+)_\d+)(\.\w+)$", fname)
            if not m:
                continue
            cell_idx = m.group(2)
            ext = m.group(3)
            key = (cell_idx, ext)
            if key in result:
                result[key] = None  # ambiguous — more than one file for this cell+ext
            else:
                result[key] = fname
        return result

    light_map = _index_files(light_dir)
    dark_map = _index_files(dark_dir)

    for key, light_name in light_map.items():
        dark_name = dark_map.get(key)
        if light_name is None or dark_name is None:
            continue
        if light_name != dark_name:
            old_path = os.path.join(dark_dir, dark_name)
            new_path = os.path.join(dark_dir, light_name)
            os.rename(old_path, new_path)
            print(f"└ ✅ reconciled dark filename: {dark_name} → {light_name}")


def _single_run(
    path: str,
    to: str,
    center_df: bool,
    chrome_path: str,
    output_dir: str,
    no_input: bool,
    execute: bool,
    root: str,
) -> str:
    """Pre-execute (if requested), convert notebook to markdown, rename files dir. Returns md path."""
    if execute:
        print(f"Pre-executing {path} ..")
        with open(path) as f:
            nb = nbformat.read(f, as_version=4)
        ep = ExecutePreprocessor(timeout=600, kernel_name="python3")
        ep.preprocess(nb, {"metadata": {"path": os.path.dirname(os.path.abspath(path))}})
        _exec_path = path.replace(".ipynb", "_executed.ipynb")
        with open(_exec_path, "w") as f:
            nbformat.write(nb, f)
        _convert_path = _exec_path
    else:
        _convert_path = path

    print(f"Converting {path} to Markdown using dataframe-image python API ..")
    try:
        dfi.convert(
            _convert_path,
            to=to,
            center_df=center_df,
            max_rows=None,
            max_cols=None,
            execute=False,
            save_notebook=False,
            limit=None,
            document_name=root,
            table_conversion="chrome",
            chrome_path=chrome_path,
            latex_command=None,
            output_dir=output_dir,
            no_input=no_input,
        )
    finally:
        if execute:
            os.remove(_exec_path)

    if execute:
        _exec_files_dir = os.path.join(output_dir, root + "_executed_files")
        _orig_files_dir = os.path.join(output_dir, root + "_files")
        target_md_path = os.path.join(output_dir, root + ".md")
        if os.path.exists(_exec_files_dir):
            if os.path.exists(_orig_files_dir):
                shutil.rmtree(_orig_files_dir)
            os.rename(_exec_files_dir, _orig_files_dir)
            with open(target_md_path, "r") as f:
                content = f.read()
            content = content.replace(root + "_executed_files", root + "_files")
            with open(target_md_path, "w") as f:
                f.write(content)

    return os.path.join(output_dir, root + ".md")


def jupyter_to_md(
    path: str,
    to: Literal["markdown", "pdf"] = "markdown",
    output_dir: str = "./docs",
    no_input=True,
    execute=False,
    center_df=True,
    chrome_path=PATH_CHROME,
    theme: Literal["dark", "light", "system"] | None = None,
    is_german: bool = False,
    to_pdf: bool = False,
):
    """
    Converts a Jupyter notebook into a Markdown file with embedded plotly diagrams
    and styled dataframes.

    Uses the following env variables:
        `RENDERER`: is set to `svg` but reset to "" after
        `GIT_HOST`: if `gitlab`, fix the TOC html tags
        `OVERRIDE`: this forces the notebook to not override theme / renderer

    If theme="system": forces `execute`, overrides theme

    Args:
        path (str): The path to the Jupyter notebook file.
        output_dir (str, optional): The directory where the Markdown file will be generated. Defaults to "./docs".
        no_input (bool, optional): Whether to remove input cells from the Markdown output. Defaults to False.
        execute (bool, optional): Whether to execute the notebook before conversion. Defaults to False.
        to (Literal["markdown", "pdf"], optional): The output format. Defaults to "markdown". ⚠️ `pdf` is experimental
        center_df (bool, optional): Whether to center the dataframes. Defaults to True.
        chrome_path (str, optional): The path to the Chrome executable.
        theme (Literal["dark", "light", "system"] | None, optional):
            None     — notebook controls theme via setup_rendering (default).
            "light"  — single run, images in _files.
            "dark"   — single run, images renamed to _files_dark, markdown refs updated.
            "system" — double run (dark + light); wraps images in <picture> for prefers-color-scheme.
        is_german (bool, optional): Whether to use german language for some auto generated text
        to_pdf (bool, optional): does not convert, but makes the markdown pdf friendly (eg. strips out github callouts)

    Returns:
        None
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    root = os.path.splitext(os.path.basename(path))[0]
    target_md_path = os.path.join(output_dir, root + ".md")
    
    # suppress dark theme when pdf
    if to_pdf:
        theme = "light"

    _theme_note = (
        f"{theme}"
        if (execute or theme == "system" or theme is None)
        else "⚠️ is taken from ipynb source since `execute` is not set!"
    )
    print(f"[theme: {_theme_note}]")

    # * set override to prevent theme setting in the notebook
    # if theme is not None:
    os.environ["OVERRIDE"] = "1"

    if theme == "system":
        # Run 1: dark — execute, convert, then stash images in _files_dark
        print("[1/2] dark theme ..")
        os.environ["THEME"] = "dark"
        _single_run(
            path=path,
            to=to,
            center_df=center_df,
            chrome_path=chrome_path,
            output_dir=output_dir,
            no_input=no_input,
            execute=True,
            root=root,
        )
        _files_dir = os.path.join(output_dir, root + "_files")
        _dark_files_dir = os.path.join(output_dir, root + "_files_dark")
        if os.path.exists(_files_dir):
            if os.path.exists(_dark_files_dir):
                shutil.rmtree(_dark_files_dir)
            os.rename(_files_dir, _dark_files_dir)

        # Run 2: light — execute, convert; _files stays as the default referenced by the markdown
        print("[2/2] light theme ..")
        os.environ["THEME"] = "light"
        _single_run(
            path=path,
            to=to,
            center_df=center_df,
            chrome_path=chrome_path,
            output_dir=output_dir,
            no_input=no_input,
            execute=True,
            root=root,
        )
        _reconcile_dark_filenames(
            light_dir=os.path.join(output_dir, root + "_files"),
            dark_dir=os.path.join(output_dir, root + "_files_dark"),
        )
    else:
        if theme is not None:
            os.environ["THEME"] = theme
        _single_run(path, to, center_df, chrome_path, output_dir, no_input, execute, root)
        if theme == "dark":
            _files_dir = os.path.join(output_dir, root + "_files")
            _dark_files_dir = os.path.join(output_dir, root + "_files_dark")
            if os.path.exists(_files_dir):
                if os.path.exists(_dark_files_dir):
                    shutil.rmtree(_dark_files_dir)
                os.rename(_files_dir, _dark_files_dir)
                with open(target_md_path, "r") as f:
                    content = f.read()
                content = content.replace(root + "_files/", root + "_files_dark/")
                with open(target_md_path, "w") as f:
                    f.write(content)
                print("└ ✅ renamed _files → _files_dark and updated markdown references.")

    os.environ.pop("THEME", None)
    os.environ.pop("OVERRIDE", None)

    # * reset RENDERER
    os.environ["RENDERER"] = ""  # <None> does not work

    # * remove style
    _remove_css_style_from_md(target_md_path)

    # 4. add br
    _add_br_to_md(target_md_path, is_debug=False)

    _enclose_block_as_code(
        markdown_filepath=target_md_path,
        start_token="<!-- START_TOKEN_PYTHON -->",
        stop_token="<!-- END_TOKEN_PYTHON -->",
        language="python",
        remove_token_lines=True,
    )

    _enclose_block_as_code(
        markdown_filepath=target_md_path,
        start_token="<!-- START_TOKEN -->",
        stop_token="<!-- END_TOKEN -->",
        language="",
        remove_token_lines=True,
    )
    _enclose_block_as_code(
        markdown_filepath=target_md_path,
        start_token="┌──────",
        stop_token="└─────────",
        language="",
        remove_token_lines=False,
    )

    _remove_duckdb_table_header(
        markdown_filepath=target_md_path,
        start_token="┌──────",
        stop_token="└─────────",
    )

    _scale_images(target_md_path)

    if theme == "system":
        _apply_system_theming(target_md_path)

    if os.getenv("GIT_HOST") == "gitlab":
        _fix_toc_for_gitlab(target_md_path)

    if to_pdf:
        _cleanse_for_pdf(target_md_path)

    if is_german:
        _apply_german_translations(target_md_path)


# * Keep the original function name as primary, alias if needed
def j2md(*args, **kwargs):
    return jupyter_to_md(*args, **kwargs)


def jupyter_to_html(
    path: str,
    output_dir: str = "./docs",
    no_input: bool = True,
    execute: bool = False,
    use_base64: bool = False,
    is_german: bool = False,
):
    """
    Converts a Jupyter notebook to HTML using `jupyter nbconvert`.

    Args:
        path (str): Path to the Jupyter notebook file.
        output_dir (str): Directory where the HTML file will be saved. Defaults to "./docs".
        no_input (bool): Exclude input cells from the output. Defaults to True.
        execute (bool): Execute the notebook before converting. Defaults to False.
        use_base64 (bool): Use base64 inline encoding for images. Defaults to False (i.e. images are stored in a folder).
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    command = [
        "jupyter",
        "nbconvert",
        "--to",
        "html",
        f"--output-dir={output_dir}",
        path,
    ]

    if no_input:
        command.append("--no-input")
    if execute:
        command.append("--execute")
    if not use_base64:
        command.append("--HTMLExporter.preprocessors=['nbconvert.preprocessors.ExtractOutputPreprocessor']")

    print(f"Converting {path} to HTML ..")
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        root = os.path.splitext(os.path.basename(path))[0]
        target_html_path = os.path.join(output_dir, root + ".html")
        print(f"└ ✅ SUCCESS: {target_html_path}")
        if is_german:
            _apply_german_translations(target_html_path)
    except subprocess.CalledProcessError as e:
        print(f"└ ❌ ERROR (exit {e.returncode}):\n{e.stderr}")
        raise


def cli_j2md():
    parser = argparse.ArgumentParser(description="Convert Jupyter notebooks to Markdown")
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

    jupyter_to_md(
        path=args.path,
        output_dir=args.output_dir,
        no_input=args.no_input,
        execute=not args.no_execute,
        chrome_path=args.chrome_path,
    )


def cli_j2html():
    parser = argparse.ArgumentParser(description="Convert Jupyter notebooks to HTML")
    parser.add_argument("path", help="Path to the Jupyter notebook to convert")
    parser.add_argument("--output-dir", "-o", default="./docs", help="Output directory (default: ./docs)")
    parser.add_argument("--no-input", action="store_true", help="Exclude input cells in output (default: False)")
    parser.add_argument("--execute", action="store_true", help="Execute notebook before conversion (default: False)")
    parser.add_argument("--use-base64", action="store_true", help="Inline images as base64 (default: False)")

    args = parser.parse_args()

    jupyter_to_html(
        path=args.path,
        output_dir=args.output_dir,
        no_input=args.no_input,
        execute=args.execute,
        use_base64=args.use_base64,
    )
