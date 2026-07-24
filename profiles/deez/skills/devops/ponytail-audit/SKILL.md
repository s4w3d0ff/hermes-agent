---
name: ponytail-audit
description: >
  Whole-repo audit for over-engineering. Like ponytail-review, but scans the
  entire codebase instead of a diff: a ranked list of what to delete, simplify,
  or replace with stdlib/native equivalents. Use when the user says "audit this
  codebase", "audit for over-engineering", "what can I delete from this repo",
  "find bloat", "ponytail-audit", or "/ponytail-audit". One-shot report, does
  not apply fixes.
  related_skills: [ponytail, ponytail-review]
---

ponytail-review, repo-wide. Scan the whole tree instead of a diff. Rank
findings biggest cut first.

## Tags

Same as ponytail-review:

- `delete:` dead code, unused flexibility, speculative feature. Replacement: nothing.
- `stdlib:` hand-rolled thing the standard library ships. Name the function.
- `native:` dependency or code doing what the platform already does. Name the feature.
- `yagni:` abstraction with one implementation, config nobody sets, layer with one caller.
- `shrink:` same logic, fewer lines. Show the shorter form.

## Hunt

Deps the stdlib or platform already ships, single-implementation interfaces,
factories with one product, wrappers that only delegate, files exporting one
thing, dead flags and config, hand-rolled stdlib.

## Output

One line per finding, ranked: `<tag> <what to cut>. <replacement>. [path]`.
End with `net: -<N> lines, -<M> deps possible.` Nothing to cut: `Lean already. Ship.`

## Boundaries

Scope: over-engineering and complexity only. Correctness bugs, security holes,
and performance are explicitly out of scope. Route them to a normal review
pass. Lists findings, applies nothing. One-shot.
"stop ponytail-audit" or "normal mode" to revert.

## Pitfalls

### DO NOT Suggest Runtime-Breaking Changes Blindly

Before flagging anything for deletion or modification, verify it does not alter
correct runtime behavior. Common traps:
- `bare except` + `raise` — exception propagation is intentional, logger captures
  tracebacks but raise handles downstream error routing. deleting the raise changes
  behavior.
- Inline comments are already removed by prior commits — do not list them again.
  check git history before suggesting removals that were already done.
- f-string nesting with same quote type on outer/inner braces crashes at compile
  time. verify syntax compiles before proposing fixes.
- Always run `python3 -m py_compile <file>` after a proposed fix to confirm it
  does not introduce new errors. do not ship suggestions that fail compilation.

### Verify Before Flagging

If you flag a change, verify the current file state matches what you saw. Prior
commits may have already addressed your finding. Check `git log --oneline -10`
before listing removals that landed elsewhere.
