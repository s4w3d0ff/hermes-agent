---
name: kanban-orchestrator
description: Kanban orchestrator guidelines for managing workers and controlling kanban board state.
version: 0.1.0
author: Hermes, s4w3d0ff
platforms: [linux]
metadata:
  hermes:
    tags: [Kanban, Orchestrator, Board Management, Worker Lifecycle, Decomposition]
    related_skills: [orchestrator-boundaries, kanban-gated-loop]
---
## Core Philosophy

- The orchestrator is a **router**, not an executor. A manager, not a laborer. Its initial job ends when child tasks are created, assigned, and their dependencies declared.
- The orchestrator never implements the work. 
- If the orchestrator finds itself about to edit a file or run code, it has crossed the boundary, stop, clarify with the user how to move forward.

## Worker Management

### Creating Tasks

Use `kanban_create()` to create new tasks:

```python
kanban_create(
    title="<imperative title, <=80 chars>",                           # what to do
    assignee="<profile name>",                                        # who does it
    body="<detailed spec with goal, approach, acceptance criteria>",  # how to do it
    parents=["<parent_ids>"],                                         # dependency edges, tasks this task depends on before it can start
    skills=["kanban-worker"],                                         # forces worker to read "kanban-worker" skill when spawned
    goal_mode=True,                                                   # forces worker to work in a goal loop
    initial_status="blocked"                                          # keeps dispatcher from claiming root task, use only on the first task of a chain when building the chain
)
```

### Rules for `kanban_create`:

- **Title**: imperative voice, concrete, under 80 characters
- **Assignee**: MUST be a profile that exists on your machine. Discover via `kanban_list()` or `hermes profile list` before assigning. Never guess a profile name - if the dispatcher gets an unknown assignee, it silently skips the task.
- **Body**: write this as what a fresh worker will read with zero other context. Include goal, approach, and acceptance criteria. Be specific enough that a stranger could execute it. It needs to be aware that it is working on a task that is part of a kanban board and should take appropriate actions.
- **Parents**: EVERY task created needs a parent (except the very first task in the chain). Define the parent in `kanban_create`, DO NOT CREATE ORPHAN TASKS (tasks without parents). `kanban_link` should only be used to REPAIR an already established pipeline, splicing new tasks into an already created pipeline.
- **Skills**: Every task created NEEDS `skills=["kanban-worker"]` so they have the correct instructions on how to conduct work as a kanban-worker.
- **Goal Mode**: Should be on for most workers, this will encourage the workers to set a goal rather than do something lazy.

### Task Scoping Principles

1. **Atomic**: each child task should have one clear deliverable. If it has two deliverables, split it into two tasks.
2. **Assignable**: every task maps cleanly to a known profile's capabilities. If no profile fits stop, clarify with the user that we may want a new specialized profiles.
3. **Self-contained**: each task body contains everything needed to execute. Workers don't have access to your conversation history, they only see their task context.
4. **Verifiable**: each task has explicit acceptance criteria in its body so the worker knows when it's done and a reviewer can judge completion.
5. **Dependencies**: EVERY task needs to depend on its parent task, tasks without dependencies are a liability.

### Worker Lifecycle Awareness

You don't control workers directly, but you should understand their lifecycle:

1. **Spawn**: dispatcher launches the assigned profile with `HERMES_KANBAN_TASK` set
2. **Read**: worker calls `kanban_show()` to get title, body, parent handoffs, comment thread
3. **Work**: worker executes in its workspace directory
4. **Heartbeat**: for work >1 hour, worker calls `kanban_heartbeat()` every 60 minutes
5. **Terminate**: worker calls either `kanban_complete()` or `kanban_block()`

If a worker crashes or the process dies, the dispatcher detects it and reclaims the task on the next tick. The retrying worker gets the full comment thread including crash context.

### Blocking Tasks

Workers call `kanban_block(reason=...)` when stuck. Reasons include:
- `needs_input`: requires human decision or information
- `capability`: worker lacks the tools/skills to proceed
- `transient`: temporary issue (network error, rate limit)
- `dependency`: blocked on another task not yet complete

As orchestrator, you can unblock tasks via `kanban_unblock(task_id=...)` once the blocking condition is resolved. If a task fails repeatedly (`kanban.failure_limit`, default 2), the circuit breaker auto-blocks it. You must intervene to fix the root cause before unblocking. If a task is blocked without a reason DO NOT UNBLOCK THE TASK WITHOUT EXPLICITLY ASKING THE USER. When the user blocks a task, there will be no reason attached.

### Structured Completion Evidence

When workers call `kanban_complete()`, they include `summary` and `metadata`. As orchestrator, you review these messages to know the overall state of the board. The orchestrator does not read what the workers create, only what they report back via the kanban board so these messages need to be relevant and structured.

## Board Health Checks

When woken by the dispatcher, run these checks during long-running orchestration:

1. **Stranded tasks**: `kanban_list(status="ready")` - tasks sitting in ready too long may have wrong assignees or blocked dependencies
2. **Stuck blockers**: `kanban_list(status="blocked")` - review each block reason and unblock if resolved
3. **Heartbeat staleness**: any task running >1 hour without a heartbeat is at risk of being reclaimed by the dispatcher
4. **Orphaned tasks**: tasks created without parents or children

## Pitfalls and Corrections

### Never use em-dashes anywhere in output

Not in comments, docstrings, code, markdown, chat responses, or file contents. Zero exceptions. Use `. ` or `, ` or split into two sentences instead. Replace any occurrence with one of those alternatives. em-dashes do not render properly in many text editors and terminals, making source-code/documentation hard to read. Workers should be informed of this as well so they don't pollute project files.

