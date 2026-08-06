---
name: kanban-user-interaction
description: >-
  Pipeline creation scope and question timing rules.
version: 0.1.0
author: Hermes, s4w3d0ff
platforms: [linux]
metadata:
  hermes:
    tags: [Kanban, Orchestrator, User Interaction, Pipeline Creation]
---

## Core Principles

### Execute exactly what is requested — no scope creep

When the user specifies a pipeline for certain milestones or components only, create ONLY those. Do not add extra work just because you think it should exist. If the user asks for M2-M4, do not add M0 or M1. Creating extra work beyond what was asked wastes resources and provokes strong negative feedback.

### When instructions are clear, execute without asking questions

If the user gives a detailed, unambiguous specification (board name, milestone range, profiles, branching strategy), do NOT ask clarifying questions about things already specified. Verify environment state first, then build directly. Only ask when there is genuinely ambiguous information that cannot be resolved by inspecting the environment yourself.

### Draft graph for review — but only when genuinely uncertain

When you are unsure about a parameter or approach, draft the pipeline graph and show it to the user for confirmation BEFORE creating tasks. This is appropriate when:
- A kanban board does not exist yet
- You are adding milestones beyond what was explicitly requested
- There are multiple valid approaches with meaningful trade-offs

This is NOT appropriate when:
- The user gave a detailed, specific specification
- All variables are already known from environment inspection
- Showing the graph would just repeat information the user already provided

## Pipeline Creation Flow

1. **Inspect**: Verify boards, profiles, and existing files exist in project directory
2. **Draft**: Write out pipeline graph with task IDs, assignees, parents, and status
3. **Execute**: Create all tasks via kanban_create, wire dependencies via kanban_link where needed
4. **Verify**: Call kanban_list to confirm board state matches your draft
5. **Stand down**: Once verified and nothing else needs doing, stop. Dispatcher handles progression.

## Pitfalls

- Asking questions when the user already specified everything → wastes time, frustrates user
- Adding milestones or components not explicitly requested → scope creep
- Creating tasks with empty parent arrays (orphans) → dispatcher runs them in parallel incorrectly
- Not verifying board state after creation → may miss wiring errors