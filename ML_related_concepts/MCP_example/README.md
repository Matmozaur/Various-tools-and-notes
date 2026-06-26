# MCP ML Example

Model Context Protocol (MCP) example project demonstrating ML-related tools with both server and client.

## Project Structure

```
MCP_example/
├── server/          # MCP server exposing ML tools
│   └── ml_server.py
├── client/          # MCP client consuming those tools
│   └── ml_client.py
├── requirements.txt # shared dependencies
└── README.md
```

## Tools

| Tool               | Description                                       |
|--------------------|---------------------------------------------------|
| `sentiment_analysis` | Rule-based sentiment scoring (positive/negative/neutral) |
| `text_statistics`    | Character count, word count, avg word length      |
| `cosine_similarity`  | Cosine similarity between two float vectors       |
| `describe_dataset`   | Parse CSV and return basic statistics on numeric columns |

## Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Run the client (it spawns the server automatically via stdio)
python client/ml_client.py server/ml_server.py
```

## How it works

- The server uses `FastMCP` to register tools and listens on **stdio** transport.
- The client spawns the server as a subprocess, connects via `ClientSession`, lists tools, and invokes them with sample data.
- Communication follows the MCP (Model Context Protocol) JSON-RPC based protocol.
