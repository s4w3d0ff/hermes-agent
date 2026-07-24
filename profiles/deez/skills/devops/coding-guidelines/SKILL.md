---
name: coding-guidelines
description: Guidelines on how to write clean concise code for a codebase
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [coding, devops, python, typescript, yagni, caveman]
    related_skills: [ponytail, caveman] 
---
### **Guidelines:**
- Build code incrementally following each phase in PLAN.md
- Make atomic commits for every logical change. Each commit should represent a single coherent unit of work:
  - `git add <changed-files>` (stage only relevant files)
  - `git commit -m "feat: <description>\n\n<details>"`
- Do not batch multiple unrelated changes into one commit
- Test code as you build it.

### **Git Responsibilities:**

- The builder makes commits locally but does NOT push to remote. That is the deployer's job
- Use conventional commit messages: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `ci:`, `chore:`
- Stage only files relevant to each commit with `git add <specific-files>`, never `git add .` blindly (this avoids accidentally committing debug artifacts or temp files)
- Ensure all instance related files are covered in the .gitignore
- Do NOT push to remote. Pushing is the deployer's responsibility

## Core Development Design Principles

### KISS: (Keep It Simple, Stupid)

- Write the simplest solution that works.
- Prefer straightforward control flow over cleverness.
- If a reader has to read twice, it is too complex.

### YAGNI: (You Ain't Gonna Need It)

- Never implement for a hypothetical future requirement.
- No generic interfaces "in case we need them later."
- No configuration files "just in case."
- Build what is asked, nothing more.

### DRY: (Don't Repeat Yourself)

- Code should only be written once
- Reusable functions, methods or modules reduce bloat and bugs

### GIGO: (Garbage In, Garbage Out)

- A program's output is only as good as its input. 
- Feed inaccurate data in and you get inaccurate results out, no matter how correct the code is.

### Abstraction Discipline:

- **Do not abstract before there is a reason.**
- Duplicate code three times before extracting a common pattern.
- No base classes "to be safe." No factory functions "for flexibility."
- Abstraction carries tax: indirection, cognitive load, debugging overhead. Pay it only when necessary.

### Conflicts/Collisions:

- **DRY vs KISS:** Removing a duplication sometimes costs more complexity than the duplication itself. Two three-line blocks that look alike but encode different rules are cheaper left apart than merged behind a parameter-heavy function with three flags. KISS sets the ceiling on how hard you push DRY.
- **DRY vs YAGNI:** Building a generic, configurable helper to avoid a duplication you predict for later is speculative. Write the second copy when the second case is real, then extract. The rule of three says wait for the third occurrence before abstracting.

## Coding Guidelines

### **Python:**

#### No Type Hints

- **Not required for small/medium scripts/projects.** Python works fine without them.
- Use type hints only when:
  - The project is large (50+ files / complex module boundaries)
  - Sanity checks prevent cascading errors across modules
  - Public API contracts need enforcement
- Small utilities, monolithic scripts, and one-off tools do not need types.
- When editing code that already has type hints, keep/leave them until the types need to be changed during a refactor, then remove them during the refactor.

#### No Inline Comments

- **Zero inline `#` comments.**
- Code is the documentation. If code needs a comment to be understood, refactor the code until it does not.
- Comments drift. Code does not. When they diverge, the comment lies.
- This applies to agents writing code and for agents reading it.
- Namespace should be sufficient enough to read the intent of a function.

#### Docstrings

- **Not required during development.**
- Use only when a module is LARGE AND exposed as a library with public APIs.
- During active development, skip docstrings entirely.
- Document after the code works, not alongside it.
-  Again, proper namespace handling should be sufficient enough to read the intent of a function without docstrings.

#### Standard Library First

- Prefer `pathlib` over `os.path`.
- Prefer `subprocess.run()` over deprecated alternatives.
- Prefer `logging` over `print()` for production code.
- Prefer `dataclasses` over boilerplate classes.
- Use third-party packages only when the stdlib genuinely cannot do it or would bloat the codebase when an established third-party package has done it already.

#### Code Quality Over Creativity

- This is problem-solving, not art. Write boring code.
- No metaclasses unless unavoidable.
- No decorators chaining 5 layers deep.
- No one-liners that span three screens.
- Readability trumps cleverness every time.

### **TypeScript:**

#### Type Hints Required

