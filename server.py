# server.py
import re
import os
from typing import List, Dict, Any, Tuple, Optional

from pydantic import Field
from mcp.server.fastmcp import FastMCP, Context

# Define the editable region markers
BEGIN_MARKER_PATTERN = re.compile(r'<!--\s*#BeginEditable\s*"([^"]+)"\s*-->')
END_MARKER_PATTERN = re.compile(r'<!--\s*#EndEditable\s*-->')

# Create an MCP server
mcp = FastMCP("EditTextRegionServer", description="MCP Server for editing text file regions.")

# --- Helper Functions ---

def _read_file_lines(full_path: str) -> Tuple[List[str], str]:
    """Reads file lines and detects line ending."""
    lines = []
    line_ending = '\n'  # Default
    with open(full_path, 'r', encoding='utf-8', errors='replace', newline='') as f:
        first_line = f.readline()
        if '\r\n' in first_line:
            line_ending = '\r\n'
        elif '\r' in first_line:
            line_ending = '\r'
        f.seek(0)  # Go back to start
        lines = f.readlines()
    return lines, line_ending

def _write_file_lines(full_path: str, lines: List[str], line_ending: str):
    """Writes lines back to the file using the specified line ending."""
    # Use 'w' mode which truncates the file first
    # Preserve original encoding and detected line ending
    # Note: Python's text mode handles universal newlines on read.
    # When writing, setting newline='' prevents any translation, ensuring
    # lines are written exactly as provided (with their existing line endings).
    with open(full_path, 'w', encoding='utf-8', errors='replace', newline='') as f:
        f.writelines(lines)

def _get_region_content_lines(lines: List[str], region_info: Dict[str, Any]) -> List[str]:
    """Extracts the lines *within* a region (excluding markers)."""
    # Adjust for 0-based indexing and exclude marker lines
    start_index = region_info["start_line"]  # Line *after* the start marker
    end_index = region_info["end_line"] - 1  # Line *before* the end marker
    if start_index >= end_index:
        return []  # Region is empty or contains only markers
    else:
        return lines[start_index:end_index]

def _prepare_content_lines(content_string: str, line_ending: str) -> List[str]:
    """Converts a string to a list of lines with the specified line ending."""
    split_lines = content_string.splitlines()
    # Add the detected line_ending back to each line.
    content_lines = [line + line_ending for line in split_lines]
    return content_lines

def _update_region_content(file_path: str, region_name: str, new_region_content_str: str, ctx: Context) -> bool:
    """Core logic to replace the content of a region."""
    region_info = _find_region(file_path, region_name, ctx)
    if not region_info:
        return False  # Error already logged by _find_region

    full_path = os.path.abspath(file_path)
    try:
        original_lines, line_ending = _read_file_lines(full_path)
        new_content_lines = _prepare_content_lines(new_region_content_str, line_ending)

        # Construct the new file content
        start_marker_index = region_info["start_line"] - 1
        end_marker_index = region_info["end_line"] - 1

        new_file_lines = (
            original_lines[:start_marker_index + 1]  # Lines up to and including start marker
            + new_content_lines  # New content
            + original_lines[end_marker_index:]  # End marker line and subsequent lines
        )

        _write_file_lines(full_path, new_file_lines, line_ending)
        ctx.info(f"Successfully updated region '{region_name}' in file '{file_path}'")
        return True

    except Exception as e:
        ctx.error(f"Error writing region '{region_name}' to file {file_path}: {e}")
        raise  # Re-raise to report via MCP

# --- MCP Tools ---

