import os
import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


MCP_SERVER_URL = os.getenv(
    "MCP_SERVER_URL",
    "http://host.docker.internal:7001/mcp",
)


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


def get_accommodations_mcp():
    return asyncio.run(
        _call_mcp_tool_async(
            "get_accommodations",
            {},
        )
    )


def get_accommodation_by_city_mcp(
    city: str,
):
    return asyncio.run(
        _call_mcp_tool_async(
            "get_accommodation_by_city",
            {
                "city": city,
            },
        )
    )
    

def search_accommodations_mcp(
    city: str,
    max_price: float | None = None,
    guests: int | None = None,
    type: str | None = None,
):
    return asyncio.run(
        _call_mcp_tool_async(
            "search_accommodations",
            {
                "city": city,
                "max_price": max_price,
                "guests": guests,
                "type": type,
            },
        )
    )
    
    
def check_accommodation_availability_mcp(
    accommodation_id: int,
    check_in: str,
    check_out: str,
):
    return asyncio.run(
        _call_mcp_tool_async(
            "check_accommodation_availability",
            {
                "accommodation_id":
                    accommodation_id,
                "check_in": check_in,
                "check_out": check_out,
            },
        )
    )