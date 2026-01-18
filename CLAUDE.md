# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
# Install in development mode
uv pip install -e .

# Run the MCP server directly
uv run src/bluesky_mcp/server.py

# Run with MCP Inspector (for debugging tool discovery)
npx @modelcontextprotocol/inspector uv --directory <path> run src/bluesky_mcp/server.py

# Kill running MCP server
pkill -f bluesky
```

## Authentication Setup

The server requires two environment variables:
- `BLUESKY_IDENTIFIER`: Your Bluesky handle (e.g., "username.bsky.social")
- `BLUESKY_APP_PASSWORD`: App Password generated from Bluesky account settings (NOT your login password)

Authentication is lazy - the Bluesky client authenticates on first tool invocation via `BlueSkyClient.ensure_client()`.

## Architecture

The MCP server follows a two-decorator pattern:

1. **Tool Registration** (`@server.list_tools()`): Returns a list of `types.Tool` objects defining name, description, and JSON Schema for parameters.

2. **Tool Execution** (`@server.call_tool()`): Single handler that dispatches to implementations based on tool name.

All tool implementations:
- Use `asyncio.to_thread()` to wrap blocking `atproto` API calls
- Return results as `types.TextContent` with JSON-serialized data
- Handle errors via try/except with user-friendly messages

## Tool Implementation Pattern

When adding a new tool:

1. Add a `types.Tool` definition to `handle_list_tools()` return value
2. Add an `elif name == "bluesky_your_tool":` block in `handle_call_tool()`
3. Extract arguments with `arguments.get("param", default_value)`
4. Make API calls via:
```python
await asyncio.to_thread(
    bluesky.client.app.bsky.namespace.method,
    {'param': value, 'other': value}
)
```
where the second argument is a dict of parameters.

**Important: The codebase only uses direct XRPC calls (`bluesky.client.app.bsky.namespace.method()`). Do NOT use wrapper methods like `bluesky.client.get_foo()` which were in an older version of this code.**

5. Return `[types.TextContent(type="text", text=json.dumps(response.model_dump(), indent=2))]`

For write operations (create/delete):
- Use `bluesky.client.com.atproto.repo.create_record()` or `delete_record()`
- These operations return success dictionaries, not Pydantic models
- Return directly with `[types.TextContent(type="text", text=json.dumps({...}))]` without calling `.model_dump()`

## List Management

List operations work with Bluesky's `app.bsky.graph.list` collection:
- Lists have URIs in format: `at://did:plc:xxx/app.bsky.graph.list/rkey`
- List items have URIs in format: `at://did:plc:xxx/app.bsky.graph.listitem/rkey`
- Purpose values are strings: `"app.bsky.graph.defs#curatelist"` or `"app.bsky.graph.defs#modlist"`

When parsing URIs for delete operations, split by `/`: `parts = uri.split('/')` where:
- `parts[0]` = "at:"
- `parts[2]` = repo (DID)
- `parts[3]` = collection
- `parts[4]` = rkey
