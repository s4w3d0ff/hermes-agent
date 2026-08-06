---
name: kanban-gated-loop
description: Gated loop kanban guidelines intended for a kanban orchestrator.
version: 0.1.0
author: [Hermes, s4w3d0ff]
platforms: [linux]
metadata:
  hermes:
    tags: [Kanban, Gated, Task Management, Looped Pipeline]
    related_skills: [kanban-orchestrator]
---

## Gated Loop on a Kanban board

```python
# Plan1: root task
kanban_create(
    title="Initial Plan",  
    assignee="planner", 
    body="...",
    initial_status="blocked"     # delays dispatcher from claiming until we unblock the task
)
# Build1: Child of Plan
kanban_create(
    title="Initial Build",  
    assignee="builder", 
    body="...",
    parents=["plan_task_id"]
)
# Audit1: Child of Build1
kanban_create(
    title="Initial Audit",  
    assignee="auditor", 
    body="...",
    parents=["build1_task_id"]
)
# Build2: Child of Audit1 (start of 2nd loop)
kanban_create(
    title="Build2",  
    assignee="builder", 
    body="...",
    parents=["audit1_task_id"]
)
#...
#...
# Audit<N>: Child of Build<N> (end of pipeline)
kanban_create(
    title="Final Audit",  
    assignee="auditor", 
    body="...",
    parents=["build<N>_task_id"]    # final build task
)
```
`kanban_list()` ensure pipeline is setup correctly, allow dispatcher to claim via unblock the root task

### A single Gated Loop:

```
Plan
▼
Build ◄━━━━━━━━┓
┃              ┃
┃  Gated Loop  ┃
┃              ┃
┗━━━━━━━━► Audit ►  Final Audit
```

> This is a bare minimum Gated Loop. A single iteration, a single loop. The ethos of the Gated Loop is to do it as many times as possible to get the highest quality result. More iteration on the same goal creates stability and improved quality over time.

During each iteration of the loop, the orchestrators job is to maintain the loops health and add more iterations when the audits call for it. You should review the audit tasks, guide and encourage Gated Loop to make improvements during every loop and learn from its mistakes.

Use kanban comments to steer Gated Loop between iterations and keep it productive, children of tasks with comments inherit the comments downstream. This can be useful when Gated Loop needs to keep and communicate notes between loops.

## Gated Loop integration within advanced pipelines/workflows:

### Already established pipeline:

```
Research
▼
Plan
▼
Build
▼
Audit
▼
Deploy
```

#### How its created:

```python
# Research: root task 
kanban_create(
    title="Initial Research into Goal",  
    assignee="researcher", 
    body="...",
    initial_status="blocked"
)
# Plan: Child of Research 
kanban_create(
    title="Plan",  
    assignee="planner", 
    body="...",
    parents=["research_task_id"]
)
# Build: Child of Plan
kanban_create(
    title="Build",  
    assignee="builder", 
    body="...",
    parents=["plan_task_id"]
)
# Audit: Child of Build
kanban_create(
    title="Audit",  
    assignee="auditor", 
    body="...",
    parents=["build_task_id"]
)
# Deploy: Child of Audit (end of pipeline)
kanban_create(
    title="Deploy",  
    assignee="deployer", 
    body="...",
    parents=["audit_task_id"]
)
```

### Wiring a Gated Loop into the pipeline:

```
Research
▼
Plan 
▼
Build ◄━━━━━━━━┓
┃              ┃
┃  Gated Loop  ┃
┃              ┃
┗━━━━━━━━► Audit ► Deploy
```

#### If constructing entire pipeline:

```python
# Research: root task
kanban_create(
    title="Initial Research into Goal",  
    assignee="researcher", 
    body="...",
    initial_status="blocked"
)
# Plan: Child of Research 
kanban_create(
    title="Initial Plan",  
    assignee="planner", 
    body="...",
    parents=["research_task_id"]
)
# Build: Child of Plan
kanban_create(
    title="Initial Build",  
    assignee="builder", 
    body="...",
    parents=["plan_task_id"]
)
# Audit: Child of Build
kanban_create(
    title="Initial Audit",  
    assignee="auditor", 
    body="...",
    parents=["build_task_id"]
)
# Build2: Child of Audit (first loop back)
kanban_create(
    title="Build2",  
    assignee="builder", 
    body="...",
    parents=["audit_task_id"]
)
#...
#...
# Deploy: End of pipeline
kanban_create(
    title="Deploy",  
    assignee="deployer", 
    body="...",
    parents=[
        "audit_task_id",
        "audit2_task_id",
        "audit3_task_id",
        ,,,                 # each Gated Loop audit iteration should be a dependency to the end of the entire Gated Loop
        ]
)
```

## Wiring to a live pipeline:

### Sequential Non-looping Pipeline created already and dispatcher is claiming:

```python
# Research: root 
kanban_create(
    title="Initial Research into Goal",  
    assignee="researcher", 
    body="...",
    initial_status="blocked"
)
# Plan: Child of Research 
kanban_create(
    title="Initial Plan",  
    assignee="planner", 
    body="...",
    parents=["research_task_id"]
)
# Build: Child of Plan
kanban_create(
    title="Initial Build",  
    assignee="builder", 
    body="...",
    parents=["plan_task_id"]
)
# Audit: Child of Build
kanban_create(
    title="Initial Audit",  
    assignee="auditor", 
    body="...",
    parents=["build_task_id"]
)
# Deploy: End of pipeline
kanban_create(
    title="Deploy",  
    assignee="deployer", 
    body="...",
    parents=["audit_task_id"]
)
```
#### Add a Gated Loop to the live pipeline without reconstructing, adding a build task to the end of an audit is our entry point:

```python
# Build2: Child of Audit (above)
kanban_create(
    title="Build2",  
    assignee="builder", 
    body="Fix xyz from audit...",
    parents=["audit_task_id"]
)
# Audit2: Child of Build2
kanban_create(
    title="Audit2",
    assignee="auditor",
    body="Aggressive adversarial audit...",
    parents=["build2_task_id"]
)
# Make the end task of the pipeline dependant on the end task of our Gated Loop
kanban_link(parent_id="audit2_task_id", child_id="deploy_task_id")
```

#### REMEMBER: Always create a task with parents, if you don't define the parents on a live (unblocked) board the dispatcher will claim the task without a parent and run it in parallel (which is BAD). We want every task to have a parent, no orphans.

The audits should use `kanban_block()` when finding HIGH or greater gaps/issues while auditing. This allows the orchestrator time to properly create extra Gated Loops with relevant context from previous loops while maintaining task dependencies.

When a loop blocks and you need to add another loop, create the loop as a child of the blocked task, when everything is created and linked use `kanban_complete` on the blocked task so that the children tasks can move forward. If you call kanban_unblock it will trigger the blocked task to run first a second time (we do not want this).