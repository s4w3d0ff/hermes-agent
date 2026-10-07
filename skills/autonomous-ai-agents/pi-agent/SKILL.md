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
- Extensions: `~/.pi/agent/extensions/*.ts`, auto-loaded via jiti (no build step). Existing: `web-browser.ts` (drives camofox on :9377), `caveman-compaction.ts` (replaces default compaction summary with caveman-ultra style; see references/context-handling.md), `wedged-recovery.ts` (activity watchdog: detects a busy-but-silent agent loop, escalates warn -> `ctx.abort()` -> `ctx.shutdown()`, plus `/unstuck [force]` command)
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
- Recovery primitives on ctx: `ctx.abort()` (end current operation), `ctx.isIdle()` (= not agent-run-active AND not compacting; false while a turn is in flight, including wedged ones), `ctx.shutdown()` (clean exit; session resumes via `pi --continue`). There is no out-of-band getContext() and no dispose/unload hook (factory returns void): capture `ctx` from any handler to use later (e.g. in timers), clear timers on `session_shutdown`, re-arm on `session_start`
- `/reload` tears down the old extension runner (`session_shutdown(reason:"reload")`) and re-runs discovery, so new/changed extension files load without a restart; it also fires `session_start(reason:"reload")`
- LLM call from extension: `ctx.modelRegistry.complete(ctx.model, {messages}, {maxTokens, signal, cacheRetention:"none", sessionId})` (uuidv7 from @earendil-works/pi-ai)
- Compaction hook `session_before_compact`: event has preparation (messagesToSummarize, turnPrefixMessages, previousSummary, fileOps, tokensBefore, firstKeptEntryId), reason manual/threshold/overflow, customInstructions, signal. Return `{compaction:{summary, firstKeptEntryId, tokensBefore, usage?, details?}}` to replace the summary; return undefined to fall back to pi default
- GOTCHA: `preparation.fileOps.read/.edited/.written` are Sets, not arrays (`.filter` on them throws). Spread before filtering
- To keep pi's cumulative file tracking in a custom summary: set `details:{readFiles, modifiedFiles}` AND append `<read-files>`/`<modified-files>` blocks to the summary text yourself. Across MULTIPLE compactions you must also seed from the previous summary yourself (pi only re-seeds details when the prior entry is fromHook:false), which caveman-compaction.ts does via parseFileBlock; see references/context-handling.md
- GOTCHA: pi only re-ingests a previous compaction's `details.readFiles/modifiedFiles` when that entry has `fromHook:false` (`extractFileOperations`). Hook-produced entries are `fromHook:true`, so on the second and later compactions structured file lists do not carry over automatically; seed them yourself from the `<read-files>`/`<modified-files>` blocks in `preparation.previousSummary`.
- Test headlessly via RPC (`pi --mode rpc`, JSONL stdin/stdout): wait for `agent_settled`, then send `{"type":"compact","customInstructions?":...}`. Manual compact fails with "Nothing to compact (session too small)" under ~20k tokens, so build a big session first (e.g., have pi read 8 files of ~45KB). Local model is slow: run tests as background jobs, allow several minutes

## Diagnosing a stuck / hung session (verified)
When pi appears frozen mid-turn (UI shows "compressing" or similar for many
minutes), cross-reference three signals to localize where it is blocked:
1. **Local process**: `ps -o pid,stat,time,%cpu,wchan:20 -p <pi-pid>`. A wedged
   pi sits in `Sl+` with WCHAN=`ep_poll` (blocked reading its socket) and near-
   zero CPU delta over a few seconds. It is NOT busy-looping.
2. **Local TCP**: `ss -tnp | grep <backend-ip>`. An ESTAB connection to the
   backend means pi is mid-request, waiting on the stream. No connection = idle
   (turn complete), not hung. The local port number changes when pi drops a dead
   stream and reconnects.
3. **Remote GPU util** (dashboard `/api/state` `gpu.gpus[]`, or nvidia-smi):
   - ~100% sustained = actively generating, just slow; wait it out.
   - 0% for minutes with no new completed request in the tap log = backend
     deadlocked mid-generation. pi is blocked on a stream that will never end.

