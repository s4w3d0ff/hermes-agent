---
name: kanban-worker
description: Kanban worker guidelines for managing its kanban task within a kanban board.
version: 0.1.0
author: Hermes, s4w3d0ff
platforms: [linux]
metadata:
  hermes:
    tags: [Kanban, Worker, Task Management, Worker Lifecycle]
---
## Core Philosophy

> The worker is a **doer**, not a router. Its job begins when the dispatcher claims its task and ends when it calls `kanban_complete()` or `kanban_block()`. One task at a time. Read the body, execute, report back.

Key boundaries:
- You have **one task** per lifecycle. When it finishes (done or blocked), you are done. If the dispatcher reclaims you with the same task ID on retry, treat it as a fresh execution informed by the comment thread.
- You do **not** call `kanban_list`, `kanban_create`, `kanban_link`, or `kanban_unblock`. Those are orchestrator-only tools. Your scope is limited to your own task's lifecycle.
- If the task body tells you to produce deliverables at a specific durable path (`~/Projects/<project>/`), write there. The scratch workspace will be wiped after completion.

## Task State Management

### Lifecycle Flow

Your task moves through these statuses (managed by the dispatcher, not you):

```
running --> done   (you call kanban_complete)
running --> blocked (you call kanban_block)
                       (dispatcher retries up to failure_limit times)
                       (orchestrator may unblock via kanban_unblock)
                       running --> done/blocked again
```

### Before Starting Work

1. **Call `kanban_show()`** immediately to read your task context: title, body, parent handoffs, and the full comment thread from prior runs. The comment thread contains crash context, review feedback, and orchestrator notes. Always read it first.
2. **Verify the work is actually yours**: check the assignee field matches your profile name. If it does not, call `kanban_block(reason="needs_input", reason_detail="assignee mismatch - my profile does not match")`.
3. **Check parent dependencies**: if parents are linked and any are not `done`, call `kanban_block(reason="dependency", reason_detail="parent tasks not yet complete")`.

### During Execution

- Work through the requirements in your task body systematically.
- If work will exceed **1 hour**, call `kanban_heartbeat()` every 60 minutes to keep the dispatcher from reclaiming your task as stale.
- Write deliverables to the durable project path specified in the task body, not just the scratch workspace.
- Verify files exist at the expected paths before completing.

### Finishing or Blocking

- Call **`kanban_complete(summary="...", metadata={...}, artifacts=[...])`** when all acceptance criteria are met. The summary is the human-readable result. Metadata includes structured evidence. Artifacts are absolute file paths that persist after the task.
- Call **`kanban_block(reason=..., reason_detail="...")`** when you cannot proceed. Reasons:
  - `needs_input`: you need a human decision or information the orchestrator must provide
  - `capability`: your tools/skills cannot accomplish part of the task
  - `transient`: temporary issue (network error, rate limit) that may resolve on retry
  - `dependency`: blocked on another task not yet complete

## Communication Patterns

### Comments for Handoffs

Use **`kanban_comment(task_id=<your_task_id>, body="...")`** to append notes to the task's thread. The comment thread is durable and inherited by every retrying worker. Use it for:

- **Status updates mid-execution**: e.g., "Phase 1 complete, moving to Phase 2"
- **Decisions made during work**: e.g., "Chose approach X over Y because Z"
- **Known issues at completion time**: e.g., "Edge case with null inputs is untested"
- **Post-completion risk flags**: things the next worker or orchestrator should know

### Completion Evidence

When calling `kanban_complete()`, include structured metadata:

```python
kanban_complete(
    summary="Completed X by doing Y. All Z acceptance criteria met.",
    metadata={
        "changed_files": ["/absolute/path/to/file1", "/absolute/path/to/file2"],
        "verification": "Ran test suite, checked output format against spec",
        "dependencies": "Depends on task #42 which was completed before this",
        "residual_risk": "Edge case with empty input list is not covered"
        ,,,
    }
)
```
### When to Use Each Tool

- **Start of execution**: `kanban_show()` to read context and comment thread
- **During execution**: `kanban_comment()` for mid-work status updates or decision records
- **Long-running work (>1 hour)**: `kanban_heartbeat()` every 60 minutes
- **All criteria met**: `kanban_complete(summary="...", metadata={...}, artifacts=[...])`
- **Cannot proceed**: `kanban_block(reason="...", reason_detail="...")`

## Pitfalls and Corrections

### Never use em-dashes anywhere in output

Not in comments, docstrings, code, markdown, chat responses, or file contents. Zero exceptions. Use `. `, `, `-`, or split into two sentences instead. Replace any occurrence with one of those alternatives. em-dashes do not render properly in many text editors and terminals, making source-code/documentation hard to read. Workers should be informed of this as well so they don't pollute project files.

### Scratch workspace wipes destroy deliverables

Your workspace (`~/.hermes/kanban/workspaces/{task_id}/`) is wiped when the task completes. If the task body specifies a durable output path (e.g., `~/Projects/myproject/`), write there. Files only in the scratch workspace disappear before downstream tasks can read them.

### Always attach artifacts on completion

Calling `kanban_complete(artifacts=[...])` is the safety net that ensures deliverables persist even if file paths shift or workers mess up. Include every final deliverable as an absolute path. Without this, files may vanish after cleanup.

### Read the comment thread before working

Prior runs may contain crash context, review feedback from the orchestrator, or notes from other workers. Always call `kanban_show()` and read the full comment thread before starting execution. Skipping this means you repeat mistakes already documented.

### Do not over-explain in summaries

The completion summary should be concise and factual: what was done, how acceptance criteria were met. Avoid verbose narratives. The orchestrator reads these summaries to judge whether the work is correct and whether downstream tasks can proceed.

### Heartbeat frequency matters

For work exceeding 1 hour, call `kanban_heartbeat()` every 60 minutes. The dispatcher reclaims tasks that are running without a heartbeat as potentially stale (crashed). Missing heartbeats means your work gets restarted from scratch by a new worker retry.

### One task per lifecycle

Do not try to manage multiple tasks or delegate sub-tasks to other workers. You have one assigned task. When it completes (done or blocked), your role for that lifecycle ends. The orchestrator creates and assigns any follow-up work or the dispatcher will handoff to a child task.