@mcp.tool(name="get_regions", description="Lists all editable regions with names and line ranges from a given file.")
def get_regions(
    file_path: str = Field(description="The relative path to the file to analyze"),
    ctx: Context = Field(description="The MCP context object")
) -> List[Dict[str, Any]]:
    """
    Lists all editable regions with names and line ranges from a given file.

    Args:
        file_path (str): The relative path to the file to analyze.
        ctx (Context): The MCP context object.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing region information.
    """
    regions = []
    current_region_name = None
    current_region_start_line = -1
    full_path = os.path.abspath(file_path)

    if not os.path.exists(full_path):
        ctx.error(f"File not found: {file_path}")
        return []

    try:
        # Use helper to read lines, though we don't need line_ending here
        lines, _ = _read_file_lines(full_path)

        for line_num, line in enumerate(lines, 1):
            begin_match = BEGIN_MARKER_PATTERN.search(line)
            end_match = END_MARKER_PATTERN.search(line)

            if begin_match:
                if current_region_name is not None:
                    raise ValueError(f"Nested region detected: Found BeginEditable for '{begin_match.group(1)}' inside region '{current_region_name}' at line {line_num}")
                current_region_name = begin_match.group(1)
                current_region_start_line = line_num
                # ctx.info(f"Found start of region '{current_region_name}' at line {line_num}") # Less verbose

            elif end_match:
                if current_region_name is None:
                    raise ValueError(f"Mismatched marker: Found EndEditable without a matching BeginEditable at line {line_num}")
                # ctx.info(f"Found end of region '{current_region_name}' at line {line_num}") # Less verbose
                regions.append({
                    "name": current_region_name,
                    "start_line": current_region_start_line,
                    "end_line": line_num
                })
                current_region_name = None
                current_region_start_line = -1

        if current_region_name is not None:
             raise ValueError(f"Mismatched marker: Reached end of file while inside region '{current_region_name}' which started at line {current_region_start_line}")

    except Exception as e:
        ctx.error(f"Error processing file {file_path}: {e}")
        raise

    ctx.info(f"Found {len(regions)} regions in {file_path}")
    return regions

# Helper function to find a specific region (avoids code duplication)
# Now uses the refactored get_regions
def _find_region(file_path: str, region_name: str, ctx: Context) -> Optional[Dict[str, Any]]:
    """Finds a specific region by name in a file."""
    try:
        regions = get_regions(file_path, ctx) # Reuse the existing tool logic
        for region in regions:
            if region["name"] == region_name:
                return region
        ctx.error(f"Region '{region_name}' not found in file '{file_path}'")
        return None
    except Exception as e:
        # If get_regions raises an error (e.g., nested/mismatched markers), catch it here
        ctx.error(f"Failed to find region '{region_name}' due to error in get_regions: {e}")
        return None


@mcp.tool()
def get_region(
    file_path: str = Field(description="The relative path to the file"),
    region_name: str = Field(description="The name of the editable region")
) -> Optional[str]:
    """
    Retrieves the current content of a specified editable region.

    Args:
        file_path (str): The relative path to the file.
        region_name (str): The name of the editable region.

    Returns:
        Optional[str]: The current content of the region, or None if not found.
    """
    region_info = _find_region(file_path, region_name, ctx)
    if not region_info:
        return None

    full_path = os.path.abspath(file_path)
    try:
        lines, line_ending = _read_file_lines(full_path)
        region_lines = _get_region_content_lines(lines, region_info)
        # Join lines back, preserving original line endings implicitly via line_ending
        # Need to handle the last line potentially not having a line ending if the original didn't
        region_content = "".join(region_lines)
        return region_content

    except Exception as e:
        ctx.error(f"Error reading region '{region_name}' from file {file_path}: {e}")
        raise


@mcp.tool()
def put_region(
    file_path: str = Field(description="The relative path to the file"),
    region_name: str = Field(description="The name of the editable region"),
    new_content: str = Field(description="The new content to replace with"),
    ctx: Context = Field(description="The MCP context object")
) -> bool:
    """
    Replaces the content of a specified editable region.

    Args:
        file_path (str): The relative path to the file.
        region_name (str): The name of the editable region.
        new_content (str): The new content to replace with.
        ctx (Context): The MCP context object.

    Returns:
        bool: True if the replacement was successful, False otherwise.
    """
    return _update_region_content(file_path, region_name, new_content, ctx)


@mcp.tool()
def replace_in_region(
    file_path: str = Field(description="The relative path to the file"),
    region_name: str = Field(description="The name of the editable region"),
    old_text: str = Field(description="The text to find and replace"),
    new_text: str = Field(description="The text to replace with"),
    count: int = Field(description="Maximum number of occurrences to replace (-1 for all)", default=-1),
    ctx: Context = Field(description="The MCP context object", default=Context())
) -> bool:
    """
    Replaces occurrences of old_text with new_text within a specified region.

    Args:
        file_path (str): The relative path to the file.
        region_name (str): The name of the editable region.
        old_text (str): The text to find and replace.
        new_text (str): The text to replace with.
        count (int): Maximum number of occurrences to replace (-1 for all).
        ctx (Context): The MCP context object.

    Returns:
        bool: True if the replacement was successful, False otherwise.
    """
    current_content = get_region(file_path, region_name, ctx)
    if current_content is None:
        # Error already logged by get_region or _find_region
        return False

    # Perform replacement on the string content
    # Handle count parameter for limiting replacements
    if count == -1:
        modified_content = current_content.replace(old_text, new_text)
    else:
        modified_content = current_content.replace(old_text, new_text, count)

    if modified_content == current_content:
        ctx.info(f"No changes made: '{old_text}' not found or already replaced in region '{region_name}' of file '{file_path}'.")
        # Still return True as the operation didn't fail, just made no changes
        return True

    # Use the helper to write the modified content back
    return _update_region_content(file_path, region_name, modified_content, ctx)


