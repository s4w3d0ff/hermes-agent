> **Purpose:** Design, build and maintain the s4w3d0ff-elements project.

### **Guidelines:**
- Read `ponytail lite`, `caveman ultra`, and `coding-guidelines` skills
- Never chain bash commands in the terminal (`&&`, `||`, `;`). You will be blocked. Call one command at a time. 
- Build code incrementally following each phase in PLAN.md (if it exists)
- Make atomic commits for every logical change. Each commit should represent a single coherent unit of work:
  - `git add <changed-files>` (stage only relevant files)
  - `git commit -m "feat: <description>\n\n<details>"`
- Do not batch multiple unrelated changes into one commit
- Test code in small chunks as you build it.

### **Git Responsibilities:**

- Use conventional commit messages: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `ci:`, `chore:`
- Stage only files relevant to each commit with `git add <specific-files>`, never `git add .` blindly (this avoids accidentally committing debug artifacts or temp files)
- Never put debug or temp artifact files where they could get staged from `git add .` by accident, keep the main repository clean.
- Ensure all instance/env related files are covered in the .gitignore

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
| `&&`, `||`, `;` in terminal tool calls | Prone to errors and unintended outcomes | 

### Pre-commit Checklist:
- [ ] Code meets the goal and nothing more (YAGNI)
- [ ] No inline comments in Python or Typescript
- [ ] Standard libraries used where possible
- [ ] Commit message follows convention
- [ ] Branch name reflects scope
- [ ] One logical change per commit
- [ ] All phases from PLAN.md implemented (if exists)
- [ ] Verification steps executed and passing