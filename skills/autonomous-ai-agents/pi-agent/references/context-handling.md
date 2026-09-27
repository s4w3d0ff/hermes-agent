# pi context handling (verified from installed bundle)

## Local modification: caveman compaction extension
`~/.pi/agent/extensions/caveman-compaction.ts` hooks `session_before_compact` and replaces the default summary with a caveman-ultra style one (same section structure, ultra-terse lines). Applies to manual `/compact [instructions]` and auto-compaction. Uses the session's current model for the summary call; honors customInstructions; falls back to stock compaction on any failure or empty result. So on THIS machine, summaries are caveman-ultra by default even though the settings file has no compaction key.

**Multi-compaction file tracking (fixed Sep 2026).** pi's `extractFileOperations` only re-seeds file lists from a previous compaction when that entry is NOT hook-produced (`fromHook:false`). Hook entries are always `fromHook:true`, so on the 2nd+ consecutive compaction the structured `details.readFiles/modifiedFiles` would silently drop everything read before the first cut. The extension now seeds its own lists: it parses the `<read-files>`/`<modified-files>` blocks out of `preparation.previousSummary` (`parseFileBlock`) and unions them with pi's current-stretch ops in `fileLists(fileOps, previousSummary)`. A file read earlier but edited later is promoted from readFiles to modifiedFiles. The prompt also tells the model NOT to emit its own `<read-files>`/`<modified-files>` blocks (the extension appends them), preventing duplicate/stale lists on update passes. Verified end-to-end: 3 consecutive hook compactions accumulate 8 -> 16 -> 24 read files in both the JSONL `details` and the actual LLM request body (confirmed via modelctl tap log).

**Context-hygiene v2 (Sep 2026).** Four additions so long sessions don't fill with stale, low-value data that never gets removed:
1. **Priority-based summarization input.** Instead of pi's `serializeConversation`, the extension re-serializes `convertToLlm(messagesToSummarize + turnPrefixMessages)` by recency/value: user messages kept in full (intent); assistant text recent=full / older=truncated to ~500 chars; **thinking/reasoning blocks only for the newest K (`KEEP_RECENT_THINKING=3`), older ones dropped entirely** (the assistant's own reply already summarizes that reasoning); tool calls recent=name(args) / older=name-only; tool results deduped by content hash so an identical repeat collapses to a one-line note. This is what makes "old thinking + repeated reads" stop consuming summary budget.
2. **Source-level read dedup (`tool_result` hook).** When the `read` tool returns text identical (sha256) to an earlier read of the same path in this session, the result is replaced AT THE SOURCE with `[duplicate read of <path>: identical to an earlier read in this session, no data change]` before it enters live context. This keeps repeated reads from ever bloating the window, independent of whether compaction runs. Verified: JSONL persisted these notes as the actual tool results.
3. **No summary-of-summary.** On repeat compactions the extension does NOT feed `preparation.previousSummary` back to the summarizer (pi already re-expands the previous retained-tail into `messagesToSummarize`, so the new summary is built from real messages: user prompts, assistant replies, most recent reasoning/tool calls). Stale facts fade out over passes instead of being re-summarized forever. Verified via modelctl tap log: round-2 prompt contained doc0-doc5 as real messages with NO `<previous-summary>` tag. (Structured file tracking still carries forward separately via details + the appended blocks.)
4. **Input-size guard.** Before calling the model, if the serialized conversation exceeds `INPUT_BUDGET_FRACTION` (0.6) of the model context window (~4 chars/token), OLDEST messages are dropped from the front until it fits. Prevents the summarization request itself from overflowing a local provider (which would crash the server and leave the session "uncompressable"). Dropping oldest-first is safe: those are exactly the stale, low-priority messages to forget.

Tunables at top of file: `MAX_SUMMARY_TOKENS=12000`, `KEEP_RECENT_THINKING=3`, `OLD_TEXT_MAX_CHARS=500`, `RECENT_WINDOW=12`, `TOOL_CALL_ARGS_MAX=400`, `TOOL_RESULT_MAX_CHARS=2000`, `INPUT_BUDGET_FRACTION=0.6`. Unit tests: `~/.hermes/cache/scratch/test-caveman-v2.js` (8 checks, jiti + pi-stub). Live RPC test: `test-v2-live.py`.

