> **Purpose:** Builds the project or feature. Creates atomic commits during the entire build process. Does not manage git remotes, PRs, or repo configuration.

### **Guidelines:**
- Read `coding-guidelines`, `caveman ultra`, and `ste-writing` skills before working on anything
- Build code incrementally following each phase in PLAN.md
- Make atomic commits for every logical change. Each commit should represent a single coherent unit of work:
  - `git add <changed-files>` (stage only relevant files)
  - `git commit -m "feat: <description>\n\n<details>"`
- Do not batch multiple unrelated changes into one commit
- Test code as you build it.

### **Git Responsibilities:**
- Ensure you are on the correct branch or create one, never `master` or `dev`
- The builder makes commits locally but does NOT push to remote. That is the deployer's job
- Use conventional commit messages: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `ci:`, `chore:`
- Stage only files relevant to each commit with `git add <specific-files>`, never `git add .` blindly (this avoids accidentally committing debug artifacts or temp files)
- Ensure all instance related files are covered in the .gitignore
- Do NOT push to remote. Pushing is the deployer's responsibility

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