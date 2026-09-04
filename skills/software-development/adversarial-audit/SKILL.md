---
name: adversarial-audit
description: Instructions on how to conduct an adversarial code audit
version: 0.0.1
author: Hermes
platforms: [linux]
metadata:
  hermes:
    tags: [code review, audit, adversarial, auditor, review]
---

## Workflow

> REVIEW PREVIOUS AUDITS -> AUDIT CHUNK A -> UPDATE AUDIT_{N}.md -> AUDIT CHUNK B -> UPDATE AUDIT_{N}.md -> ... -> REVIEW AUDIT_{N}.md -> DONE

#### Incrementally build the AUDIT_{N}.md file across many small passes. Never construct the entire audit in one go.

1. Read RESEARCH.md if it exists, this is the researcher's output, loaded into your workspace.
2. Read any existing AUDIT_{N}.md files to understand prior findings and their resolution status.
3. Audit a focused area of the project (one directory, one concern, one file type).
4. Append findings to AUDIT_{N}.md, small chunks only.
5. Repeat steps 4-5 until all scopes are covered.
6. Before completing: read the full AUDIT_{N}.md, verify no outstanding prior issues were missed, then complete.

### Incremental Build Discipline (STRICT)

```
WRONG: audit -> update AUDIT_{N}.md -> done
CORRECT: audit -> update AUDIT_{N}.md -> continue auditing -> update AUDIT_{N}.md -> review AUDIT_{N}.md -> done
```

You MUST split your audit into multiple passes. Each pass covers one focused area, appends findings to the file, audits another area, and appends again. Only after every area has been covered do you perform the final review pass.

> This prevents lazy, superficial audits that rely on context window capacity rather than genuine thoroughness.

## Reading Prior Context

### RESEARCH.md

If present, read it first. It contains the researcher's findings, architecture decisions, known issues, third-party dependencies, and constraints. Cross-reference your code observations against what the researcher documented. Flag any discrepancies.

### Previous Audits (AUDIT_{N}.md)

Read every prior audit file in order. For each finding in a previous audit:

- Verify whether it was actually resolved by examining the current codebase state.
- If the issue no longer exists, note it as `RESOLVED` in your audit with a brief explanation of how you verified resolution.
- If the issue still exists (or was only partially fixed), re-list it as an active finding in your audit and explain why the prior fix was insufficient.

> Outstanding unresolved issues from previous audits MUST be carried forward into the current audit. You are responsible for ensuring nothing slips through the cracks between passes.

## Audit Scope

Examine the codebase thoroughly across all of the following dimensions:

### Dead / Orphaned Code

- Functions, classes, or modules that are defined but never imported or called anywhere in the project.
- Import statements pointing to missing or deleted files.
- Configuration keys or feature flags with no corresponding code path.
- Test files referencing non-existent source files.
- Git history: `git log --follow <file>` to confirm if a file was ever part of the codebase or if it was added as dead weight.

### Abstraction Hell

- Functions that exist solely to wrap another function with no or minimal added logic.
- Deep inheritance hierarchies (more than 3 levels) with minimal behavioral differentiation between subclasses.
- Factory patterns or dependency injection containers used for simple, stable objects.
- Interfaces defined but implemented by exactly one concrete class.
- Wrapper layers where direct calls would be clearer.

### Excessive Commenting and Docstrings

- Inline comments that restate what the code already says plainly.
- Module-level docstrings that merely repeat the filename or module purpose.
- TODO/FIXME/HACK comments that have persisted across multiple audit cycles without action.
- Docstrings describing parameters and return types that match the type hints exactly (redundant).
- Flag any comment block longer than 3 lines, it likely belongs in a separate design document.

### Missing Expected Features

- Compare against RESEARCH.md: does the codebase implement everything the researcher documented as required?
- Public APIs or CLI commands mentioned in documentation but absent from source.
- Configuration options listed in docs but with no corresponding parser or validation code.
- Error handling gaps: missing try/except, unhandled None values, silent failures.
- Input validation on public-facing functions and endpoints.

### Overall Codebase Structure

- File naming conventions: consistent? If not, which files break the pattern?
- Module boundaries: are related concerns co-located or scattered across unrelated directories?
- Circular imports or cross-dependencies between modules that should be independent.
- Entry points: is there a clear main/root module, or is it ambiguous where execution begins?
- Package layout: does it follow PEP 8 / project conventions (src layout, flat layout)?
- Test coverage alignment: are tests co-located with source files or segregated in an unlinked directory?

### Third-Party Dependency Vulnerabilities

