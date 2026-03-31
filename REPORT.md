# Lab 8 — Report

Paste your checkpoint evidence below. Add screenshots as image files in the repo and reference them with `![description](path)`.

## Task 1A — Bare agent

**Question 1: "What is the agentic loop?"**

The agentic loop is the fundamental cycle that autonomous AI agents follow to accomplish tasks. It's the core reasoning and action pattern that enables agents to work independently toward goals.

The Basic Loop: **Perceive → Reason → Act → Observe → (repeat)**

1. **Perceive**: The agent gathers information about its environment (reads user input, observes tool outputs, checks current state/context)

2. **Reason**: The agent processes information and plans (analyzes the current situation, determines what needs to be done, decides on the next action(s), may break complex goals into sub-tasks)

3. **Act**: The agent executes its decision (calls tools/functions, makes API requests, modifies files or systems, sends messages)

4. **Observe**: The agent evaluates the results (checks if the action succeeded, reads outputs/errors, determines if the goal is achieved, identifies what to do next)

This pattern is what distinguishes agentic systems from simple chatbots — the ability to take initiative, use tools, and iterate toward outcomes.

**Question 2: "What labs are available in our LMS?"**

Before MCP tools were added, the agent could only inspect local repo files. It responded by exploring the workspace directory structure and listing the labs from the task files:

- Required Labs (4 tasks): Task 1-4 covering agent setup, web client deployment, observability, and proactive diagnostics
- Optional Labs (1 task): Telegram Bot Client

The agent noted it was Lab 8 — "The Agent is the Interface" but could not access live LMS backend data yet.

## Task 1B — Agent with LMS tools

**Question 1: "What labs are available?"**

After adding the MCP server, the agent returned real backend data:

Here are the available labs:
1. Lab 01 – Products, Architecture & Roles
2. Lab 02 — Run, Fix, and Deploy a Backend Service
3. Lab 03 — Backend API: Explore, Debug, Implement, Deploy
4. Lab 04 — Testing, Front-end, and AI Agents
5. Lab 05 — Data Pipeline and Analytics Dashboard
6. Lab 06 — Build Your Own Agent
7. Lab 07 — Build a Client with an AI Coding Agent
8. lab-08

**Question 2: "Is the LMS backend healthy?"**

Yes, the LMS backend is healthy. It currently has 56 items in the system.

**Question 3: "Which lab has the lowest pass rate?"**

The agent chained multiple tool calls and returned:

| Lab    | Completion Rate | Passed | Total |
|--------|-----------------|--------|-------|
| lab-01 | 100.0%          | 258    | 258   |
| lab-02 | 89.1%           | 131    | 147   |
| lab-03 | 89.1%           | 156    | 175   |
| lab-04 | 96.7%           | 238    | 246   |
| lab-05 | 98.4%           | 246    | 250   |
| lab-06 | 98.4%           | 241    | 245   |
| lab-07 | 99.6%           | 236    | 237   |
| lab-08 | 0.0%            | 0      | 0     |

Lab-02 and Lab-03 are tied for the lowest pass rate at 89.1% among labs that have submissions.

## Task 1C — Skill prompt

**Question: "Show me the scores" (without specifying a lab)**

After adding the LMS skill prompt, the agent responded:

"I'll check what labs are available in the LMS first."

[Called lms_labs tool]

"There are 8 labs available. Which lab would you like to see the scores for?"

1. Lab 01 – Products, Architecture & Roles
2. Lab 02 — Run, Fix, and Deploy a Backend Service
3. Lab 03 — Backend API: Explore, Debug, Implement, Deploy
4. Lab 04 — Testing, Front-end, and AI Agents
5. Lab 05 — Data Pipeline and Analytics Dashboard
6. Lab 06 — Build Your Own Agent
7. Lab 07 — Build a Client with an AI Coding Agent
8. lab-08

The skill prompt successfully taught the agent to:
1. Call `lms_labs` first when a lab parameter is needed but not provided
2. Ask the user to choose which lab they want to see scores for
3. Present the list with proper lab titles as labels

## Task 2A — Deployed agent

<!-- Paste a short nanobot startup log excerpt showing the gateway started inside Docker -->

## Task 2B — Web client

<!-- Screenshot of a conversation with the agent in the Flutter web app -->

## Task 3A — Structured logging

