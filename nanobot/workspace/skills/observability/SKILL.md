---
name: observability
description: Use observability MCP tools to investigate logs and traces
always: true
---

# Observability Skill

Use observability MCP tools to investigate system health, errors, and failures.

## Available Tools

The following `logs_*` and `traces_*` tools are available via the MCP server:

- **logs_search**: Search logs in VictoriaLogs using LogsQL query
- **logs_error_count**: Count errors per service over a time window
- **traces_list**: List recent traces for a service
- **traces_get**: Fetch a specific trace by ID

## Strategy

### When the user asks "What went wrong?" or "Check system health"

Run a one-shot investigation that chains log and trace tools:

1. **Call `logs_error_count`** with `time_range: "10m"` to find recent errors
2. **Call `logs_search`** scoped to the most likely failing service (e.g., `service.name:"Learning Management Service" severity:ERROR _time:10m`)
3. **Extract a `trace_id`** from the error logs if one is present
4. **Call `traces_get`** with that trace ID to inspect the full request path
5. **Summarize findings** in one coherent explanation that mentions:
   - The error count and affected service
   - What the logs show (error message, operation)
   - What the trace shows (span hierarchy, where it failed)
   - The root cause (e.g., "PostgreSQL connection refused", "SQLAlchemy timeout")

**Important**: When investigating the LMS backend failure, pay attention to this discrepancy:
- Logs and traces will show a real PostgreSQL/SQLAlchemy error (connection refused, database down)
- The HTTP response may incorrectly report `404 Items not found`
- The real issue is the database being unavailable, not items missing
- Always report the **root cause from logs/traces**, not the misleading HTTP status

### When the user asks about errors or system health (general)

1. **Start with `logs_error_count`** to quickly see if there are recent errors and which services are affected
2. If errors are found, use **`logs_search`** to inspect the relevant service and extract details
3. If you find a `trace_id` in the logs, use **`traces_get`** to inspect the full request path
4. Summarize findings concisely — don't dump raw JSON

### When the user asks about errors or system health (general)

1. **Start with `logs_error_count`** to quickly see if there are recent errors and which services are affected
2. If errors are found, use **`logs_search`** to inspect the relevant service and extract details
3. If you find a `trace_id` in the logs, use **`traces_get`** to inspect the full request path
4. Summarize findings concisely — don't dump raw JSON

### When the user asks about a specific service

1. Use **`logs_search`** with a query like `service.name:"<service-name>"` to find recent logs
2. Use **`traces_list`** with the service name to see recent traces
3. If any trace has `has_error: true`, fetch it with **`traces_get`**

### When investigating a failure

1. Ask the user for the time range or use a recent window (e.g., `10m`)
2. Call **`logs_error_count`** with `time_range: "10m"` and `service: "Learning Management Service"`
3. If errors exist, call **`logs_search`** with a query like:
   ```
   service.name:"Learning Management Service" severity:ERROR
   ```
4. Extract the `trace_id` from error logs
5. Call **`traces_get`** with the trace ID to see the full span hierarchy
6. Identify where the error occurred (DB connection, HTTP request, etc.)

### Query syntax tips

VictoriaLogs uses LogsQL. Useful patterns:

- `_time:10m` — last 10 minutes
- `severity:ERROR` — only error-level logs
- `service.name:"Learning Management Service"` — filter by service
- Combine: `_time:10m service.name:"Learning Management Service" severity:ERROR`

## Response formatting

- Keep responses concise and actionable
- Summarize error counts: "Found 3 errors in the LMS backend in the last 10 minutes"
- When showing trace details, highlight the failing span
- Include the `trace_id` for reference
- Don't dump raw JSON — explain what happened in plain language

## Examples

**User**: "Any errors in the last hour?"
**You**: Call `logs_error_count` with `time_range: "1h"`, report findings

**User**: "Any LMS backend errors in the last 10 minutes?"
**You**: 
1. Call `logs_error_count` with `time_range: "10m"` and `service: "Learning Management Service"`
2. If errors found, call `logs_search` to get details
3. Extract `trace_id` and call `traces_get` if needed
4. Summarize: "Yes, found 2 errors. The database connection was closed during a query..."

**User**: "Show me the trace for request abc123"
**You**: Call `traces_get` with `trace_id: "abc123"` and explain the span hierarchy

**User**: "Is the system healthy?"
**You**: 
1. Call `logs_error_count` with `time_range: "1h"`
2. If no errors: "No errors detected in the last hour"
3. If errors: Report the count and affected services
