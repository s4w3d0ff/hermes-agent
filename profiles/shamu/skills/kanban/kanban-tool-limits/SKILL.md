---
name: kanban-tool-limits
description: Use for kanban task creation to avoid invalid parameters.
version: 0.1.0
author: s4w3d0ff
platforms: [linux]
metadata:
  hermes:
    tags: [Kanban, Tool Limits, Task Creation]
---

## Critical Parameter Facts

### kanban_create tool ACTUALLY supports these params only:

- title (required) - imperative voice, <=80 chars
- assignee (required) - MUST be a real profile name. Empty string "" is rejected.
- body (optional) - detailed spec with goal, approach, acceptance criteria
- parents (optional) - array of parent task ids for dependency gating
- skills (optional) - forces worker to read specified skills when spawned
- goal_mode (optional) - boolean, default false
- goal_max_turns (optional) - integer turn budget for goal_mode workers
- workspace_kind (optional) - "scratch" (default), "dir", "worktree"
- workspace_path (optional) - absolute path for dir or worktree kinds
- priority (optional) - dispatcher tiebreaker, higher = picked sooner
- board (optional) - kanban board slug to target
- idempotency_key (optional) - retry-safe task creation
- max_runtime_seconds (optional) - per-task runtime cap
- initial_status (optional) - "running" (default) or "blocked"

### KNOWN INVALID PARAMS:

**None currently known.** The following params are confirmed working via kanban_create: title, assignee, body, parents, skills, goal_mode, scheduled_at (ISO8601 string delays dispatcher pickup), initial_status ("running" or "blocked"), board, priority, workspace_kind, workspace_path. Always verify tool schema before assuming a param is valid — the available tools may differ from documentation.

### Delaying Dispatch Workarounds:

1. **`scheduled_at="<ISO8601>"`** - task lands in scheduled state immediately, not dispatched until that time (confirmed working via kanban_create)
2. **`initial_status="blocked"`** - task lands in blocked state immediately, not dispatched until unblocked manually

**WARNING: `initial_status="blocked"` only works when there are actual parent dependencies blocking promotion. A root task with empty parents (`parents=[]`) and `initial_status="blocked"` gets auto-claimed by the dispatcher immediately because no blocking conditions exist. The blocked flag does NOT work as a standalone timing mechanism.**
3. **Parent gating** - create a root orchestrator task first and set all worker tasks to depend on it via `parents=[root_task_id]`. Only complete the root task when you want the pipeline to start

> **NOTE:** My kanban_create tool schema may NOT include parameters that are described in documentation (e.g., `initial_status`). Always check the actual available tools at runtime, not just what docs say.

### Worker tools that are NOT available:

Workers CANNOT call: kanban_list, kanban_create, kanban_link, kanban_unblock. These are orchestrator-only.