<!-- Paste happy-path and error-path log excerpts, VictoriaLogs query screenshot -->

## Task 3B — Traces

<!-- Screenshots: healthy trace span hierarchy, error trace -->

## Task 3C — Observability MCP tools

<!-- Paste agent responses to "any errors in the last hour?" under normal and failure conditions -->

## Task 4A — Multi-step investigation

**Observability Skill Enhancement:**

The observability skill was enhanced to guide the agent through a one-shot investigation when the user asks "What went wrong?" or "Check system health":

1. Call `logs_error_count` with `time_range: "10m"` to find recent errors
2. Call `logs_search` scoped to the LMS backend
3. Extract a `trace_id` from error logs
4. Call `traces_get` with that trace ID to inspect the full request path
5. Summarize findings concisely, mentioning both log evidence and trace evidence

**Key insight for the planted bug:**
- Logs and traces show a real PostgreSQL/SQLAlchemy error (connection refused, database down)
- The HTTP response incorrectly reports `404 Items not found`
- The real issue is the database being unavailable, not items missing

**Test scenario:** PostgreSQL was stopped to trigger the failure, then a request to list labs/items was made through the Flutter app.

---

## Task 4B — Proactive health check

**Scheduled Health Check Configuration:**

The agent uses the built-in `cron` tool to create recurring health checks. The health check:
- Runs every 2 minutes
- Checks for LMS/backend errors in the last 2 minutes using `logs_error_count`
- Inspects traces if errors are found
- Posts a short summary to the chat
- Reports "system looks healthy" if no recent errors are found

**Usage:**
- Create: "Create a health check for this chat that runs every 2 minutes using your cron tool..."
- List: "List scheduled jobs."
- Remove: "Remove the health check job."

---

## Task 4C — Bug fix and recovery

### 1. Root Cause

**Location:** `backend/src/lms_backend/routers/items.py`, function `get_items()`

**The planted bug:** A broad `except Exception` block caught all exceptions (including database connection errors) and re-raised them as `HTTPException` with status code `404 NOT_FOUND` and detail "Items not found".

```python
# BEFORE (buggy code):
@router.get("/", response_model=list[ItemRecord])
async def get_items(session: AsyncSession = Depends(get_session)):
    try:
        return await read_items(session)
    except Exception as exc:
        logger.warning("items_list_failed_as_not_found", ...)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Items not found",
        ) from exc
```

This masked the real database failure (PostgreSQL connection refused) and reported it as a 404, misleading both users and observability tools.

### 2. Fix Applied

**File:** `backend/src/lms_backend/routers/items.py`

**Changes:**
1. Import `SQLAlchemyError` to catch database-specific exceptions
2. Add specific exception handler for `SQLAlchemyError` that returns `503 SERVICE_UNAVAILABLE`
3. Keep generic `Exception` handler for unexpected errors, returning `500 INTERNAL_SERVER_ERROR`
4. Both handlers now log the actual error message and type for proper observability

```python
# AFTER (fixed code):
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

@router.get("/", response_model=list[ItemRecord])
async def get_items(session: AsyncSession = Depends(get_session)):
    """Get all items."""
    try:
        return await read_items(session)
    except SQLAlchemyError as exc:
        logger.error(
            "items_list_database_error",
            extra={
                "event": "items_list_database_error",
                "error": str(exc),
                "error_type": type(exc).__name__,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database unavailable: {str(exc)}",
        ) from exc
    except Exception as exc:
        logger.error(
            "items_list_unexpected_error",
            extra={
                "event": "items_list_unexpected_error",
                "error": str(exc),
                "error_type": type(exc).__name__,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(exc)}",
        ) from exc
```

### 3. Post-Fix Verification

After rebuilding and redeploying the backend:
- With PostgreSQL stopped, requests to `/items/` now return `503 SERVICE_UNAVAILABLE` with the actual database error message
- Logs show `items_list_database_error` with the real exception details
- Traces correctly show the database connection failure
- The agent's "What went wrong?" investigation now reports the true root cause

### 4. Recovery

PostgreSQL was restarted:
```bash
docker compose --env-file .env.docker.secret start postgres
```

After recovery:
- Backend health check returns healthy
- Requests to `/items/` succeed and return the item list
- Scheduled health checks report "system looks healthy"
- No recent backend errors detected in the last 2-minute window
