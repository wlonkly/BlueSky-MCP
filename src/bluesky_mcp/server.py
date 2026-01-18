from typing import Any
import asyncio
import json
import os
from atproto import Client, models
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
from datetime import datetime, timezone

API_KEY = os.getenv('BLUESKY_APP_PASSWORD')
IDENTIFIER = os.getenv('BLUESKY_IDENTIFIER')

# if not API_KEY or not IDENTIFIER:
#     raise ValueError("BLUESKY_APP_PASSWORD and BLUESKY_IDENTIFIER must be set")

server = Server("bluesky_social")

class BlueSkyClient:
    def __init__(self):
        self.client = None

    async def ensure_client(self):
        """Ensure we have an authenticated client"""
        if not self.client:
            self.client = Client()
            profile = await asyncio.to_thread(
                self.client.login, 
                IDENTIFIER, 
                API_KEY
            )
            if not profile:
                raise ValueError("Failed to authenticate with BlueSky")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools for BlueSky API integration."""
    return [
        types.Tool(
            name="bluesky_get_profile",
            description="Get a user's profile information",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="bluesky_get_posts",
            description="Get recent posts from a user",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of posts to return (default 50, max 100)",
                        "default": 50,
                    },
                    "cursor": {
                        "type": "string",
                        "description": "Pagination cursor for next page of results",
                    },
                },
            },
        ),
        types.Tool(
            name="bluesky_search_posts",
            description="Search for posts on Bluesky",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of posts to return (default 25, max 100)",
                        "default": 25,
                    },
                    "cursor": {
                        "type": "string",
                        "description": "Pagination cursor for next page of results",
                    },
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="bluesky_get_follows",
            description="Get a list of accounts the user follows",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of follows to return (default 50, max 100)",
                        "default": 50,
                    },
                    "cursor": {
                        "type": "string",
                        "description": "Pagination cursor for next page of results",
                    },
                },
            },
        ),
        types.Tool(
            name="bluesky_get_followers",
            description="Get a list of accounts following the user",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of followers to return (default 50, max 100)",
                        "default": 50,
                    },
                    "cursor": {
                        "type": "string",
                        "description": "Pagination cursor for next page of results",
                    },
                },
            },
        ),
        types.Tool(
            name="bluesky_get_liked_posts",
            description="Get a list of posts liked by the user",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of liked posts to return (default 50, max 100)",
                        "default": 50,
                    },
                    "cursor": {
                        "type": "string",
                        "description": "Pagination cursor for next page of results",
                    },
                },
            },
        ),
        types.Tool(
            name="bluesky_get_personal_feed",
            description="Get your personalized Bluesky feed",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of feed items to return (default 50, max 100)",
                        "default": 50,
                    },
                    "cursor": {
                        "type": "string",
                        "description": "Pagination cursor for next page of results",
                    },
                },
            },
        ),
        types.Tool(
            name="bluesky_search_profiles",
            description="Search for Bluesky profiles",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query string",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default 25, max 100)",
                        "default": 25,
                    },
                    "cursor": {
                        "type": "string",
                        "description": "Pagination cursor for next page of results",
                    },
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="bluesky_get_lists",
            description="Get lists created by a specified user (defaults to current user)",
            inputSchema={
                "type": "object",
                "properties": {
                    "actor": {
                        "type": "string",
                        "description": "User handle or DID (defaults to current user)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of lists to return (default 50, max 100)",
                        "default": 50,
                    },
                    "cursor": {
                        "type": "string",
                        "description": "Pagination cursor for next page of results",
                    },
                },
            },
        ),
        types.Tool(
            name="bluesky_get_list",
            description="Get a specific list with its members",
            inputSchema={
                "type": "object",
                "properties": {
                    "list": {
                        "type": "string",
                        "description": "List URI (at://did:collection/rkey)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of members to return (default 50, max 100)",
                        "default": 50,
                    },
                    "cursor": {
                        "type": "string",
                        "description": "Pagination cursor for next page of results",
                    },
                },
                "required": ["list"],
            },
        ),
        types.Tool(
            name="bluesky_create_list",
            description="Create a new list for the current user",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The list's title",
                    },
                    "description": {
                        "type": "string",
                        "description": "Explanatory text about the list",
                    },
                    "purpose": {
                        "type": "string",
                        "description": "List purpose: 'curatelist' for feeds, 'modlist' for muting/blocking",
                        "enum": ["curatelist", "modlist"],
                        "default": "curatelist",
                    },
                },
                "required": ["name", "description"],
            },
        ),
        types.Tool(
            name="bluesky_delete_list",
            description="Delete a list owned by the current user",
            inputSchema={
                "type": "object",
                "properties": {
                    "list_uri": {
                        "type": "string",
                        "description": "List URI to delete (at://did:collection/rkey)",
                    },
                },
                "required": ["list_uri"],
            },
        ),
        types.Tool(
            name="bluesky_add_user_to_list",
            description="Add a user to a list owned by the current user",
            inputSchema={
                "type": "object",
                "properties": {
                    "list_uri": {
                        "type": "string",
                        "description": "List URI (at://did:collection/rkey)",
                    },
                    "did": {
                        "type": "string",
                        "description": "User's DID to add to the list",
                    },
                },
                "required": ["list_uri", "did"],
            },
        ),
        types.Tool(
            name="bluesky_remove_user_from_list",
            description="Remove a user from a list owned by the current user",
            inputSchema={
                "type": "object",
                "properties": {
                    "list_uri": {
                        "type": "string",
                        "description": "List URI (at://did:collection/rkey)",
                    },
                    "did": {
                        "type": "string",
                        "description": "User's DID to remove from the list",
                    },
                },
                "required": ["list_uri", "did"],
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution requests."""
    if not arguments:
        arguments = {}
    
    bluesky = BlueSkyClient()
    await bluesky.ensure_client()
    
    try:
        if name == "bluesky_get_profile":
            response = await asyncio.to_thread(
                bluesky.client.app.bsky.actor.get_profile,
                {'actor': IDENTIFIER}
            )

        elif name == "bluesky_get_posts":
            limit = arguments.get("limit", 50)
            cursor = arguments.get("cursor")
            response = await asyncio.to_thread(
                bluesky.client.app.bsky.feed.get_author_feed,
                {'actor': IDENTIFIER, 'limit': limit, 'cursor': cursor}
            )

        elif name == "bluesky_search_posts":
            query = arguments.get("query")
            if not query:
                return [types.TextContent(type="text", text="Missing required argument: query")]
            limit = arguments.get("limit", 25)
            cursor = arguments.get("cursor")
            response = await asyncio.to_thread(
                bluesky.client.app.bsky.feed.search_posts,
                {'q': query, 'limit': limit, 'cursor': cursor}
            )

        elif name == "bluesky_get_follows":
            limit = arguments.get("limit", 50)
            cursor = arguments.get("cursor")
            response = await asyncio.to_thread(
                bluesky.client.app.bsky.graph.get_follows,
                {'actor': IDENTIFIER, 'limit': limit, 'cursor': cursor}
            )

        elif name == "bluesky_get_followers":
            limit = arguments.get("limit", 50)
            cursor = arguments.get("cursor")
            response = await asyncio.to_thread(
                bluesky.client.app.bsky.graph.get_followers,
                {'actor': IDENTIFIER, 'limit': limit, 'cursor': cursor}
            )

        elif name == "bluesky_get_liked_posts":
            limit = arguments.get("limit", 50)
            cursor = arguments.get("cursor")
            response = await asyncio.to_thread(
                bluesky.client.app.bsky.feed.get_likes,
                {'uri': IDENTIFIER, 'limit': limit, 'cursor': cursor}
            )

        elif name == "bluesky_get_personal_feed":
            limit = arguments.get("limit", 50)
            cursor = arguments.get("cursor")
            response = await asyncio.to_thread(
                bluesky.client.app.bsky.feed.get_timeline,
                {'limit': limit, 'cursor': cursor}
            )

        elif name == "bluesky_search_profiles":
            query = arguments.get("query")
            if not query:
                return [types.TextContent(type="text", text="Missing required argument: query")]
            limit = arguments.get("limit", 25)
            cursor = arguments.get("cursor")
            response = await asyncio.to_thread(
                bluesky.client.app.bsky.actor.search_actors,
                {'term': query, 'limit': limit, 'cursor': cursor}
            )

        elif name == "bluesky_get_lists":
            actor = arguments.get("actor", bluesky.client.me.did)
            limit = arguments.get("limit", 50)
            cursor = arguments.get("cursor")
            response = await asyncio.to_thread(
                bluesky.client.app.bsky.graph.get_lists,
                {'actor': actor, 'limit': limit, 'cursor': cursor}
            )

        elif name == "bluesky_get_list":
            list_uri = arguments.get("list")
            if not list_uri:
                return [types.TextContent(type="text", text="Missing required argument: list")]
            limit = arguments.get("limit", 50)
            cursor = arguments.get("cursor")
            response = await asyncio.to_thread(
                bluesky.client.app.bsky.graph.get_list,
                {'list': list_uri, 'limit': limit, 'cursor': cursor}
            )

        elif name == "bluesky_create_list":
            list_name = arguments.get("name")
            description = arguments.get("description")
            if not list_name or not description:
                return [types.TextContent(type="text", text="Missing required arguments: name, description")]
            purpose = arguments.get("purpose", "curatelist")

            purpose_map = {
                "curatelist": "app.bsky.graph.defs#curatelist",
                "modlist": "app.bsky.graph.defs#modlist",
            }

            response = await asyncio.to_thread(
                bluesky.client.com.atproto.repo.create_record,
                models.ComAtprotoRepoCreateRecord.Data(
                    repo=bluesky.client.me.did,
                    collection=models.ids.AppBskyGraphList,
                    record=models.AppBskyGraphList.Record(
                        name=list_name,
                        description=description,
                        purpose=purpose_map[purpose],
                        created_at=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                    ),
                )
            )
            return [types.TextContent(type="text", text=json.dumps(response, indent=2))]

        elif name == "bluesky_delete_list":
            list_uri = arguments.get("list_uri")
            if not list_uri:
                return [types.TextContent(type="text", text="Missing required argument: list_uri")]

            # Parse the list URI to extract repo, collection, and rkey
            # Format: at://did:plc:xxx/app.bsky.graph.list/yyy
            parts = list_uri.split('/')
            if len(parts) < 5 or parts[0] != 'at:':
                return [types.TextContent(type="text", text="Invalid list_uri format. Expected: at://did/collection/rkey")]

            repo = parts[2]
            collection = parts[3]
            rkey = parts[4]

            await asyncio.to_thread(
                bluesky.client.com.atproto.repo.delete_record,
                models.ComAtprotoRepoDeleteRecord.Data(
                    repo=repo,
                    collection=collection,
                    rkey=rkey,
                )
            )
            return [types.TextContent(type="text", text=json.dumps({"success": True, "message": f"Deleted list: {list_uri}"}, indent=2))]

        elif name == "bluesky_add_user_to_list":
            list_uri = arguments.get("list_uri")
            did = arguments.get("did")
            if not list_uri or not did:
                return [types.TextContent(type="text", text="Missing required arguments: list_uri, did")]

            response = await asyncio.to_thread(
                bluesky.client.com.atproto.repo.create_record,
                models.ComAtprotoRepoCreateRecord.Data(
                    repo=bluesky.client.me.did,
                    collection=models.ids.AppBskyGraphListitem,
                    record=models.AppBskyGraphListitem.Record(
                        subject=did,
                        list=list_uri,
                        created_at=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                    ),
                )
            )
            return [types.TextContent(type="text", text=json.dumps(response, indent=2))]

        elif name == "bluesky_remove_user_from_list":
            list_uri = arguments.get("list_uri")
            did = arguments.get("did")
            if not list_uri or not did:
                return [types.TextContent(type="text", text="Missing required arguments: list_uri, did")]

            # First, find the listitem record for this user in the list
            # Use pagination to handle lists with more than 100 items
            cursor = None
            target_uri = None

            while target_uri is None and cursor is not False:
                params = {'list': list_uri, 'limit': 100}
                if cursor:
                    params['cursor'] = cursor

                response = await asyncio.to_thread(
                    bluesky.client.app.bsky.graph.get_list,
                    params
                )

                if not hasattr(response, 'items') or not response.items:
                    break

                # Find the item with matching subject (DID)
                for item in response.items:
                    if item.subject.did == did:
                        target_uri = item.uri
                        break

                # Continue pagination if not found and there's a cursor
                cursor = getattr(response, 'cursor', False) if not target_uri else False

            if not target_uri:
                return [types.TextContent(type="text", text=f"User {did} not found in list")]

            # Parse the item URI to extract repo, collection, and rkey
            parts = target_uri.split('/')
            if len(parts) < 5 or parts[0] != 'at:':
                return [types.TextContent(type="text", text="Invalid item URI format")]

            repo = parts[2]
            collection = parts[3]
            rkey = parts[4]

            await asyncio.to_thread(
                bluesky.client.com.atproto.repo.delete_record,
                models.ComAtprotoRepoDeleteRecord.Data(
                    repo=repo,
                    collection=collection,
                    rkey=rkey,
                )
            )
            return [types.TextContent(type="text", text=json.dumps({"success": True, "message": f"Removed user {did} from list {list_uri}"}, indent=2))]

        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

        return [types.TextContent(type="text", text=json.dumps(response.model_dump(), indent=2))]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="bluesky_social",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())