The session JSONL only writes when a message/compaction COMPLETES, so a frozen
file mtime + open TCP conn + idle GPU = stuck, not "still thinking". A completed
compaction appears as a `type:"compaction"` entry with the summary text; its
presence is proof compaction finished.

**Fix for a deadlocked backend**: restart the model service (see
modelctl skill). pi detects the dropped TCP connection, opens a
fresh one, and retries the in-flight request once the backend reloads (~2 min of
`503 Loading model`). No local state is lost; the session resumes from where it
was. Do NOT kill or restart the pi process itself to clear a stuck turn.
4. **Long-prefill timeout cascade (distinct from deadlock)**: with big contexts
   (~140k+ tokens) the backend spends 8-15 min prefilling with ZERO output bytes,
   and three independent timeouts used to kill such requests:
   - gateway header-wait window = `MC_UPSTREAM_CONNECT_TIMEOUT + 30` (NOT the read
     timeout), default 60s -> fixed on rvlab via drop-in
     `/etc/systemd/system/mc-gateway.service.d/timeout.conf`
     (`MC_UPSTREAM_CONNECT_TIMEOUT=3600`, `MC_UPSTREAM_READ_TIMEOUT=3600`).
   - pi's per-request timeout derives from the `httpIdleTimeoutMs` setting
     (default 300s; also sets undici global headers/body idle timeouts). Set
     `"httpIdleTimeoutMs": 0` in `~/.pi/agent/settings.json` to disable it.
   - openai-node SDK default is 600s, but pi overrides via the setting above.
   Signature: tap log shows requests dying at exactly ~60.04s with status 502
   while GPU sits at 100% (healthy prefill, not deadlock).
5. **Settings are read at startup and on `/reload` only** - no file watcher.
   Edit `~/.pi/agent/settings.json`, then run `/reload` inside pi to apply live
   (re-reads settings, re-runs `configureHttpDispatcher`, rebuilds chat from the
   session JSONL; safe mid-session).
6. **Client-side wedge (no backend involvement)**: zero TCP sockets from pi (`ss -tnp | grep <pid>` empty) + zero child processes + frozen session mtime + healthy backend = the agent loop deadlocked locally at turn end (still busy, no provider request in flight, nothing to wake the event loop). Distinct from #2/#3: there is NO ESTAB connection and GPU is idle. Fix without losing state: load a watchdog extension via `/reload` (see `wedged-recovery.ts`) or kill pi + `pi --continue`; the JSONL holds everything through the last completed message.

## Pitfalls
- Do not guess pi behavior from other agents; verify against `~/.pi/README.md` or the bundle, because behavior is version-specific (`pi update` changes it).
- Compaction summaries are generated by whatever model is active (here: local qwen38 27B), so long-session memory quality depends on that small model.
- When reporting pi internals, cite the symbol/constant you verified in the bundle so the claim stays auditable after updates.
- Some default strings exist TWICE in the bundle (skills intro: main builder + rpc/print-mode copy; read/write descriptions: legacy createReadTool/createWriteTool + *Definition variants). Count occurrences before replacing and replace every copy, or the print-mode path leaks defaults.
- Template literals inside minified chunks hold REAL newline bytes inside backticks, not `\n` escapes (e.g. the skills intro starts with two literal newlines). Print repr() of the surrounding bytes before building exact-match replacements.
- When removing/replacing text at user request, do not leave explanatory comments noting what was removed - the replacement content just stands there; leftover "removed X" notes are unwanted.
- Unit-testing an extension via jiti: clear `/tmp/jiti` between runs (jiti caches compiled modules by path and silently serves stale code after edits), load from the INSTALLED path so tests match production, and pass `ctx` as the 2nd handler arg in your fake pi (`(event, ctx)`)
- Silence-based wedge detection needs separate windows per state: llama.cpp emits ZERO stream events during prefill (multi-minute at big contexts), so use a generous window when no token has arrived since the last provider request; suppress while any tool is in flight (long builds produce legitimate silence); prime `busy` from `ctx.isIdle()` on load to catch already-wedged sessions
- A CUSTOM compaction handler (`session_before_compact`, e.g. caveman-compaction.ts) makes a nested one-shot LLM call via `ctx.modelRegistry.complete(...)` that emits NO pi lifecycle events (it is not an assistant turn), so during it the agent looks perfectly silent while still busy. On a local model with a big context this runs for many minutes, and a fast wedge threshold will fire `ctx.abort()` mid-compaction - cancelling the summary AND killing the in-flight response (the aborted assistant message lands with EMPTY content; no `type:"compaction"` entry is written). Track compaction via `session_before_compact` / `session_compact` / `session_compact_failed` and give that window its own generous threshold