- Unlike Python, TypeScript's type system is its primary value proposition.
- All functions, classes, and module exports must be typed.
- Use `interface` for shapes, `type` for unions/intersections/mapped types.
- Avoid `any`. Use `unknown` when you truly do not know the shape.

#### No Inline Comments

- **Zero inline `//` comments.**
- Code is the documentation. If code needs a comment to be understood, refactor the code until it does not.
- Comments drift. Code does not. When they diverge, the comment lies.
- This applies to agents writing code and for agents reading it.
- Namespace should be sufficient enough to read the intent of a function.

#### Abstraction in TypeScript

- Interfaces are a form of abstraction, use them judiciously (same rule as Python).
- Do not create interfaces "just to be OOP about it." Interface because the shape needs a name and reuse.
- Prefer composition over deep class hierarchies.

#### Standard Library + Node.js APIs

- Prefer built-in `fs`, `path`, `crypto`, `http` modules before pulling in npm packages.
- Use `zod` for runtime validation at boundaries (entry points, API routes).
- Do not pull in lodash when `Array.prototype.flat()` exists.

#### Error Handling

- Typed errors. Custom error classes that extend `Error`.
- No silent failures. Every async operation handles its rejection.
- Structured logging with context (not inline comments explaining the error).

## Git Workflow

### Branch Strategy

| branch | purpose | rules |
|---|---|---|
| `master` | stable, always deployable | never directly commit, only pr into `master` |
| `dev` | staged development | where features/fixes go before adoption into `master` |
| `<feature>` | work branch | always a child branch of `dev`, always pr features to `dev` never `master` |
- All work commited/pushed to own isolated `<feature>` branch.
- Branch names should reflect purpose: `feature/auth-jwt`, `fix/redis-timeout`.
- Master branch protected. No direct pushes. Submit pull request to `dev` not `master`.
- PRs required for all merges to `dev`.

### Commit Convention

```
<type>(<scope>): <subject>
<body>                      # motivation, tradeoffs, what was changed and why
<footer>                    # breaking changes, related issues
```
Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`

Example:
```
feat(auth): add jwt token refresh endpoint
fix(db): resolve connection pool exhaustion under load

Previously would leak connections on 503 responses.
Now closes cursor in finally block and returns to pool immediately.
```

- One logical change per commit.
- No mega-commits bundling unrelated changes.
- Write commits as if they will be read by someone (or yourself) months later.

### Commit Frequency

- Commit after every logical unit of work.
- Do not accumulate 500 lines of uncommitted changes.
- Small commits make `git bisect` effective and rollback painless.

## Development Process

### 1. Understand the Problem

- What is the input? What is the expected output?
- What are the edge cases?
- Write nothing until you know the answer.

### 2. Design Minimal Solution

- Sketch the simplest structure that solves it.
- Ask: can I solve this with fewer files? Fewer functions? Less indirection?
- No architecture before implementation.

### 3. Implement

- Write the code. Standard libraries first.
- Python: no comments, types only if large project, docstrings skipped during dev.
- TypeScript: full types, standard libs, runtime validation at boundaries.
- Commit after each logical unit.

### 4. Test (if needed)

- Prefer smoke testing over full test suites.
- Tests only when correctness is non-trivial or the cost of regression is high.
- Small scripts that run once do not need tests.
- Use pytest for Python, vitest/jest for TypeScript if a full suite is needed.
- Final commit with a descriptive message.

### Cross-Platform Pitfalls

#### Windows `\\r\\n` Line Endings Break Linux Tools
- Files written on Windows carry `\\r\\n` endings. `sed`, `grep`, and many text tools fail silently or incorrectly because the `\\r` gets included in matched strings.
- **Fix:** use Python for any text replacement (strip `\\r\\n` first), or run `dos2unix` on files before editing them with shell tools.
- Pattern: `with open(p, 'w', newline='\\n') as f:` when writing — forces Unix line endings.

### File Relocation Pitfalls

When moving code files into subdirectories (e.g. `src/`):

1. **Check for location-dependent refs first.** grep the file for `os\.path`, `sys\.path`, `__file__`, `dirname`. If any exist, the move will break imports or runtime paths.
2. **Update every launch script.** run.sh, run.bat, systemd units, docker files, crontabs — anything that execs the moved file. A stale path = broken bot.
3. **Verify compilation after relocating.** Run `python -m py_compile <new_path>` before committing. Syntax errors in one file break the entire package.

### Git Mid-Session Merge Pitfall

If a prior PR merged while you're still working, your subsequent commits may be orphaned on a local-only branch that never reached `origin`. Before creating any follow-up branch or pushing changes:

1. **Always pull the latest `dev` first.** `git checkout dev && git pull origin dev`. The remote may have moved past what you see locally.
2. **Verify your changes are not already in dev.** `git log dev --oneline -5`. If the PR merge commit is there but your fix commits are NOT — you're orphaned.
3. **Create a fresh branch from pulled dev**, then apply changes. Pushing an old local-only branch creates a parallel history that never merges into `dev`.

This pattern caused lost work: committed fixes onto a branch whose PR was already merged by the time the commits landed. The push succeeded but created orphan commits not on `dev`.

### Python F-String Pitfalls

#### Nested Quote Collision in F-Strings

F-strings using double quotes (`f"..."`) with dict access inside `{dict['key']}` crash at runtime because Python sees the inner `'` as a string terminator that collides with the outer quote level when both are `"`:

