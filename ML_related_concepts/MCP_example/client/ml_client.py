import asyncio
import json
import sys

from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.types import CallToolResult


async def main(server_script: str):
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[server_script],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("=== Available Tools ===")
            for t in tools.tools:
                print(f"  {t.name}: {t.description}")

            print("\n=== sentiment_analysis ===")
            resp = await session.call_tool(
                "sentiment_analysis",
                {"text": "This movie is absolutely amazing and wonderful!"},
            )
            print(_fmt(resp))

            print("\n=== cosine_similarity ===")
            resp = await session.call_tool(
                "cosine_similarity",
                {"vec1": [1.0, 2.0, 3.0], "vec2": [4.0, 5.0, 6.0]},
            )
            print(_fmt(resp))


def _fmt(resp: CallToolResult) -> str:
    prefix = "[ERROR] " if resp.isError else ""
    for c in resp.content:
        text = getattr(c, "text", str(c))
        try:
            return prefix + json.dumps(json.loads(text), indent=2)
        except (json.JSONDecodeError, TypeError):
            return prefix + text
    return prefix + str(resp)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ml_client.py <path_to_server_script>")
        sys.exit(1)
    asyncio.run(main(sys.argv[1]))
