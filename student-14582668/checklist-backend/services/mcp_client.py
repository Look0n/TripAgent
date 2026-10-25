import asyncio
import json
import os
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


MCP_SERVER_URL = os.getenv(
    "MCP_SERVER_URL",
    "http://localhost:7001/mcp",
)

# Checklist starts OFF; the UI controls this backend process only.
MCP_ENABLED = False

MCP_TIMEOUT_SECONDS = 20


class MCPClientError(RuntimeError):
    """Raised when the shared MCP request fails."""


def is_mcp_enabled() -> bool:
    return MCP_ENABLED and not is_mcp_locked()


def is_mcp_locked() -> bool:
    return os.getenv("MCP_LOCKED", "false").strip().lower() in ("1", "true", "yes", "on")


def set_mcp_enabled(enabled: bool) -> None:
    global MCP_ENABLED
    MCP_ENABLED = enabled


def _normalise_tool_result(result: Any) -> Any:
    structured = getattr(result, "structuredContent", None)

    if structured is None:
        structured = getattr(result, "structured_content", None)

    if structured is not None:
        return structured

    values = []

    for item in getattr(result, "content", None) or []:
        text = getattr(item, "text", None)

        if text is not None:
            try:
                values.append(json.loads(text))
            except (TypeError, json.JSONDecodeError):
                values.append(text)

    if len(values) == 1:
        return values[0]

    return values


async def _list_tools_async() -> list[dict]:
    async with streamable_http_client(
        MCP_SERVER_URL
    ) as (read_stream, write_stream, _):
        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:
            await session.initialize()
            result = await session.list_tools()

            return [
                {
                    "name": tool.name,
                    "description": tool.description or "",
                    "input_schema": tool.inputSchema,
                }
                for tool in result.tools
            ]


async def _call_tool_async(
    tool_name: str,
    arguments: dict,
) -> dict:
    async with streamable_http_client(
        MCP_SERVER_URL
    ) as (read_stream, write_stream, _):
        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:
            await session.initialize()

            result = await session.call_tool(
                tool_name,
                arguments=arguments,
            )

            payload = _normalise_tool_result(result)
            is_error = result.isError

    if is_error:
        raise MCPClientError(
            f"MCP tool execution failed: {payload}"
        )

    if not isinstance(payload, dict):
        raise MCPClientError("MCP returned an invalid result")

    if type(payload.get("success")) is not bool:
        raise MCPClientError(
            "MCP result is missing a valid success field"
        )

    return payload


def list_tools() -> list[dict]:
    if not is_mcp_enabled():
        raise MCPClientError("MCP mode is disabled")

    try:
        return asyncio.run(
            asyncio.wait_for(
                _list_tools_async(),
                timeout=MCP_TIMEOUT_SECONDS,
            )
        )
    except Exception as exc:
        raise MCPClientError(
            "Unable to retrieve tools from the shared MCP server"
        ) from exc


def call_tool(
    tool_name: str,
    arguments: dict,
) -> dict:
    if not is_mcp_enabled():
        raise MCPClientError("MCP mode is disabled")

    try:
        return asyncio.run(
            asyncio.wait_for(
                _call_tool_async(tool_name, arguments),
                timeout=MCP_TIMEOUT_SECONDS,
            )
        )
    except MCPClientError:
        raise
    except Exception as exc:
        raise MCPClientError(
            "Unable to call the shared MCP server"
        ) from exc