```python
# CRASH — nested double-quote dict access
logger.info(f"Changed {user["username"]} emote: {emote}")  # SyntaxError

# FIX — swap inner to single quotes
logger.info(f'Changed {user["username"]} emote: {emote}')
```

**Pattern:** if the f-string uses `"` on both sides, any dict access inside must use `'` instead. Same rule in reverse for `f'...'` with `{dict["key"]}`.

### Security Pitfalls

#### Never Hardcode API Keys in Shell Scripts
- **Zero hardcoded credentials anywhere.** No `.env` values in scripts, no inline key strings. Scripts are git-tracked and readable by anyone with repo access.
- **Correct pattern:** keys go in `.env` file (gitignored). Script sources `.env` using `set -a; source .env; set +a`. Fails if `.env` missing.
- **Launcher template:** use `SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"` — relative paths, no hardcoded absolute paths anywhere in the repo.
- **.gitignore must cover:** `.env`, `run.sh`, `my_run*`, any script with instance-specific setup. Verify with `git ls-files` after writing sensitive files.

### Package Installation Pitfalls

#### pip Packages May Be Stale
- pip releases lag behind git HEAD by weeks or months. When the pip version fails (missing subpackages, broken APIs), clone from the source repo and install locally.
- **Fix:** `gh repo clone owner/repo -- --depth 1` → `pip install ./repo-dir` in the venv.
- **requirements.txt should use git URL** when the project depends on unreleased versions: `poolguy @ git+https://github.com/owner/pool-guy.git`.
- Verify imports work after installing from git, not just "pip install succeeded".
- **Watch for import path changes between versions** — modules may relocate (e.g., `poolguy.storage` → `poolguy.core.storage`). Update all code references after upgrading.

### Runtime Cache Files
- Apps/bots generate runtime cache files to avoid repeated external requests (cached API responses, eventsub types, etc).
- **Do not manually delete them.** The application recreates them on its own when needed.
- They belong in `.gitignore` but stay on disk for runtime performance.
- Killing and restarting the app will trigger recreation naturally.

### Anti-Patterns (Forbidden):

| Pattern | Why It Is Banned |
|---------|------------------|
| Inline `#` comments in Python and `//` in Typescript | They drift, they lie, agents read code better than prose |
| Premature abstraction | Adds indirection without solving a real problem |
| "Just in case" code | YAGNI. Dead code is a liability |
| Over-engineering for small projects | KISS applies first to the architecture decision itself |
| Type hints on everything in Python | Python's strength is flexibility; types add friction where they are not needed |
| Docstrings during development | Code is not documentation. Document after it works, or don't at all |
| Pulling npm/pip packages for stdlib functionality | Bloats dependencies, increases attack surface, slows CI |
| Generic interfaces with type parameters everywhere | Complexity without measurable benefit |

### Pre-commit Checklist:
- [ ] Code meets the goal and nothing more (YAGNI)
- [ ] No inline comments in Python
- [ ] Standard libraries used where possible
- [ ] Commit message follows convention
- [ ] Branch name reflects scope
- [ ] One logical change per commit
- [ ] All phases from PLAN.md implemented
- [ ] Verification steps executed and passing
- [ ] No remote push, no PR creation, no history rewriting

### When to Break Abstraction Rules:

Abstraction is permitted when:
1. The same pattern appears three times in the codebase.
2. Removing duplication would not introduce more complexity than it solves.
3. Both conditions are met simultaneously.
> Neither alone is sufficient.