import os
import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


MCP_SERVER_URL = os.getenv(
    "MCP_SERVER_URL",
    "http://host.docker.internal:7001/mcp",
)


async def _search_accommodations_async(
    city: str,
    max_price: float | None = None,
    guests: int | None = None,
):
    async with streamable_http_client(
        MCP_SERVER_URL
    ) as (read_stream, write_stream, _):

        async with ClientSession(
            read_stream,
            write_stream
        ) as session:

            await session.initialize()

            result = await session.call_tool(
                "search_accommodations",
                arguments={
                    "city": city,
                    "max_price": max_price,
                    "guests": guests,
                },
            )

            if result.isError:
                messages = []

                for item in result.content:
                    if hasattr(item, "text"):
                        messages.append(item.text)

                raise RuntimeError(
                    "MCP tool call failed: "
                    + " | ".join(messages)
                )

            # MCP 1.x usually returns tool output in content
            content = []

            for item in result.content:
                if hasattr(item, "text"):
                    content.append(item.text)

            return {
                "content": content
            }


def search_accommodations_mcp(
    city: str,
    max_price: float | None = None,
    guests: int | None = None,
):
    return asyncio.run(
        _search_accommodations_async(
            city=city,
            max_price=max_price,
            guests=guests,
        )
    )