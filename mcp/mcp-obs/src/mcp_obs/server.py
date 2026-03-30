"""MCP server for observability tools (VictoriaLogs and VictoriaTraces)."""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from typing import Any

import httpx
from mcp.server import Server
from mcp.types import Tool

# Configuration from environment
VICTORIALOGS_URL = os.environ.get(
    "NANOBOT_VICTORIALOGS_URL", "http://victorialogs:9428"
)
VICTORIATRACES_URL = os.environ.get(
    "NANOBOT_VICTORIATRACES_URL", "http://victoriatraces:10428"
)

server = Server("mcp-obs")


@dataclass(frozen=True, slots=True)
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Any


async def logs_search_handler(arguments: dict[str, Any]) -> dict[str, Any]:
    """Search logs in VictoriaLogs using LogsQL query."""
    query = arguments.get("query", "")
    time_range = arguments.get("time_range", "10m")
    limit = arguments.get("limit", 50)

    # Build LogsQL query with time range
    logsql_query = f"_time:{time_range}"
    if query:
        logsql_query += f" {query}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{VICTORIALOGS_URL}/select/logsql/query"
        params = {"query": logsql_query, "limit": limit}
        response = await client.get(url, params=params)
        response.raise_for_status()

        # Parse response - VictoriaLogs returns newline-delimited JSON
        lines = response.text.strip().split("\n")
        results = []
        for line in lines:
            if line.strip():
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    results.append({"raw": line})

        return {
            "query": logsql_query,
            "count": len(results),
            "logs": results[:limit],
        }


async def logs_error_count_handler(arguments: dict[str, Any]) -> dict[str, Any]:
    """Count errors per service over a time window."""
    time_range = arguments.get("time_range", "1h")
    service = arguments.get("service")

    # Build query for errors
    logsql_query = f"_time:{time_range} severity:ERROR"
    if service:
        logsql_query += f' service.name:"{service}"'

    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{VICTORIALOGS_URL}/select/logsql/query"
        params = {"query": logsql_query, "limit": 1000}
        response = await client.get(url, params=params)
        response.raise_for_status()

        # Count errors by service
        error_counts: dict[str, int] = {}
        lines = response.text.strip().split("\n")
        for line in lines:
            if line.strip():
                try:
                    entry = json.loads(line)
                    service_name = entry.get("service.name", "unknown")
                    error_counts[service_name] = error_counts.get(service_name, 0) + 1
                except json.JSONDecodeError:
                    error_counts["unknown"] = error_counts.get("unknown", 0) + 1

        return {
            "query": logsql_query,
            "time_range": time_range,
            "total_errors": sum(error_counts.values()),
            "by_service": error_counts,
        }


async def traces_list_handler(arguments: dict[str, Any]) -> dict[str, Any]:
    """List recent traces for a service."""
    service = arguments.get("service", "Learning Management Service")
    limit = arguments.get("limit", 10)

    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{VICTORIATRACES_URL}/select/jaeger/api/traces"
        params = {"service": service, "limit": limit}
        response = await client.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        traces_data = data.get("data", [])

        # Extract summary info for each trace
        traces_summary = []
        for trace in traces_data:
            trace_id = trace.get("traceID", "unknown")
            spans = trace.get("spans", [])
            span_count = len(spans)

            # Find the root span (no references or empty refType)
            root_span = None
            for span in spans:
                refs = span.get("references", [])
                is_root = all(
                    ref.get("refType") != "CHILD_OF" for ref in refs
                ) or not refs
                if is_root:
                    root_span = span
                    break

            operation_name = root_span.get("operationName", "unknown") if root_span else "unknown"
            duration = root_span.get("duration", 0) if root_span else 0
            start_time = root_span.get("startTime", 0) if root_span else 0

            # Check for errors in any span
            has_error = any(
                any(
                    tag.get("key") == "error" and tag.get("value")
                    for tag in span.get("tags", [])
                )
                for span in spans
            )

            traces_summary.append(
                {
                    "trace_id": trace_id,
                    "operation": operation_name,
                    "duration_ms": duration / 1000,  # Convert from microseconds
                    "span_count": span_count,
                    "has_error": has_error,
                    "start_time": start_time,
                }
            )

        return {
            "service": service,
            "count": len(traces_summary),
            "traces": traces_summary,
        }


