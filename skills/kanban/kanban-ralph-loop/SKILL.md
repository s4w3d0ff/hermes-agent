---
name: kanban-ralph-loop
description: Ralph loop kanban guidelines intended for a kanban orchestrator.
version: 0.1.0
author: [Hermes, s4w3d0ff]
platforms: [linux]
metadata:
  hermes:
    tags: [Kanban, Ralph, Task Management, Looped Pipeline]
    related_skills: [kanban-orchestrator]
---
# Ralph Loop

> Named after the infamously high-pitched, hapless yet persistent character on The Simpsons.

### **Concept:**

    Building software with Ralph requires a great deal of faith and a belief in eventual consistency. Ralph will test you. Each time Ralph does something bad, Ralph gets tuned - like a guitar.

    It begins with no playground, and Ralph is given instructions to construct one.

    Ralph is very good at making playgrounds, but he comes home bruised because he fell off the slide, so one then tunes Ralph by adding a sign next to the slide saying "SLIDE DOWN, DON'T JUMP, LOOK AROUND," and Ralph is more likely to look and see the sign.

    Eventually all Ralph thinks about is the signs so that's when you get a new Ralph that doesn't feel defective like Ralph, at all.

    To get good outcomes with Ralph, you need to ask Ralph to do one thing per loop. Only one thing.

    One item per loop. I need to repeat myself here-one item per loop. You may relax this restriction as the project progresses, but if it starts going off the rails, then you need to narrow it down to just one item.

    The name of the game is that you only have approximately 170k of context window to work with. So it's essential to use as little of it as possible. The more you use the context window, the worse the outcomes you'll get.

    A common failure scenario for Ralph is when the agent runs ripgrep and comes to the incorrect conclusion that the code has not been implemented. This failure scenario is easily resolved by erecting a sign for Ralph, instructing Ralph not to make assumptions.

    > Before making changes search codebase (don't assume an item is not implemented). Think hard.

    If you wake up to find that Ralph is doing multiple implementations, then you need to tune this step. This nondeterminism is the Achilles' heel of Ralph.

    You want to program in ways where Ralph can loop himself back into the agent for evaluation. This is incredibly important. Always look for opportunities to loop Ralph back on itself. This could be as simple as instructing it to add additional logging, or in the case of a compiler, asking Ralph to compile the application and then looking at the LLVM IR representation. 

    During a loop, Ralph might determine that something needs to be fixed. It's crucial to capture that reasoning.


## Ralph on a Kanban board

```python
# Plan1: root task
kanban_create(
    title="Initial Plan",  
    assignee="planner", 
    body="...",
    scheduled_at="2026-06-01T03:00:00Z"     # delays dispatcher from claiming until set time
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
`kanban_list()` ensure pipeline is setup correctly, allow dispatcher to claim when scheduled

### A single Ralph loop:

```
Plan
▼
Build ◄━━━━━━━━┓
┃              ┃
┃  Ralph Loop  ┃
┃              ┃
┗━━━━━━━━► Audit ►  Final Audit
```

> This is a bare minimum ralph loop. A single iteration, a single loop. The ethos of the Ralph loop is to do it as many times as possible to get the highest quality result. More iteration on the same goal creates stability and improved quality over time.

During each iteration of the loop, the orchestrators job is to maintain the loops health and add more iterations when the audits call for it. You should review the audit tasks, guide and encourage ralph to make improvements during every loop and learn from its mistakes.

Use kanban comments to steer ralph between iterations and keep it productive, children of tasks with comments inherit the comments downstream. This can be useful when ralph needs to keep and communicate notes between loops.

## Ralph integration within advanced pipelines/workflows:

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
    scheduled_at="2026-06-01T03:00:00Z"
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

### Wiring a Ralph loop into the pipeline:

```
Research
▼
Plan 
▼
Build ◄━━━━━━━━┓
┃              ┃
┃  Ralph Loop  ┃
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
    scheduled_at="2026-06-01T03:00:00Z"
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
        ,,,                 # each ralph audit iteration should be a dependency to the end of the entire ralph loop
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
    scheduled_at="2026-06-01T03:00:00Z"
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
#### Add a ralph loop to the live pipeline without reconstructing, adding a build task to the end of an audit is our entry point:

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
# Make the end task of the pipeline dependant on the end task of our ralph loop
kanban_link(parent_id="audit2_task_id", child_id="deploy_task_id")
```

#### REMEMBER: Always create a task with parents, if you don't define the parents on a live (unblocked) board the dispatcher will claim the task without a parent and run it in parallel (which is BAD). We want every task to have a parent, no orphans.

The audits should use `kanban_block()` when finding HIGH or greater gaps/issues while auditing. This allows the orchestrator to properly create extra ralph loops with relevant context from previous loops while maintaining task dependencies.