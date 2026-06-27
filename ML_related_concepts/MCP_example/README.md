# MCP ML Example

Minimal [Model Context Protocol](https://modelcontextprotocol.io) example with an ML-themed server and client.

## Structure

```
MCP_example/
├── server/ml_server.py    # MCP server — registers tools with @server.tool()
├── client/ml_client.py    # MCP client — connects, lists, and calls tools
└── requirements.txt
```

## Usage

```bash
pip install -r requirements.txt
python client/ml_client.py server/ml_server.py
```

## What to notice

| File | MCP key concepts |
|------|-----------------|
| `server/ml_server.py` | `FastMCP`, `@server.tool()`, docstring-as-description, `server.run(transport="stdio")` |
| `client/ml_client.py` | `StdioServerParameters`, `stdio_client`, `ClientSession`, `initialize()`, `list_tools()`, `call_tool()` |
