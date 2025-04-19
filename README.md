# MCP Edit Text Server

This repository contains the source code for an MCP server that allows editing text file regions.

## Running the Server

You can run the server using the following command:

```bash
uvx --from git+https://github.com/raymondclowe/mcp-edit-text mcp-edit-text
```

## Usage

This MCP server provides several tools for editing text file regions. The available tools are:

1. `get_regions(file_path)`: Lists all editable regions with names and line ranges from a given file.
   - `file_path`: The relative path to the file to analyze.

2. `get_region(file_path, region_name)`: Retrieves the current content of a specified editable region.
   - `file_path`: The relative path to the file.
   - `region_name`: The name of the editable region.

3. `put_region(file_path, region_name, new_content)`: Replaces the content of a specified editable region.
   - `file_path`: The relative path to the file.
   - `region_name`: The name of the editable region.
   - `new_content`: The new content to replace with.

4. `replace_in_region(file_path, region_name, old_text, new_text, count=-1)`: Replaces occurrences of `old_text` with `new_text` within a specified region.
   - `file_path`: The relative path to the file.
   - `region_name`: The name of the editable region.
   - `old_text`: The text to find and replace.
   - `new_text`: The text to replace with.
   - `count`: Maximum number of occurrences to replace (-1 for all).

5. `delete_in_region(file_path, region_name, text_to_delete)`: Deletes the first occurrence of specified text within a region.
   - `file_path`: The relative path to the file.
   - `region_name`: The name of the editable region.
   - `text_to_delete`: The text to find and delete.

6. `insert_before_in_region(file_path, region_name, find_text, text_to_insert)`: Inserts text immediately before the first occurrence of `find_text` within a region.
   - `file_path`: The relative path to the file.
   - `region_name`: The name of the editable region.
   - `find_text`: The text to locate for insertion point.
   - `text_to_insert`: The text to insert.

7. `insert_after_in_region(file_path, region_name, find_text, text_to_insert)`: Inserts text immediately after the first occurrence of `find_text` within a region.
   - `file_path`: The relative path to the file.
   - `region_name`: The name of the editable region.
   - `find_text`: The text to locate for insertion point.
   - `text_to_insert`: The text to insert.

These tools enable various text editing operations within specified regions of text files.