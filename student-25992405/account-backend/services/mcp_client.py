import asyncio
import json
import os
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


MCP_SERVER_URL = os.getenv(
    "MCP_SERVER_URL",
    "http://host.docker.internal:7001/mcp"
)

# MCP_ENABLED controls the initial mode. Local development defaults to ON.
# CI/CD can set MCP_ENABLED=false so the Account service starts with MCP off.
_mcp_enabled = os.getenv(
    "MCP_ENABLED",
    "true"
).strip().lower() == "true"


class MCPClientError(Exception):
    """Raised when the Account backend cannot communicate with MCP."""


def is_mcp_enabled() -> bool:
    """Return the current MCP mode for this Account backend process."""
    return _mcp_enabled


def set_mcp_enabled(enabled: bool) -> bool:
    """Enable or disable MCP calls at runtime."""
    global _mcp_enabled
    _mcp_enabled = bool(enabled)
    return _mcp_enabled


def _require_mcp_enabled() -> None:
    if not is_mcp_enabled():
        raise MCPClientError("MCP mode is disabled.")


def _normalise_tool_result(result: Any) -> Any:
    """Convert an MCP CallToolResult into JSON-serialisable data."""

    structured = getattr(result, "structuredContent", None)
    if structured is None:
        structured = getattr(result, "structured_content", None)

    if structured is not None:
        return structured

    content = getattr(result, "content", None) or []
    values = []

    for item in content:
        text = getattr(item, "text", None)

        if text is not None:
            try:
                values.append(json.loads(text))
            except (TypeError, json.JSONDecodeError):
                values.append(text)
            continue

        if hasattr(item, "model_dump"):
            values.append(item.model_dump(mode="json"))
        else:
            values.append(str(item))

    if len(values) == 1:
        return values[0]

    return values


async def _list_tools_async() -> list[dict]:
    async with streamable_http_client(
        MCP_SERVER_URL
    ) as (read_stream, write_stream, *rest):
        async with ClientSession(
            read_stream,
            write_stream
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
    arguments: dict | None = None,
) -> Any:
    async with streamable_http_client(
        MCP_SERVER_URL
    ) as (read_stream, write_stream, *rest):
        async with ClientSession(
            read_stream,
            write_stream
        ) as session:
            await session.initialize()

            result = await session.call_tool(
                tool_name,
                arguments=arguments or {},
            )

            if getattr(result, "isError", False):
                raise MCPClientError(
                    str(_normalise_tool_result(result))
                )

            return _normalise_tool_result(result)


def list_tools() -> list[dict]:
    """Return tools exposed by the shared MCP server."""

    _require_mcp_enabled()

    try:
        return asyncio.run(_list_tools_async())
    except Exception as exc:
        raise MCPClientError(
            f"Unable to list MCP tools: {exc}"
        ) from exc


def call_tool(
    tool_name: str,
    arguments: dict | None = None,
) -> Any:
    """Call one tool on the shared MCP server."""

    _require_mcp_enabled()

    try:
        return asyncio.run(
            _call_tool_async(
                tool_name,
                arguments,
            )
        )
    except MCPClientError:
        raise
    except Exception as exc:
        raise MCPClientError(
            f"Unable to call MCP tool '{tool_name}': {exc}"
        ) from exc


def check_mcp_status() -> dict:
    """Return MCP mode and, when enabled, server connectivity."""

    if not is_mcp_enabled():
        return {
            "enabled": False,
            "available": False,
            "server_url": MCP_SERVER_URL,
            "tool_count": 0,
            "message": "MCP mode is disabled.",
        }

    try:
        tools = list_tools()
        return {
            "enabled": True,
            "available": True,
            "server_url": MCP_SERVER_URL,
            "tool_count": len(tools),
        }
    except MCPClientError as exc:
        return {
            "enabled": True,
            "available": False,
            "server_url": MCP_SERVER_URL,
            "tool_count": 0,
            "error": str(exc),
        }
