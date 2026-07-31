---
name: markdown-cleanup
description: >- 
  Fix malformed markdown syntax without changing content.
platforms: [linux]
metadata:
  hermes:
    tags: [markdown, cleanup, formatting, patching]
---

# markdown-cleanup

Clean up malformed syntax in markdown files while preserving all original content. This applies to fixing broken code blocks, repairing table formatting, standardizing headers, and correcting punctuation issues — without rewriting or changing the meaning of any text.

## Rules

- ONLY modify markdown syntax (formatting, structure). Never change content, wording, or meaning.
- Use `patch` tool for all edits — never rewrite entire files.
- Fix one issue at a time with specific context to avoid affecting other similar patterns.

## Pitfalls

- NEVER use `replace_all=True` when patching files with many similar patterns (like curl commands, code blocks, or repeated structures). It matches ALL instances and overwrites them identically, destroying unique URLs, parameters, tokens, and content throughout the file.
  - Instead: read specific sections using offset/limit in read_file, then patch one at a time with unique surrounding context so only that line changes.

- When dealing with large files (100KB+), use `read_file` with `offset` and `limit` parameters to read specific sections. Do NOT call `read_file` repeatedly without these parameters — the system blocks after 10 identical calls to the same region.

- If terminal commands are blocked due to `&&` restrictions, try alternative approaches like using Python scripts or different command structures.

## Workflow

1. Read the file with offset/limit to see specific sections
2. Identify malformed patterns (broken code blocks, bad formatting)
3. Patch each issue individually with unique surrounding context
4. Verify changes don't affect other similar patterns
5. Continue until all issues are fixed

## Common Issues to Fix

- Malformed curl commands: `curl-XGET'url'` → `curl -X GET 'url' \`
- Broken code blocks: missing line breaks, improper escaping
- Table formatting issues
- Header level inconsistencies
- Spelling/grammar in documentation text (use ste-writing skill for this)
