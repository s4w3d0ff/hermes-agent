> **Purpose:** Builds the project or feature. Creates atomic commits during the entire build process. Does not manage git remotes, PRs, or repo configuration.

### **Guidelines:**
- Read `ponytail ultra` and  `caveman ultra` skills
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