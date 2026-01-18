# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Model Context Protocol (MCP) server that exposes Bluesky social network APIs. The server implements a standardized MCP interface that allows Claude to interact with Bluesky through a set of tools. The implementation uses the `atproto` library for API calls and the `mcp` library for protocol handling.

## Development Commands

```bash
# Install in development mode with dependencies
uv pip install -e .

# Run the MCP server directly
uv run src/bluesky_mcp/server.py

# Run with MCP Inspector for debugging and tool discovery
npx @modelcontextprotocol/inspector uv --directory . run src/bluesky_mcp/server.py

# Kill any running MCP server processes
pkill -f bluesky
```

## Authentication Setup

The server requires two environment variables:

- `BLUESKY_IDENTIFIER`: Your Bluesky handle (e.g., `username.bsky.social`)
- `BLUESKY_APP_PASSWORD`: App Password generated from Bluesky account settings (NOT your login password)

Authentication is lazy—the Bluesky client authenticates on the first tool invocation through `BlueSkyClient.ensure_client()`. This means the credentials are only used when a tool is actually called, not when the server starts.

## Architecture

### Core Components

The MCP server (`src/bluesky_mcp/server.py`) follows a two-decorator pattern:

1. **Tool Registration** (`@server.list_tools()`): Returns a list of `types.Tool` objects that define:
   - Tool name and description
   - JSON Schema for input parameters
   - All tools are listed here before implementation

2. **Tool Execution** (`@server.call_tool()`): Single handler that dispatches to implementations based on tool name. This pattern keeps the dispatcher logic centralized.

### BlueSkyClient Class

A simple singleton pattern wrapper around the `atproto.Client`:
- `ensure_client()`: Lazily initializes and authenticates the client on first use
- Stores the authenticated client instance for reuse across tool calls
- Handles authentication errors gracefully

### Tool Implementation Pattern

All tool implementations follow this pattern:

1. Extract parameters from the `arguments` dict using `.get()` with appropriate defaults
2. Make XRPC API calls using direct client methods: `bluesky.client.app.bsky.namespace.method()`
   - **Important**: Use only direct XRPC calls. The codebase does NOT use wrapper methods like `get_foo()`.
3. Wrap blocking calls with `asyncio.to_thread()` since the atproto library is synchronous
4. Return results as `types.TextContent` with JSON-serialized response data

### Write Operations

Create and delete operations use `atproto.repo` methods directly:
- `bluesky.client.com.atproto.repo.create_record()` for creating records
- `bluesky.client.com.atproto.repo.delete_record()` for deleting records

These return success dictionaries (not Pydantic models), so return them directly without calling `.model_dump()`.

## List Management

Bluesky list operations work with specific URI formats:

- **List URIs**: `at://did:plc:xxx/app.bsky.graph.list/rkey`
- **List Item URIs**: `at://did:plc:xxx/app.bsky.graph.listitem/rkey`
- **Purpose values**:
  - `"app.bsky.graph.defs#curatelist"` for feeds
  - `"app.bsky.graph.defs#modlist"` for moderation lists (muting/blocking)

When parsing URIs for operations (especially delete), split by `/`:
```python
parts = uri.split('/')
# parts[0] = "at:"
# parts[2] = repo (DID)
# parts[3] = collection
# parts[4] = rkey
```

## Available Tools

The server currently exposes 15 tools grouped by category:

**Profile & User Data:**
- `bluesky_get_profile`: Get authenticated user's profile
- `bluesky_search_profiles`: Search for Bluesky profiles by query

**Posts & Feed:**
- `bluesky_get_posts`: Get recent posts from authenticated user
- `bluesky_search_posts`: Search for posts by query
- `bluesky_get_personal_feed`: Get personalized timeline
- `bluesky_get_liked_posts`: Get posts liked by authenticated user

**Graph (Follows & Followers):**
- `bluesky_get_follows`: Get accounts the authenticated user follows
- `bluesky_get_followers`: Get accounts following the authenticated user

**List Management:**
- `bluesky_get_lists`: Get lists created by a user (defaults to authenticated user)
- `bluesky_get_list`: Get a specific list with its members
- `bluesky_create_list`: Create a new list (curatelist or modlist)
- `bluesky_delete_list`: Delete a list owned by authenticated user
- `bluesky_add_user_to_list`: Add a user to a list
- `bluesky_remove_user_from_list`: Remove a user from a list

All tools support pagination via `limit` and `cursor` parameters where applicable.

## Key Implementation Details

### Pagination

Many endpoints support pagination through:
- `limit`: Maximum results to return (typically 1-100, defaults vary by tool)
- `cursor`: Pagination token returned from previous requests

Pass both parameters to `asyncio.to_thread()` in the API call dict.

### Error Handling

All tool execution is wrapped in try/except:
- Catches exceptions and returns error messages as `TextContent`
- Returns user-friendly error messages, not stack traces
- Validation of required parameters happens before API calls

### Timestamp Handling

For create operations (lists, list items), use ISO format timestamps with Z suffix:
```python
datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
```

This format is required by the atproto API.

## Dependencies

Core dependencies (from `pyproject.toml`):
- `mcp>=0.1.0`: Model Context Protocol SDK
- `atproto>=0.0.47`: Bluesky/ATProto API client
- `pydantic>=2.0.0`: Data validation (used by atproto)
- Python 3.12+

## Project Structure

```
src/bluesky_mcp/
├── __init__.py          # Exports main() entry point
└── server.py            # Main MCP server implementation with all tools
```

No additional modules or subdirectories—all tool implementations are in `server.py`.
