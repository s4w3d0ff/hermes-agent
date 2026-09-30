---
name: pi-agent
description: "Use when configuring, extending, or debugging the pi agent."
category: autonomous-ai-agents
metadata:
  hermes:
    tags: [pi, agent-harness, context-management]
---
# pi agent (local installation)

`pi` is `@earendil-works/pi-coding-agent`, installed npm-global on this server; the user actively develops against it. CLI: `~/.local/bin/pi` symlinks to `~/.local/lib/node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js` (note: `~/.local/lib`, not `~/lib`).

## First move
Read `~/.pi/README.md` before answering pi questions or changing anything. It is the user-maintained setup doc (layout, web_browser extension, shared skills, system prompt customization, model config). If it is stale relative to what you find on disk, update it as part of your change.

## Config surfaces
- `~/.pi/agent/settings.json` - defaultProvider/defaultModel (`rvlab/qwen38`), thinking level, telemetry off, `skills: ["~/.hermes/skills"]`, optional `compaction` block (see references/context-handling.md)
- `~/.pi/agent/models.json` - providers; rvlab points at a keyless LAN OpenAI-compatible endpoint; qwen38 = 245k context / 32768 max out, reasoning on
- System prompt: `~/.pi/agent/SYSTEM.md` (replaces), `APPEND_SYSTEM.md` (appends); per-project `.pi/SYSTEM.md` wins over agent-dir; `AGENTS.md`/`CLAUDE.md` always loaded
- Extensions: `~/.pi/agent/extensions/*.ts`, auto-loaded via jiti (no build step). Existing: `web-browser.ts` (drives camofox on :9377), `caveman-compaction.ts` (replaces default compaction summary with caveman-ultra style; see references/context-handling.md), `caveman-prompt.ts` (hardcoded old->new table rewriting every default system prompt string + tool description to caveman ultra at runtime; full inventory in references/system-prompt.md)
- Skills: `~/.pi/agent/skills/` plus the shared Hermes skills dir; name+description are injected into the system prompt, bodies load on demand
- Sessions: `~/.pi/agent/sessions/<cwd-slug>/*.jsonl`; resume with `pi --continue`; every entry (messages, usage, compaction) is in the JSONL

## Investigating internals (verified technique)
dist is minified; real code lives in `dist/bundle/chunks/*.js` plus `index.js`/`cli.js`, one giant line per chunk. Line-based tools are useless there.
1. Grep symbol names across chunks to find the right file (`grep -rl 'shouldCompact' dist/bundle/chunks/`).
2. Extract function bodies with a Python string search: locate `'function <name>('` and slice ~2-3k chars around it; print several hits of a key symbol to disambiguate.
3. Key symbols for context handling: `DEFAULT_COMPACTION_SETTINGS`, `shouldCompact`, `prepareCompaction`, `findCutPoint`, `findValidCutPoints`, `compactWithRequest`, `generateSummaryWithRequest`, `serializeConversation`, `SUMMARIZATION_PROMPT`, `UPDATE_SUMMARIZATION_PROMPT`, `TURN_PREFIX_SUMMARIZATION_PROMPT`, `COMPACTION_SUMMARY_PREFIX`, `TOOL_RESULT_MAX_CHARS`, `isContextMessage`, `extractFileOperations`.
4. GOTCHA: the bundle contains two parallel symbol families (plain and `2`-suffixed); what is actually exported is the `2` family, aliased at the end of the chunk (`serializeConversation2 as serializeConversation`). A grep for `'function <name>('` can return 0 hits when only the suffixed form exists; check the export alias map before concluding a symbol is missing.

## Context handling (short version)
pi DOES auto-compact, on by default: when context exceeds `contextWindow - reserveTokens` (default 16384), it LLM-summarizes the old history into a structured checkpoint and keeps the most recent ~20k tokens verbatim. Full mechanics in references/context-handling.md.

