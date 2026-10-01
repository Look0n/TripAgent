# MCP client for the Attractions backend.
# The MCP server runs on the host machine (not in Docker),
# so we reach it via host.docker.internal from inside the container.

import os
import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


MCP_SERVER_URL = os.getenv(
    "MCP_SERVER_URL",
    "http://host.docker.internal:7001/mcp",
)


# Quick check that the MCP server is reachable.
def check_mcp_health():
    return asyncio.run(
        _check_mcp_health_async()
    )


async def _check_mcp_health_async():

    async with streamable_http_client(
        MCP_SERVER_URL
    ) as (
        read_stream,
        write_stream,
        _
    ):

        async with ClientSession(
            read_stream,
            write_stream
        ) as session:

            await session.initialize()

            return {
                "status": "connected"
            }


# Generic call: open a session, call one tool, close the session.
def call_mcp_tool(
    tool_name: str,
    arguments: dict | None = None,
):
    return asyncio.run(
        _call_mcp_tool_async(
            tool_name,
            arguments or {},
        )
    )


async def _call_mcp_tool_async(
    tool_name: str,
    arguments: dict,
):

    error_message = None
    content = []

    async with streamable_http_client(
        MCP_SERVER_URL
    ) as (
        read_stream,
        write_stream,
        _
    ):

        async with ClientSession(
            read_stream,
            write_stream
        ) as session:

            await session.initialize()

            result = await session.call_tool(
                tool_name,
                arguments=arguments,
            )

            if result.isError:

                messages = []

                for item in result.content:
                    if hasattr(item, "text"):
                        messages.append(item.text)

                error_message = (
                    "MCP tool call failed: "
                    + " | ".join(messages)
                )

            else:
                for item in result.content:
                    if hasattr(item, "text"):
                        content.append(
                            item.text
                        )

        # Raise only AFTER MCP sessions are closed.
        if error_message:
            raise RuntimeError(
                error_message
            )

        return {
            "content": content
        }


# Shortcuts below: one wrapper per registered MCP tool.
# Each just calls call_mcp_tool with the right name + arguments.

def get_attractions_mcp():
    return asyncio.run(
        _call_mcp_tool_async(
            "get_attractions",
            {},
        )
    )


def get_attractions_by_city_mcp(
    city: str,
):
    return asyncio.run(
        _call_mcp_tool_async(
            "get_attractions_by_city",
            {
                "city": city,
            },
        )
    )


def search_attractions_mcp(
    city: str | None = None,
    category: str | None = None,
    max_price: float | None = None,
):
    return asyncio.run(
        _call_mcp_tool_async(
            "search_attractions",
            {
                "city": city,
                "category": category,
                "max_price": max_price,
            },
        )
    )


def get_attraction_details_mcp(
    attraction_id: int,
):
    return asyncio.run(
        _call_mcp_tool_async(
            "get_attraction_details",
            {
                "attraction_id": attraction_id,
            },
        )
    )


def get_top_rated_attractions_mcp(
    city: str | None = None,
    limit: int = 5,
):
    return asyncio.run(
        _call_mcp_tool_async(
            "get_top_rated_attractions",
            {
                "city": city,
                "limit": limit,
            },
        )
    )
