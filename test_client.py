import asyncio
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

async def run_tests():
    # Create server parameters for stdio connection
    server_params = StdioServerParameters(
        command="python",  # Executable
        args=["server.py"],  # Server script
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print("Available tools:", tools)

            # Create a test HTML file
            test_file = "test_regions.html"
            with open(test_file, "w") as f:
                f.write("""
<html>
<body>
<!-- #BeginEditable "test-region" -->
Original content
<!-- #EndEditable -->
</body>
</html>
""")

            # Test get_regions tool
            regions = await session.call_tool("get_regions", arguments={"file_path": test_file})
            print("Regions:", regions)

            # Test get_region tool
            region_content = await session.call_tool("get_region", arguments={"file_path": test_file, "region_name": "test-region"})
            print("Region content:", region_content)

            # Test put_region tool
            new_content = "New content"
            result = await session.call_tool("put_region", arguments={"file_path": test_file, "region_name": "test-region", "new_content": new_content})
            print("Put region result:", result)

            # Verify the change
            with open(test_file, "r") as f:
                print("File content after put_region:", f.read())

            # Test replace_in_region tool
            replace_result = await session.call_tool("replace_in_region", arguments={"file_path": test_file, "region_name": "test-region", "old_text": "New", "new_text": "Replaced"})
            print("Replace in region result:", replace_result)

            # Verify the change
            with open(test_file, "r") as f:
                print("File content after replace_in_region:", f.read())

            # Test delete_in_region tool
            delete_result = await session.call_tool("delete_in_region", arguments={"file_path": test_file, "region_name": "test-region", "text_to_delete": "Replaced"})
            print("Delete in region result:", delete_result)

            # Verify the change
            with open(test_file, "r") as f:
                print("File content after delete_in_region:", f.read())

            # Test insert_before_in_region tool
            insert_before_result = await session.call_tool("insert_before_in_region", arguments={"file_path": test_file, "region_name": "test-region", "find_text": "content", "text_to_insert": "Inserted before "})
            print("Insert before in region result:", insert_before_result)

            # Verify the change
            with open(test_file, "r") as f:
                print("File content after insert_before_in_region:", f.read())

            # Test insert_after_in_region tool
            insert_after_result = await session.call_tool("insert_after_in_region", arguments={"file_path": test_file, "region_name": "test-region", "find_text": "content", "text_to_insert": " inserted after"})
            print("Insert after in region result:", insert_after_result)

            # Verify the change
            with open(test_file, "r") as f:
                print("File content after insert_after_in_region:", f.read())

if __name__ == "__main__":
    asyncio.run(run_tests())