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

<!-- Paste the agent's response to "What went wrong?" showing chained log + trace investigation -->

## Task 4B — Proactive health check

<!-- Screenshot or transcript of the proactive health report that appears in the Flutter chat -->

## Task 4C — Bug fix and recovery

<!-- 1. Root cause identified
     2. Code fix (diff or description)
     3. Post-fix response to "What went wrong?" showing the real underlying failure
     4. Healthy follow-up report or transcript after recovery -->