## Auto-compaction
Defaults baked into pi: `{enabled: true, reserveTokens: 16384, keepRecentTokens: 20000}`. The user's `~/.pi/agent/settings.json` has no `compaction` key, so defaults apply.

Trigger (`shouldCompact`): context tokens > `contextWindow - reserveTokens`. Context tokens = real total from the last assistant API usage + chars/4 estimate for messages after that point (images count as ~4800 chars each). For qwen38 (245k window) this fires around ~228.6k tokens.

What happens:
- pi calls the active model to summarize the old portion into a structured checkpoint with fixed sections: Goal, Constraints & Preferences, Progress (Done / In Progress / Blocked), Key Decisions, Next Steps, Critical Context. The prompt requires preserving exact file paths, function names, and error messages.
- A list of read/modified files from that stretch is appended automatically.
- The most recent ~20k tokens are kept verbatim, cut at turn boundaries; if the cut must split a turn, the prefix gets its own mini-summary ("Turn Context (split turn)").
- In context, everything older becomes one `compactionSummary` message: "The conversation history before this point was compacted into the following summary: <summary>...</summary>".

## Cut point selection (`findCutPoint`, `findValidCutPoints`)
Walks backward from the newest entry accumulating token estimates until it has kept `keepRecentTokens` (20k), then snaps forward to a valid cut point. Valid roles: user, assistant, bashExecution, custom, branchSummary, compactionSummary. `toolResult` is explicitly excluded, so pi never cuts between an assistant tool call and its result; the retained tail always contains complete call/result pairs.
- Cut lands on a **user message**: clean split; everything before it goes to summarization, from that user message on stays verbatim (recent user prompts survive untouched unless older than the keep window).
- Cut lands mid-turn (assistant/tool entry): "split turn". pi finds the turn start (`findTurnStartIndex`, nearest earlier user or bashExecution entry) and does TWO summaries: old history plus a prefix-only summary of this turn using `TURN_PREFIX_SUMMARIZATION_PROMPT`. Final summary = history + "---" + "**Turn Context (split turn):**" + prefixSummary.
- Assistant messages with stopReason error/aborted/deferred are dropped from context entirely (`isContextMessage`), never summarized.

## What the summarizer sees (`serializeConversation`)
Messages flatten to plain text, one block per message: user -> `[User]: <text>` (text blocks only; images dropped); assistant -> optional `[Assistant thinking]:`, then `[Assistant]: <text>`, then `[Assistant tool calls]: name(k=v, k2="v2"); ...` with arguments JSON-stringified (the summarizer sees every call and its full args); toolResult -> `[Tool result]: <first 2000 chars>` (`TOOL_RESULT_MAX_CHARS=2000`) with a truncation marker; bashExecution entries are pre-converted to user text ("Ran `cmd`" + output) so they appear as `[User]:`. Full tool outputs never enter the summary prompt, only the 2k-char sample.

## Summary request shape
One single user message: `<conversation>...</conversation>` plus, on repeat compactions, the previous summary in `<previous-summary>` tags with `UPDATE_SUMMARIZATION_PROMPT` (preserve/merge rules) instead of the initial `SUMMARIZATION_PROMPT`; custom `/compact instructions` are appended as "Additional focus". System prompt is `SUMMARIZATION_SYSTEM_PROMPT`. maxTokens = min(0.8 * reserveTokens, model.maxOut).

Rolling updates: subsequent compactions use an UPDATE prompt that merges new messages into the existing summary (preserve prior info, move items In Progress -> Done) instead of summarizing from scratch. The JSONL stores only `firstKeptEntryId` on the compaction entry; the retained tail is reconstructed by walking back to it (system entries skipped), and on the next compaction those retained messages are re-expanded as pseudo-entries so they get folded into the new summary rather than lost. Summaries therefore accumulate across many compactions and degrade with each pass through a small model.

## File list carry-over (`extractFileOperations`)
pi seeds file tracking from a previous compaction's `details.readFiles/modifiedFiles` ONLY when that entry has `fromHook:false`. Hook-produced entries are `fromHook:true`, so on the second and later compactions structured file lists do not carry over automatically; they survive only insofar as the summary text preserves them (pi feeds `<previous-summary>` back). A custom hook that wants bulletproof multi-compaction tracking must seed its own file lists from the previous summary's `<read-files>`/`<modified-files>` blocks.

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
