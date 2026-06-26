import asyncio
import json
import sys

from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters


async def main(server_script: str):
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[server_script],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            result = await session.list_tools()
            print("=== Available Tools ===")
            for tool in result.tools:
                print(f"  {tool.name}: {tool.description or 'No description'}")

            print("\n=== sentiment_analysis ===")
            resp = await session.call_tool("sentiment_analysis",
                                           {"text": "This movie is absolutely amazing and wonderful!"})
            print(_fmt(resp))

            print("\n=== sentiment_analysis (negative) ===")
            resp = await session.call_tool("sentiment_analysis",
                                           {"text": "This is the worst terrible experience ever"})
            print(_fmt(resp))

            print("\n=== text_statistics ===")
            resp = await session.call_tool("text_statistics",
                                           {"text": "Machine learning is transforming the world"})
            print(_fmt(resp))

            print("\n=== cosine_similarity ===")
            resp = await session.call_tool("cosine_similarity",
                                           {"vec1": [1.0, 2.0, 3.0],
                                            "vec2": [4.0, 5.0, 6.0]})
            print(_fmt(resp))

            print("\n=== describe_dataset ===")
            csv_data = "feature1,feature2,label\n1.0,2.0,A\n3.0,4.0,B\n5.0,6.0,A"
            resp = await session.call_tool("describe_dataset",
                                           {"csv_content": csv_data})
            print(_fmt(resp))

            print("\n✅ All ML MCP tools executed successfully.")


from mcp.types import CallToolResult


def _fmt(resp: CallToolResult) -> str:
    prefix = "[ERROR] " if getattr(resp, "isError", False) else ""
    for content in resp.content:
        if hasattr(content, "text"):
            try:
                obj = json.loads(content.text)
                return prefix + json.dumps(obj, indent=2)
            except (json.JSONDecodeError, TypeError):
                return prefix + content.text
    return prefix + str(resp)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ml_client.py <path_to_server_script>")
        sys.exit(1)
    asyncio.run(main(sys.argv[1]))
