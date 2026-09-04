---
name: project-planning
description: Outlines how to create MILESTONES.md and PLAN.md files for a project
version: 0.0.1
author: [s4w3d0ff, hermes]
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [plan, milestones, project planning, planning, agent planning]
---

### When to Use This Skill

- Creating a new project structure from scratch
- Planning milestones for an existing project
- Decomposing a milestone into executable phases and tasks
- Establishing clear project goals and verification criteria
- Creating task-level plans with test cases

##S Project Milestones File- `{projectroot}/.agents/MILESTONES.md`

A high-level project overview document that:

- Describes the overall project purpose and structure
- Lists required libraries and dependencies
- Defines sequential milestones (M0, M1, M2, etc.)
- For each milestone, includes a goal and verification checklist
- Serves as the source of truth for project scope

#### **Questions to Ask**

1. **Project Identity**: What is the project name, purpose, and where is it located?
2. **Structure**: What is the expected file/directory layout?
3. **Dependencies**: What libraries (built-in or third-party) will be needed?
4. **Overview**: What is the high-level flow? What are the main functions/modules/components?
5. **Milestones**: What are the sequential milestones needed to complete the project?

#### **Format:**

```markdown
# {Project Name} - ({project root location}) - [{github url}]
## **Project Structure**
{basic project files expected layout}
## **`.gitignore`** (base patterns)
{basic expected `.gitignore`}
## **Libraries**
{expected builtin/third party libraries to be used and why}
## **Overview**
{high level project overview, purpose of the project, expected flow, expected functions/methods/modules}
## **Milestones**
### **M0** - [{title}]
#### **Goal:**
{Overall goal of milestone}
#### **Verification:**:
{verifiable list of minimum expected deliverables, expected behaviors and function results, tests, no regression, full integration with project, etc}
```

#### **Content Guidelines**

- **Project Name**: Use the format `{Project Name} - ({project root location}) - [{github url}]`
- **Project Structure**: Show expected directory tree or file layout (e.g., `src/`, `tests/`, `docs/`)
- **`.gitignore`**: List base patterns relevant to the tech stack (e.g., `node_modules/`, `*.pyc`, `dist/`, `.env`)
- **Libraries** - For each library, explain:
  - Name and version (if applicable)
  - Why it's being used
  - What problem it solves
- **Overview** - Provide:
  - High-level purpose in 2-3 sentences
  - Expected data flow or workflow
  - Key functions, methods, or modules to be built
- **Milestones** - Define multiple sequential milestones (0-?):
  - M0: Foundation/scaffolding
  - M1: Core functionality
  - M2: Features
  - M3: Features
  - M4: Features
  - M5: ...

#### **Verification for Each Milestone**

Include a checklist of verifiable deliverables:

- Specific functions/methods implemented
- Expected behaviors and return values
- Passing test cases
- Integration requirements
- No regressions in existing functionality

#### **Best Practices**

1. **Be Specific**: Use concrete names and paths, not placeholders
2. **Realistic Scope**: Milestones should be achievable in 1-2 weeks of work
3. **Sequential**: Ensure milestones build on each other; avoid circular dependencies
4. **Complete**: Include all major components before moving to optimization

## Project Plans - `{projectroot}/.agents/{milestone}_PLAN.md`

A detailed breakdown of a specific milestone that:

- Extends the goal from `MILESTONES.md` with implementation details
- Decomposes the milestone into phases (Phase 0, Phase 1, etc.)
- Breaks each phase into testable, verifiable tasks
- Includes acceptance criteria and test examples for each task
- Acts as the execution guide for developers

#### **Questions to Ask**

1. **Scope**: What exactly needs to be delivered in this milestone?
2. **Dependencies**: Are there other milestones or tasks that must complete first?
3. **Phases**: How can this milestone logically break down into sequential phases?
4. **Tasks**: What are the smallest unit tasks that can be tested independently?

#### **Format:**

```markdown
# {milestone} Plan - `{milestone}_PLAN.md`
## Goal
{extended/detailed goal from MILESTONES.md for this particular milestone}
## Phase 0
{summary}
### Tasks
1. {task}
    - [ ] {task verification check/test}
    - [ ] {task verification check/test}
2. {task}
    - [ ] {task verification check/test}
    - [ ] {task verification check/test}
...

## Phase 1
...

```

#### **Content Guidelines**

- **Goal**: Restate and expand the goal from `MILESTONES.md` with implementation context
- **Phases**: Divide the milestone into 2-4 logical phases:
  - Phase 0: Setup/scaffolding (e.g., project structure, initial configuration)
  - Phase 1: Core implementation (e.g., main algorithms or features)
  - Phase 2: Testing and refinement (e.g., test suite, edge cases)
  - Phase 3: Integration and documentation (if applicable)
- **Tasks**: For each phase, list 3-8 granular tasks:
  - Task title should be a complete action (verb + object)
  - Include 2-4 verification checkboxes per task
  - Each checkbox should be a concrete, testable criterion

#### **Task Verification Criteria**

Each task verification should answer:

- **Exists**: Does the code/file/function exist?
- **Correct**: Does it behave as expected?
- **Tested**: Is it covered by tests or manual verification?
- **Integrated**: Does it work with other components?

#### **Best Practices**

1. **Atomic Tasks**: Each task should be completable in 2-4 hours
2. **Testable**: Every verification should be runnable or verifiable
3. **Ordered**: List tasks in dependency order (prerequisites first)
4. **Clear Acceptance**: A developer should know exactly when a task is "done"
5. **Examples**: Include code examples for expected outputs or behavior
6. **Realistic Estimates**: Be honest about complexity; break large tasks down further