## Keeping pi's runtime self-contained (no hermes dependency)
pin: pi must run on its own install environment and rely on nothing under `~/.hermes/`.
- Layout: node at `/home/s4w3d0ff/.local/node/`; `~/.local/bin/{node,npm,npx}` are relative symlinks into it; npm prefix pinned to `~/.local` in `~/.npmrc`; pi package at `~/.local/lib/node_modules/@earendil-works/pi-coding-agent`. All independent of hermes.
- Repair when bin links dangle or node is missing: install Node LTS under `/home/s4w3d0ff/.local/node/` (tarball from `nodejs.org/dist/<v>/`, NOT scratch - it gets pruned), repoint the three bin links with relative targets, and pin `npm config set prefix /home/s4w3d0ff/.local` so future global installs stay coherent.
- `~/.local/bin/camofox-browser` was a sibling casualty: stale relative link into node_modules; its real self-contained install is `/home/s4w3d0ff/camofox-browser/`, bin link points at `bin/camofox-browser.js` there.
- `settings.json` has `skills: ["~/.hermes/skills"]` - that is an intentional content choice (shared skill library), not a runtime dependency. When scanning for hermes coupling, distinguish content references (fine) from install/runtime dependencies (must go).

## Replacing stock prompt sections via extension (verified)
- `before_agent_start` gives mutable `systemPromptOptions`; set `customPrompt` to replace the identity preamble and `sections[name]` to add/replace tagged sections. Section names must match `/^[a-z][a-z0-9_-]*$/`.
- GOTCHA: in `buildSystemPromptSections`, the standard `<tools>`, `<rules>` and `<docs>` sections are built ONLY in the no-custom-prompt branch. Setting `customPrompt` silently DROPS all three (confirmed absent from the recorded system message). To keep them, copy their inner text out of `event.systemPrompt` (the stock render available at handler time) with a `<name>...</name>` extractor and re-inject as explicit `sections[name]`. Copying pi's own output stays correct across `pi update`s; do not hardcode doc paths or duplicate `buildRules()`.
- Verify an extension end-to-end by reading the system message's `message.sections` dict from the session JSONL at `~/.pi/agent/sessions/<cwd-slug>/*.jsonl` (e.g. cwd `/tmp` -> slug `--tmp--`). It lists every section actually sent to the model, in order.
- Unit-test a `.ts` extension without a full pi run: load it with pi's own jiti (the bundled default export is a FACTORY exposing `.createJiti`; call `require("jiti")(cwd,{interopDefault:true,esmResolve:true})` to GET the require fn, then load the file - calling `require('jiti')(file)` directly throws `t.startsWith is not a function`; NODE_PATH pointed at pi's `node_modules`), call the factory with a fake `{on}` to capture the handler, feed it a realistic normalized-options object + a stock `systemPrompt` string, then render with pi's exact algorithm (preamble raw; every other section wrapped `<name>\n..\n</name>`; joined by blank lines) and assert.
- Node runtime: self-contained at `/home/s4w3d0ff/.local/node/` (LTS), npm prefix pinned to `~/.local`. If pi ever fails to launch, check the bin symlinks first - they were once dangling links into a deleted `~/.hermes/node/`; repair per "Keeping pi's runtime self-contained" below.