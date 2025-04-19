# server.py
import re
import os
from typing import List, Dict, Any
from mcp.server.fastmcp import FastMCP, Context

# Define the editable region markers
BEGIN_MARKER_PATTERN = re.compile(r'<!--\s*#BeginEditable\s*"([^"]+)"\s*-->')
END_MARKER_PATTERN = re.compile(r'<!--\s*#EndEditable\s*-->')

# Create an MCP server
mcp = FastMCP("EditTextRegionServer", description="MCP Server for editing text file regions.")

@mcp.tool()
def get_regions(file_path: str, ctx: Context) -> List[Dict[str, Any]]:
    """
    Lists all editable regions with names and line ranges from a given file.

    Args:
        file_path: The relative path to the file to scan.
        ctx: The MCP context object.

    Returns:
        A list of dictionaries, each representing an editable region
        with 'name', 'start_line', and 'end_line'.
        Returns an empty list if the file doesn't exist or no regions are found.
        Raises an error for nested regions or mismatched markers.
    """
    regions = []
    current_region_name = None
    current_region_start_line = -1
    full_path = os.path.abspath(file_path) # Ensure we use absolute path for file ops

    # Basic security check (optional but recommended)
    # workspace_root = os.path.abspath('.') # Or get from context if available
    # if not full_path.startswith(workspace_root):
    #     raise ValueError("Access denied: File path is outside the allowed workspace.")

    if not os.path.exists(full_path):
        ctx.error(f"File not found: {file_path}")
        return [] # Return empty list if file doesn't exist

    try:
        # Read with universal newlines to handle different line endings consistently
        # Decode assuming UTF-8, but handle potential errors gracefully
        with open(full_path, 'r', encoding='utf-8', errors='replace', newline='') as f:
            lines = f.readlines() # Read all lines at once for easier indexing

        for line_num, line in enumerate(lines, 1):
            begin_match = BEGIN_MARKER_PATTERN.search(line)
            end_match = END_MARKER_PATTERN.search(line)

            if begin_match:
                if current_region_name is not None:
                    raise ValueError(f"Nested region detected: Found BeginEditable for '{begin_match.group(1)}' inside region '{current_region_name}' at line {line_num}")
                current_region_name = begin_match.group(1)
                current_region_start_line = line_num
                ctx.info(f"Found start of region '{current_region_name}' at line {line_num}")

            elif end_match:
                if current_region_name is None:
                    raise ValueError(f"Mismatched marker: Found EndEditable without a matching BeginEditable at line {line_num}")
                ctx.info(f"Found end of region '{current_region_name}' at line {line_num}")
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
        raise # Re-raise the exception to report it via MCP

    ctx.info(f"Found {len(regions)} regions in {file_path}")
    return regions

# Helper function to find a specific region (avoids code duplication)
def _find_region(file_path: str, region_name: str, ctx: Context) -> Dict[str, Any] | None:
    """Finds a specific region by name in a file."""
    regions = get_regions(file_path, ctx) # Reuse the existing tool logic
    for region in regions:
        if region["name"] == region_name:
            return region
    ctx.error(f"Region '{region_name}' not found in file '{file_path}'")
    return None

@mcp.tool()
def get_region(file_path: str, region_name: str, ctx: Context) -> str | None:
    """
    Retrieves the current content of a specified editable region.

    Args:
        file_path: The relative path to the file.
        region_name: The name of the editable region to retrieve.
        ctx: The MCP context object.

    Returns:
        The content of the region as a string, excluding the marker lines.
        Returns None if the file or region is not found.
    """
    region_info = _find_region(file_path, region_name, ctx)
    if not region_info:
        return None # Error already logged by _find_region

    full_path = os.path.abspath(file_path)
    try:
        # Read with universal newlines
        with open(full_path, 'r', encoding='utf-8', errors='replace', newline='') as f:
            lines = f.readlines()

        # Extract content between markers (exclusive)
        # Adjust for 0-based indexing and exclude marker lines
        start_index = region_info["start_line"] # Line after the start marker
        end_index = region_info["end_line"] - 1 # Line before the end marker

        if start_index >= end_index:
             # Region is empty or contains only markers
             return ""
        else:
            region_content = "".join(lines[start_index:end_index])
            return region_content

    except Exception as e:
        ctx.error(f"Error reading region '{region_name}' from file {file_path}: {e}")
        raise

@mcp.tool()
def put_region(file_path: str, region_name: str, new_content: str, ctx: Context) -> bool:
    """
    Replaces the content of a specified editable region.

    Args:
        file_path: The relative path to the file.
        region_name: The name of the editable region to modify.
        new_content: The new content to place inside the region.
        ctx: The MCP context object.

    Returns:
        True if the region was updated successfully, False otherwise.
    """
    region_info = _find_region(file_path, region_name, ctx)
    if not region_info:
        return False # Error already logged by _find_region

    full_path = os.path.abspath(file_path)
    try:
        # Read original file content and detect line endings
        original_lines = []
        line_ending = '\n' # Default
        with open(full_path, 'r', encoding='utf-8', errors='replace', newline='') as f:
            first_line = f.readline()
            if '\r\n' in first_line:
                line_ending = '\r\n'
            elif '\r' in first_line:
                 line_ending = '\r'
            f.seek(0) # Go back to start
            original_lines = f.readlines()


        # Prepare new content lines, ensuring consistent line endings.
        # Use splitlines() to handle various newline types correctly.
        # It splits the string at line breaks and returns a list of lines
        # *without* the line break characters.
        split_lines = new_content.splitlines()

        # Add the detected line_ending to each line from splitlines().
        # This ensures that each line of the new content ends with the
        # correct newline character, and the subsequent EndEditable marker
        # will start on its own new line.
        new_content_lines = [line + line_ending for line in split_lines]

        # Example: If new_content is "line1\nline2" and line_ending is '\n',
        # split_lines = ['line1', 'line2']
        # new_content_lines = ['line1\n', 'line2\n']
        # Example: If new_content is ""
        # split_lines = []
        # new_content_lines = []


        # Construct the new file content
        # Adjust for 0-based indexing
        start_marker_index = region_info["start_line"] - 1
        end_marker_index = region_info["end_line"] - 1

        new_file_lines = (
            original_lines[:start_marker_index + 1] # Lines up to and including start marker
            + new_content_lines # New content
            + original_lines[end_marker_index:] # End marker line and subsequent lines
        )

        # Write the modified content back to the file
        # Use 'w' mode which truncates the file first
        # Preserve original encoding and detected line ending
        with open(full_path, 'w', encoding='utf-8', errors='replace', newline='') as f:
            f.writelines(new_file_lines)

        ctx.info(f"Successfully updated region '{region_name}' in file '{file_path}'")
        return True

    except Exception as e:
        ctx.error(f"Error writing region '{region_name}' to file {file_path}: {e}")
        raise # Re-raise to report via MCP


# Add a simple main block for direct execution if needed (optional)
if __name__ == "__main__":
    # This allows running the server directly using 'python server.py'
    # It's useful for local testing but not required for MCP integration.
    print("Starting MCP server directly...")
    mcp.run()