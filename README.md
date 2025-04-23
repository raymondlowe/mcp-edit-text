# MCP Edit Text Server

This repository contains the source code for an MCP server that allows editing text file regions.

## Running the Server

You can run the server using the following command:

```bash
uvx --from git+https://github.com/raymondlowe/mcp-edit-text mcp-edit-text
```

## Roo Code configuration

```
{
  "mcpServers": {
    ""FrontPage-DWT-Region-Editor": {": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/raymondlowe/mcp-edit-text",
        "mcp-edit-text"
      ]
    }
  }
}
```

## Usage

This MCP server provides several tools for editing text file regions. The available tools are:

1. `get_regions(file_path)`: Lists all editable regions with names and line ranges from a given file.
   - `file_path`: The relative path to the file to analyze.

2. `get_region(file_path, region_name, output_format="html", output_file_path=None)`: Retrieves the current content of a specified editable region.
   - `file_path`: The relative path to the file.
   - `region_name`: The name of the editable region.
   - `output_format`: The format of the output content ("html" or "markdown"). Defaults to "html".
   - `output_file_path`: Optional path to save the extracted content to. If provided, the content will be saved to this file.

3. `put_region(file_path, region_name, new_content=None, content_type="html", markdown_file_path=None)`: Replaces the content of a specified editable region. Content can be provided directly via `new_content` (as HTML or Markdown specified by `content_type`) or by specifying a `markdown_file_path`.
   - `file_path`: The relative path to the target HTML file.
   - `region_name`: The name of the editable region.
   - `new_content`: Optional. The new content string. Ignored if `markdown_file_path` is set.
   - `content_type`: Optional. Type of `new_content` ("html" or "markdown"). Ignored if `markdown_file_path` is set. Defaults to "html".
   - `markdown_file_path`: Optional. Path to a markdown file. If provided, its content is read, converted to HTML, and used as the new content, overriding `new_content` and `content_type`.

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

## Testing and Development

To run tests against the MCP server, you can use the provided `test_client.py` script. This script creates a test HTML file, connects to the MCP server, and exercises the available tools.

To run the tests, first ensure the MCP server is not running, then execute the following command in your terminal:

```bash
uv run test_client.py
```

This command will create a virtual environment, resolve dependencies, and run the tests. The output will show the results of each test, including the regions found, content retrieved, and modifications made to the test file.

## Examples

### Get region content as Markdown

```json
{
  "tool_name": "get_region",
  "arguments": {
    "file_path": "test_regions.html",
    "region_name": "content",
    "output_format": "markdown"
  }
}
```

### Get region content and save as Markdown file

```json
{
  "tool_name": "get_region",
  "arguments": {
    "file_path": "test_regions.html",
    "region_name": "content",
    "output_format": "markdown",
    "output_file_path": "extracted_content.md"
  }
}
```

### Put Markdown content into a region

```json
{
  "tool_name": "put_region",
  "arguments": {
    "file_path": "test_regions.html",
    "region_name": "content",
    "new_content": "# New Title\n\nThis is **markdown** content.",
    "content_type": "markdown"
  }
}
```

### Put content from a Markdown file into a region

```json
{
  "tool_name": "put_region",
  "arguments": {
    "file_path": "test_regions.html",
    "region_name": "content",
    "markdown_file_path": "input_content.md"
  }
}