## System prompt assembly (verified)
One flat list of named sections, all static by construction (no date/timestamp band). `buildSystemPromptSections` builds them; rendered as preamble raw + every other section wrapped `<name>...</name>`, joined with blank lines. Sections are diffed per turn (`diffSystemPromptSections`) so only changed sections re-send.
- Sections: preamble (SYSTEM.md, or the stock default identity), tools, rules, docs, skills, cwd, project_context (only if project context files exist), addendum (APPEND_SYSTEM.md)
- tools section = `- name: snippet` lines from each tool's `*SystemPromptContribution.snippet`; rules = bash rule + per-tool guidelines + extension promptGuidelines + always-appended "Be concise in your responses" / "Show file paths clearly when working with files"
- Tool *descriptions* are NOT in the system message; they ride in the provider payload's `tools` array. Rewriting only the system message misses them
- Full string inventory, hook signatures, and test recipe: references/system-prompt.md

Runtime rewrite without touching the bundle (verified): extension hooks, pure string logic, no LLM calls
- `context_with_system`: fires before every LLM call; event `{messages}` includes the system message; return `{messages}` to own the prompt. Mutate content/sections in place
- `before_provider_request`: deep-walk `event.payload` and mutate strings in place - this is where tool descriptions get rewritten
- User wants full character-level control: one extension file holding a hardcoded literal old->new pair table, no fuzzy matching, no LLM rewrites. Patching the minified bundle was rejected (regenerated by `pi update`, not user-editable)

## Extension API (verified)
- Factory: default export `(pi: ExtensionAPI) => void`. Events via `pi.on(name, async (event, ctx) => ...)`. Types in `<pkg>/dist/core/extensions/types.d.ts`; docs at `<pkg>/docs/extensions.md` and `examples/extensions/`
- LLM call from extension: `ctx.modelRegistry.complete(ctx.model, {messages}, {maxTokens, signal, cacheRetention:"none", sessionId})` (uuidv7 from @earendil-works/pi-ai)
- Compaction hook `session_before_compact`: event has preparation (messagesToSummarize, turnPrefixMessages, previousSummary, fileOps, tokensBefore, firstKeptEntryId), reason manual/threshold/overflow, customInstructions, signal. Return `{compaction:{summary, firstKeptEntryId, tokensBefore, usage?, details?}}` to replace the summary; return undefined to fall back to pi default
- GOTCHA: `preparation.fileOps.read/.edited/.written` are Sets, not arrays (`.filter` on them throws). Spread before filtering
- To keep pi's cumulative file tracking in a custom summary: set `details:{readFiles, modifiedFiles}` AND append `<read-files>`/`<modified-files>` blocks to the summary text yourself. Across MULTIPLE compactions you must also seed from the previous summary yourself (pi only re-seeds details when the prior entry is fromHook:false), which caveman-compaction.ts does via parseFileBlock; see references/context-handling.md
- GOTCHA: pi only re-ingests a previous compaction's `details.readFiles/modifiedFiles` when that entry has `fromHook:false` (`extractFileOperations`). Hook-produced entries are `fromHook:true`, so on the second and later compactions structured file lists do not carry over automatically; seed them yourself from the `<read-files>`/`<modified-files>` blocks in `preparation.previousSummary`.
- Test headlessly via RPC (`pi --mode rpc`, JSONL stdin/stdout): wait for `agent_settled`, then send `{"type":"compact","customInstructions?":...}`. Manual compact fails with "Nothing to compact (session too small)" under ~20k tokens, so build a big session first (e.g., have pi read 8 files of ~45KB). Local model is slow: run tests as background jobs, allow several minutes

## Pitfalls
- Do not guess pi behavior from other agents; verify against `~/.pi/README.md` or the bundle, because behavior is version-specific (`pi update` changes it).
- Compaction summaries are generated by whatever model is active (here: local qwen38 27B), so long-session memory quality depends on that small model.
- When reporting pi internals, cite the symbol/constant you verified in the bundle so the claim stays auditable after updates.
- Some default strings exist TWICE in the bundle (skills intro: main builder + rpc/print-mode copy; read/write descriptions: legacy createReadTool/createWriteTool + *Definition variants). Count occurrences before replacing and replace every copy, or the print-mode path leaks defaults.
- Template literals inside minified chunks hold REAL newline bytes inside backticks, not `\n` escapes (e.g. the skills intro starts with two literal newlines). Print repr() of the surrounding bytes before building exact-match replacements.
- When removing/replacing text at user request, do not leave explanatory comments noting what was removed - the replacement content just stands there; leftover "removed X" notes are unwanted.