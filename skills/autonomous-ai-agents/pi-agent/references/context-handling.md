# pi context handling (verified from installed bundle)

## Local modification: caveman compaction extension
`~/.pi/agent/extensions/caveman-compaction.ts` hooks `session_before_compact` and replaces the default summary with a caveman-ultra style one (same section structure, ultra-terse lines). Applies to manual `/compact [instructions]` and auto-compaction. Uses the session's current model for the summary call; keeps pi's cumulative `<read-files>`/`<modified-files>` tracking via `details`; honors customInstructions; falls back to stock compaction on any failure or empty result. So on THIS machine, summaries are caveman-ultra by default even though the settings file has no compaction key.

## Auto-compaction
Defaults baked into pi: `{enabled: true, reserveTokens: 16384, keepRecentTokens: 20000}`. The user's `~/.pi/agent/settings.json` has no `compaction` key, so defaults apply.

Trigger (`shouldCompact`): context tokens > `contextWindow - reserveTokens`. Context tokens = real total from the last assistant API usage + chars/4 estimate for messages after that point (images count as ~4800 chars each). For qwen38 (245k window) this fires around ~228.6k tokens.

What happens:
- pi calls the active model to summarize the old portion into a structured checkpoint with fixed sections: Goal, Constraints & Preferences, Progress (Done / In Progress / Blocked), Key Decisions, Next Steps, Critical Context. The prompt requires preserving exact file paths, function names, and error messages.
- A list of read/modified files from that stretch is appended automatically.
- The most recent ~20k tokens are kept verbatim, cut at turn boundaries; if the cut must split a turn, the prefix gets its own mini-summary ("Turn Context (split turn)").
- In context, everything older becomes one `compactionSummary` message: "The conversation history before this point was compacted into the following summary: <summary>...</summary>".

Rolling updates: subsequent compactions use an UPDATE prompt that merges new messages into the existing summary (preserve prior info, move items In Progress -> Done) instead of summarizing from scratch. Summaries therefore accumulate across many compactions and degrade with each pass through a small model.

Overflow recovery: if a request still hits the context limit after normal checks (e.g., one giant tool output), pi performs an emergency compaction and retries once (`prepareOverflowCompaction`, single attempt per generation).

Persistence: compactions are stored as `compaction` entries in the session JSONL (summary, firstKeptEntryId, tokensBefore, read/modified file lists). Original messages stay on disk but are excluded from context past the cut point; `pi --continue` resumes with the compacted state.

## Manual controls and settings
- `/compact [instructions]` - force compaction now, optionally with custom emphasis instructions.
- `~/.pi/agent/settings.json` -> `compaction: {enabled, reserveTokens, keepRecentTokens}`; per-model overrides are supported (settings lookup checks model-specific values first).
- Auto-compaction can be toggled off entirely (`set_auto_compaction` in the RPC layer / `compaction.enabled`).

## Other context management (separate from compaction)
- Tool outputs are truncated at the source: ~51,200 byte cap on read/bash results with a pointer to the full output file on disk when truncated.
- Images are resized before entering context and count as ~4800 chars in token estimates.

## Observing it live
`pi-verbose` (wrapper around `pi --mode json`) labels compaction events under `[meta]`; interactive mode shows usage/cost in the footer. To audit what a session actually sent, read its JSONL under `~/.pi/agent/sessions/<cwd-slug>/`.