- Identify all declared dependencies (requirements.txt, pyproject.toml, package.json, Cargo.toml, etc.).
- Check versions against known CVE databases (pypi.org, npmjs.com, crates.io advisory DB).
- Flag deprecated packages with active security advisories.
- Note transitive dependencies pulling in risky or unmaintained packages.
- Compare pinned vs. latest available version; flag when a major security patch is available but not upgraded.

### Configuration Gaps

- Missing `.env` templates or `config.example` files (credentials hardcoded, or no example config exists).
- Hardcoded credentials, API keys, tokens, or connection strings in source files.
- Development vs. production configuration indistinguishable (no environment-based config switching).
- Database connection strings with default passwords or localhost references committed to version control.

### Code Quality Signals

- Functions exceeding 50 lines: flag the file, function name, and line range.
- Files exceeding 350 lines: flag the file path.
- Cyclomatic complexity indicators: excessive nested conditionals, long switch/case chains.
- Magic numbers or strings used directly in logic without named constants.
- Inconsistent error handling patterns across modules (some raise, some return error codes, some log silently).

### Security Review

- SQL query construction via string concatenation instead of parameterized queries.
- Unvalidated user input reaching file system operations (path traversal risk).
- Exposed debug endpoints or verbose error messages in production code paths.
- Insecure deserialization (`pickle.loads`, `yaml.load` without SafeLoader, eval/exec on untrusted data).
- Missing rate limiting on publicly exposed endpoints.

## Finding Format

Every finding MUST follow this structure:

```markdown
## {Short Title} - [file.py:42, file2.py:69]
**Severity:** CRITICAL / HIGH / MEDIUM / LOW
**Scope:** {scope(s) this issue falls under}
**Evidence:** {specific, factual observation, exact code snippet, import chain, or structural fact}
{1-3 sentences explaining why this is a problem and what the impact would be. No speculation.}
```

### Severity Definitions

- **CRITICAL:** Exploitable security vulnerability, data loss risk, production-blocking bug.
- **HIGH:** Significant quality issue causing maintainability degradation or likely runtime failure under normal conditions.
- **MEDIUM:** Moderate issue that creates technical debt, violates conventions, or could cause problems at scale.
- **LOW:** Minor inconsistency, style deviation, or cleanup opportunity with minimal functional impact.

## Audit Report Structure

Every time an issue is found during the audit, append the AUDIT_{N}.md with your findings BEFORE continuing the audit.
The AUDIT_{N}.md file should be organized as follows:

```markdown
## {project name} Audit - {date} ({time})
## Audit Summary
{Brief overview of findings: total count by severity, key themes.}
## Unresolved Issues from Prior Audits
{Table or list of any prior findings that still exist in the current codebase, with brief status.}
## Findings:
### {Title} - [files/lines effected]
**Severity:** {level}
**Scope:** {scope}
**Evidence:** {evidence}
{short explanation}
[... more findings ...]
```

## Process Constraints

- **Read-only.** You never modify source files, configs, or project structure. You only write to AUDIT_{N}.md.
- **No speculation.** Every finding must have concrete evidence, a file path, line number, import graph, or code snippet. If you cannot verify it exists in the current codebase, do not include it.
- **No remediation suggestions beyond scope.** You identify problems and state their impact. Fixing them is not your job. However, noting severity implicitly communicates urgency.
- **One area per pass.** Each incremental write should cover exactly one audit dimension (e.g., dead code in module X, dependency review of requirements.txt). Do not mix areas within a single chunk.
- **Cite evidence precisely.** When referencing code, include file path and line number. When referencing imports, show the full import chain. When referencing configuration, quote the relevant section.
- **Audit files are append-only per pass.** Each pass appends to the existing file; it does not overwrite. The final review pass reads the complete file for coherence before completion.

## Before Completing

1. Read the full AUDIT_{N}.md in its entirety.
2. Verify every finding has: a severity level, a specific location, and concrete evidence.
3. Cross-check every prior audit finding, confirm each is either resolved (with proof) or carried forward.
4. Remove any findings that are speculative, lack evidence, or cannot be verified against the current codebase.
5. Ensure no two findings describe the same problem (deduplicate).

## Constraints

- No coding, no implementation, no refactoring, no file modification other than AUDIT_{N}.md.
- Do not modify files outside your workspace unless reading for the audit.
- Do not guess about vulnerabilities or missing features, only report what you can verify by inspecting actual source files.
- If a concern cannot be verified (e.g., a third-party dependency's internal code is not present), note it as `UNVERIFIABLE` with severity LOW and explain what would need to be checked externally.
- Depth over breadth within each pass, thoroughly audit one area before moving to the next.

### **Never use em-dashes anywhere**

Zero exceptions. Use `. `, `; `, `, ` or split into two sentences instead. Replace any occurrence with an alternative. Em-dash do not render properly in many text editors and applications, making source-code/documentation or output hard to read and should be avoided at all costs.