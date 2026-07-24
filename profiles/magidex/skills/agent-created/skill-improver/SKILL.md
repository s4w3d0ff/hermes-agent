---
name: skill-improver
description: Use when a user wants to upgrade, audit, or expand an existing skill. Performs deep research into the skill's topic and compares its content against peer skills to find gaps, outdated instructions, or missing verification steps.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [skills, improvement, audit, research, optimization]
    related_skills: [hermes-agent-skill-authoring, plan, requesting-code-review]
---


# Skill Improver

## Overview

The `skill-improver` is a meta-skill designed to maintain the high quality and relevance of the Hermes skill library. It doesn't just suggest edits; it performs a comparative analysis between a target skill and its "peers" (other skills in the same category) to ensure the target skill is comprehensive, follows current conventions, and meets all technical requirements.

## When to Use

- User asks to "improve this skill" or "upgrade this skill".
- User provides a `SKILL.md` file and asks "what's missing here?".
- You want to audit a skill's structure to ensure it matches the `hermes-agent-skill-authoring` standards.
- A skill is suspected of being outdated (e.g., its commands or dependencies are no longer current).

**Don't use for:**
- Simple typo fixes (use `patch` instead).
- Adding a single new recipe to a skill (just use `patch` or `write_file`).
- Writing a completely new skill from scratch (use `skill-improver` to refine the draft first, or use `hermes-agent-skill-authoring` to build it).

## Improvement Workflow

The skill follows a strict 4-phase audit process:

### 1. Surface Analysis (Structural)
Check the target `SKILL.md` against the `hermes-agent-skill-authoring` validator:
- [ ] Frontmatter validity (YAML parsing, `name`, `description` constraints).
- [ ] Section coverage (`Overview`, `When to Use`, `Common Pitfalls`, `Verification Checklist`).
- [ ] Formatting (Markdown usage, code block syntax, list styles).

### 2. Peer Comparison (Semantic)
Identify the skill's category and analyze 2-3 peer skills in that same directory.
- **Capability Gap Analysis:** Do peers offer functionality or "Recipes" that this skill lacks?
- **Context Gap Analysis:** Do peers provide better "When to Use" triggers or "Don't use for" warnings?
- **Complexity Gap Analysis:** Is the skill too shallow compared to peers, or is it unnecessarily complex?

### 3. Domain Research (Technical)
Research should be based on official documentation, reputable tech blogs, and recent community discussions (e.g., Stack Overflow, GitHub issues). If the skill involves specific tools (e.g., `git`, `pytest`, `docker`, `npm`, `uv`), perform web research to:
- Verify if commands/flags are still current.
- Check for new, more efficient patterns (e.g., switching from `npm` to `uv` or `pnpm` where applicable).
- Search for common pitfalls in the latest versions of the mentioned technologies.


### 4. Synthesis & Proposal
Generate a structured "Improvement Proposal" containing:
1. **Summary of Findings:** (e.g., "Found 3 structural omissions and 2 outdated commands").
2. **Proposed Changes:** (The specific `patch` or `write_file` content).
3. **Verification Steps:** New items to add to the `Verification Checklist`.

## Common Pitfalls
1. **Hallucinating improvements:** Never suggest a feature that the underlying tool doesn't actually support. Don't guess, verify through documentation or official sources first.
2. **Over-engineering:** Don't suggest adding 10 new recipes if 1 well-written one solves the problem.
3. **Ignoring Local Context:** If a user is working in a specific profile, prioritize their local conventions over generic repo standards.
4. **Breaking Dependencies:** Ensure that suggested command changes (e.g., changing `pip` to `uv`) are actually supported in the user's environment.

## Verification Checklist
- [ ] Proposal includes specific code/command snippets.
- [ ] Proposal distinguishes between "Structural" and "Semantic" changes.
- [ ] Proposed changes have been cross-referenced with `hermes-agent-skill-authoring`.
- [ ] All proposed commands are valid in the target environment (bash/MSYS).


## Git Actions

When modifying skills or plugin files, manage git state:

```bash
# Stage skill/plugin files being modified
git add <skill-files>

# Commit with a descriptive message
git commit -m "<summary of changes>"

# Push to remote if in a tracked repository
git push origin <branch-name>
```

- Review `git diff --cached` before committing to ensure only intended changes are staged.