@mcp.tool()
def delete_in_region(
    file_path: str = Field(description="The relative path to the file"),
    region_name: str = Field(description="The name of the editable region"),
    text_to_delete: str = Field(description="The text to find and delete"),
    ctx: Context = Field(description="The MCP context object", default=Context())
) -> bool:
    """
    Deletes the first occurrence of specified text within a region.

    Args:
        file_path (str): The relative path to the file.
        region_name (str): The name of the editable region.
        text_to_delete (str): The text to find and delete.
        ctx (Context): The MCP context object.

    Returns:
        bool: True if the deletion was successful, False otherwise.
    """
    # Use replace_in_region with count=1 and empty new_text
    return replace_in_region(
        file_path=file_path,
        region_name=region_name,
        old_text=text_to_delete,
        new_text="",
        count=1, # Delete only the first occurrence
        ctx=ctx
    )


@mcp.tool()
def insert_before_in_region(
    file_path: str = Field(description="The relative path to the file"),
    region_name: str = Field(description="The name of the editable region"),
    find_text: str = Field(description="The text to locate for insertion point"),
    text_to_insert: str = Field(description="The text to insert"),
    ctx: Context = Field(description="The MCP context object", default=Context())
) -> bool:
    """
    Inserts text immediately before the first occurrence of find_text within a region.

    Args:
        file_path (str): The relative path to the file.
        region_name (str): The name of the editable region.
        find_text (str): The text to locate for insertion point.
        text_to_insert (str): The text to insert.
        ctx (Context): The MCP context object.

    Returns:
        bool: True if insertion was successful, False if find_text not found or error occurred.
    """
    current_content = get_region(file_path, region_name, ctx)
    if current_content is None:
        return False

    try:
        index = current_content.index(find_text)
        modified_content = current_content[:index] + text_to_insert + current_content[index:]
        return _update_region_content(file_path, region_name, modified_content, ctx)
    except ValueError:
        ctx.error(f"Text '{find_text}' not found in region '{region_name}' of file '{file_path}'. Cannot insert.")
        return False
    except Exception as e:
        ctx.error(f"Error during insert_before operation: {e}")
        raise


@mcp.tool()
def insert_after_in_region(
    file_path: str = Field(description="The relative path to the file"),
    region_name: str = Field(description="The name of the editable region"),
    find_text: str = Field(description="The text to locate for insertion point"),
    text_to_insert: str = Field(description="The text to insert"),
    ctx: Context = Field(description="The MCP context object", default=Context())
) -> bool:
    """
    Inserts text immediately after the first occurrence of find_text within a region.

    Args:
        file_path (str): The relative path to the file.
        region_name (str): The name of the editable region.
        find_text (str): The text to locate for insertion point.
        text_to_insert (str): The text to insert.
        ctx (Context): The MCP context object.

    Returns:
        bool: True if insertion was successful, False if find_text not found or error occurred.
    """
    current_content = get_region(file_path, region_name, ctx)
    if current_content is None:
        return False

    try:
        index = current_content.index(find_text)
        insert_point = index + len(find_text)
        modified_content = current_content[:insert_point] + text_to_insert + current_content[insert_point:]
        return _update_region_content(file_path, region_name, modified_content, ctx)
    except ValueError:
        ctx.error(f"Text '{find_text}' not found in region '{region_name}' of file '{file_path}'. Cannot insert.")
        return False
    except Exception as e:
        ctx.error(f"Error during insert_after operation: {e}")
        raise


# Add a simple main block for direct execution if needed (optional)
if __name__ == "__main__":
    # This allows running the server directly using 'python server.py'
    # It's useful for local testing but not required for MCP integration.
    print("Starting MCP server directly...")
    mcp.run()