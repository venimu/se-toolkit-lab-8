---
name: lms
description: Use LMS MCP tools for live course data
always: true
---

# LMS Skill

Use LMS MCP tools to provide live data about the learning management system.

## Available Tools

The following `lms_*` tools are available via the MCP server:

- **lms_health**: Check if the LMS backend is healthy and report the item count
- **lms_labs**: List all labs available in the LMS
- **lms_learners**: List all learners registered in the LMS
- **lms_pass_rates**: Get pass rates (avg score and attempt count per task) for a lab
- **lms_timeline**: Get submission timeline (date + submission count) for a lab
- **lms_groups**: Get group performance (avg score + student count per group) for a lab
- **lms_top_learners**: Get top learners by average score for a lab
- **lms_completion_rate**: Get completion rate (passed / total) for a lab
- **lms_sync_pipeline**: Trigger the LMS sync pipeline

## Strategy

### When to use LMS tools

- If the user asks about **scores**, **pass rates**, **completion**, **groups**, **timeline**, or **top learners** without naming a lab:
  1. First call `lms_labs` to get the list of available labs
  2. If multiple labs are available, ask the user to choose one using the shared `structured-ui` skill
  3. Use each lab's `title` field as the default user-facing label unless the tool output gives a better identifier

- If the user asks which lab has the **lowest/highest** pass rate or completion rate:
  1. Call `lms_labs` to get all labs
  2. Call `lms_completion_rate` or `lms_pass_rates` for each lab
  3. Compare and report the result

- If the user asks about **backend health**:
  - Call `lms_health` and report the result

- If the user asks **what labs are available**:
  - Call `lms_labs` and present the list with titles

- If the user asks about **learners**:
  - Call `lms_learners` for the full list
  - Call `lms_top_learners` with a lab parameter for top performers

### Handling missing lab parameter

When a lab parameter is needed but not provided:
1. Call `lms_labs` first
2. Use the shared `structured-ui` skill to present the choice with:
   - `type: "choice"` for multiple options
   - Each option's label should be the lab's `title` field
   - Each option's value should be the lab's `id` field
3. Wait for user selection before proceeding

### Response formatting

- Format percentages with one decimal place (e.g., "89.1%")
- Format counts as plain numbers
- When presenting tabular data, use markdown tables
- Keep responses concise but informative
- Include relevant context (e.g., "among labs with submissions")

### When the user asks "what can you do?"

Explain current capabilities clearly:
- "I can access live LMS data including lab information, pass rates, completion rates, group performance, top learners, and submission timelines."
- "I can check if the LMS backend is healthy."
- "I can trigger the LMS sync pipeline to update data."
- Mention limits: "I can only access data through the LMS API - I cannot modify grades or enrollments."

## Examples

**User**: "Show me the scores"
**You**: Call `lms_labs`, then use structured-ui to ask which lab

**User**: "Which lab has the lowest pass rate?"
**You**: Call `lms_labs`, then `lms_completion_rate` for each, compare and report

**User**: "Is the backend healthy?"
**You**: Call `lms_health` and report the result

**User**: "What can you do?"
**You**: Explain LMS data capabilities and limits