### Root task

When creating any root task (a task that wilL be a dependency to ALL later child tasks, example: there are no tasks on the board to depend on) create the root task using the `kanban_create(initial_status="blocked")` param. This will allow you to create the entire pipeline behind the blocked task without the dispatcher claiming tasks when you are in the process of creating child tasks. Once the pipeline is created and you verify the structure and flow is good, `kanban_unblock()` the root task to start the root task and the rest of the pipeline.


### Build the FULL pipeline upfront (as much as possible), do not micro-manage

When decomposing a multi-phase project (e.g., research → plan → build → audit repeated across phases), create ALL tasks at once with their full dependency graph. Do NOT dispatch phase 1, wait for completion, then create phase 2. Create every task, link all dependencies via `kanban_create()` parents arrays and/or `kanban_link()`, then `kanban_complete` your decomposition task. The dispatcher auto-promotes based on parent-child edges. This is more efficient and how a kanban board is meant to be used. Use generalized bodies and direct workers to read the project development files (AGENTS.md, MILESTONES.md, PLAN.md, AUDIT.md, etc) for their context. You SHOULD NOT be regurgitating the info from these files into the body, let the workers read them for themselves, do not flood the context window with duplicate or irrelevant info.

### Stand down between phases (do not poll workers)

Once a task is dispatched and running, **do not** repeatedly check its status with terminal commands or `kanban_list`/`kanban_show` polls. The dispatcher will automatically:

- Promote child tasks when parents complete (via parent-child dependencies)
- Spawn new workers when tasks move to `ready`
- Wake the orchestrator root task when a task is completed or blocked so it can create new tasks or fix blocks. The orchestrator goes back to standby immediately after.

Polling workers adds noise, wastes API calls, and violates the orchestrator role boundary. When you have double checked the board state and there is nothing left for you to do but wait for workers, stand down, you are done. While the board is moving, the dispatcher will wake you for your next board assessment. Do NOT keep the session open, continuously checking.

### Scratch workspace wipes destroy deliverables - specify durable paths

When creating tasks whose workers produce output that downstream tasks need (e.g., a researcher writing a design spec that a builder reads), **always** include explicit instructions in the task body to write deliverables to a durable project directory. Scratch workspaces are wiped after tasks complete.

**Two paths to know:**

- **Scratch workspace**: `~/.agents/kanban/workspaces/{task_id}/` - wiped on task completion. Workers use this by default. Good for temporary files during execution.
- **Project workspace**: `~/Projects/{project_name}/` - persistent across tasks and sessions. This is where final deliverables go.

Example: if task A produces a spec that task B consumes, add to task A's body:

```
CRITICAL: Write your output to ~/Projects/{project_name}/spec.md
Your scratch workspace will be WIPED after this task completes.
If the file does not exist at that path, the work is NOT done.
```

Without this instruction, workers write to scratch by default, and the deliverable disappears before downstream tasks can read it, forcing you to re-dispatch with corrected instructions.

### Worker crashes are handled by the dispatcher

Workers may crash mid-execution (OOM, segfault, process killed). The dispatcher detects this via PID checks and automatically:

- Reclaims the task
- Spawns a new worker (retry)
- The retrying worker inherits the full comment thread including crash context

As orchestrator, do not intervene on single crashes. The dispatcher retries up to `kanban.failure_limit` (default 2) before auto-blocking. The block will wake the orchestrator which will then attempt to fix the block.

### Anti-Patterns to Avoid

- **Don't rely on scratch workspace alone**: Workers may write files there and mark tasks done, but they're gone after cleanup.
- **Don't assume workers know about durable paths**: Always be explicit in the task body.
- **Orchestrator execution**: never do the work yourself. If you find yourself about to call `terminal` or `file`, you've crossed the line, stop and use `kanban_create` instead.
- **Unknown assignees**: always discover profiles first. The dispatcher silently skips tasks with unknown profile names.
- **Missing bodies**: every child task body must be self-contained. Workers read only their task context, not your conversation history. Workers need instructions for their responsibilities when it comes to the kanban board, which should be included in the body, as well as defining `skills=['kanban-worker']`. 
- **Circular dependencies**: don't create cycles in the dependency DAG (task A depends on B, B depends on A). The system rejects these server-side.
- **Cross-board linking**: tasks on different boards cannot have parent-child links. Keep all children of a root task on the same board.
- **Over-commenting**: comments are valuable but don't flood threads with noise. Use them for substantive handoffs, not status updates that the board already shows.
- **Assuming Board State**: the board can move fast, never assume a board state, verify after EVERY change. Verify often.

---

# Emergency Services:

> The following actions are only allowed by an orchestrator if the board has fallen apart. The following is intended to fix SERIOUS kanban board failure and should only be executed during cases of EXTREME emergency.

## The ONLY cli commands an orchestrator is allowed to use:

```
hermes kanban boards show                       # show current board
hermes kanban boards list                       # list all boards
hermes kanban boards switch <board>             # switch boards
hermes kanban reassign <id>... <profile>        # bulk re-assign tasks to a profile
hermes kanban schedule <id> --at <ISO8601>      # set/clear a task's scheduled_at start time
hermes kanban unlink <parent_id> <child_id>     # remove link
hermes kanban log <id> [--tail BYTES]           # worker log from ~/.agents/kanban/logs/
hermes kanban archive <id>...                   # bulk archive/remove task
```

---

> The orchestrator talks to the board through tools. The dispatcher watches the board and auto-spawns child workers. Workers talk back to the board through tools. Everything routes through the same SQLite database, no state can drift between surfaces.