async def traces_get_handler(arguments: dict[str, Any]) -> dict[str, Any]:
    """Fetch a specific trace by ID."""
    trace_id = arguments.get("trace_id")

    if not trace_id:
        return {"error": "trace_id is required"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{VICTORIATRACES_URL}/select/jaeger/api/traces/{trace_id}"
        response = await client.get(url)
        response.raise_for_status()

        data = response.json()
        traces_data = data.get("data", [])

        if not traces_data:
            return {"error": f"Trace {trace_id} not found"}

        trace = traces_data[0]

        # Build span hierarchy summary
        spans = trace.get("spans", [])
        spans_summary = []
        for span in spans:
            span_summary = {
                "span_id": span.get("spanID"),
                "operation_name": span.get("operationName"),
                "duration_ms": span.get("duration", 0) / 1000,
                "start_time": span.get("startTime", 0),
                "has_error": any(
                    tag.get("key") == "error" and tag.get("value")
                    for tag in span.get("tags", [])
                ),
                "tags": {
                    tag.get("key"): tag.get("value")
                    for tag in span.get("tags", [])
                    if tag.get("key") in ("http.status_code", "http.method", "http.url", "db.system", "error")
                },
            }
            spans_summary.append(span_summary)

        # Sort by start time
        spans_summary.sort(key=lambda s: s["start_time"])

        return {
            "trace_id": trace_id,
            "span_count": len(spans_summary),
            "spans": spans_summary,
        }


# Tool specifications
TOOL_SPECS = (
    ToolSpec(
        name="logs_search",
        description="Search logs in VictoriaLogs using LogsQL query. Use this to find specific log entries by keyword, service, or severity.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "LogsQL query filter (e.g., 'service.name:\"Learning Management Service\" severity:ERROR'). Leave empty for all logs.",
                    "default": "",
                },
                "time_range": {
                    "type": "string",
                    "description": "Time range for search (e.g., '10m', '1h', '1d'). Default is 10 minutes.",
                    "default": "10m",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of log entries to return. Default is 50.",
                    "default": 50,
                },
            },
            "required": [],
        },
        handler=logs_search_handler,
    ),
    ToolSpec(
        name="logs_error_count",
        description="Count errors per service over a time window. Use this first to see if there are any recent errors.",
        input_schema={
            "type": "object",
            "properties": {
                "time_range": {
                    "type": "string",
                    "description": "Time window for counting errors (e.g., '10m', '1h'). Default is 1 hour.",
                    "default": "1h",
                },
                "service": {
                    "type": "string",
                    "description": "Filter by service name. Leave empty to count errors across all services.",
                    "default": "",
                },
            },
            "required": [],
        },
        handler=logs_error_count_handler,
    ),
    ToolSpec(
        name="traces_list",
        description="List recent traces for a service. Shows trace ID, operation, duration, and error status.",
        input_schema={
            "type": "object",
            "properties": {
                "service": {
                    "type": "string",
                    "description": "Service name to list traces for. Default is 'Learning Management Service'.",
                    "default": "Learning Management Service",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of traces to return. Default is 10.",
                    "default": 10,
                },
            },
            "required": [],
        },
        handler=traces_list_handler,
    ),
    ToolSpec(
        name="traces_get",
        description="Fetch a specific trace by ID. Use this to inspect the full span hierarchy of a request.",
        input_schema={
            "type": "object",
            "properties": {
                "trace_id": {
                    "type": "string",
                    "description": "The trace ID to fetch (e.g., 'c8c8e754d79a4280b7689778c20ac4c8').",
                },
            },
            "required": ["trace_id"],
        },
        handler=traces_get_handler,
    ),
)


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available observability tools."""
    return [
        Tool(
            name=spec.name,
            description=spec.description,
            inputSchema=spec.input_schema,
        )
        for spec in TOOL_SPECS
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[dict[str, Any]]:
    """Call an observability tool by name."""
    tool_spec = next((t for t in TOOL_SPECS if t.name == name), None)
    if not tool_spec:
        raise ValueError(f"Unknown tool: {name}")

    result = await tool_spec.handler(arguments)
    return [{"type": "text", "text": json.dumps(result, indent=2)}]


def main() -> None:
    """Run the MCP observability server."""
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
