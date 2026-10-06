---
name: modelctl
description: Add, load, switch, or verify models managed by modelctl.
metadata:
  hermes:
    tags: [linux-sysadmin, modelctl, gpu, llama-cpp]
---
## What you are driving

modelctl is a GPU model orchestrator. It loads/unloads/switches generative-AI
models and manages their VRAM budget. Run as root:
`sudo modelctl <status|list|load|unload|switch|check|pin|unpin>`.

Key paths (all under MODELCTL_HOME, default /models/modelctl):
- Binary: /usr/local/bin/modelctl (real code: $MODELCTL_HOME/modelctl.py)
- Registry: registry.yaml. YAML ONLY - there is no JSON format or fallback anymore.
  The single home for model parameters: llama models
  carry args{} + extra[]; torch servers carry flat knobs their server reads via
  config.entry(). configs/<id>.yaml is a supported fallback only (read when an
  entry has no args/extra); do not create one unless portability to a box
  without the merged registry is needed.
- Generated units: /etc/systemd/system/model-<id>.service (do not hand-edit)
- README (authoritative field docs): $MODELCTL_HOME/README.md
- Gateway: mc/servers/gateway.py on :8080, fronts every model and auto-loads by
  registry id; serves the dashboard at /dashboard (per-GPU cards, gpu.gpus[] in
  /api/state, per-model GPU column, history keys gpu<N>_util/mem/total).

## Repo layout

`modelctl.py` at root; package under `mc/`:
  mc/core/{paths,registry,deploy,config}.py   shared library
  mc/servers/{gateway,dashboard,<per-model servers>}.py
  mc/tools/verify_models.py                   fleet verifier
Every entry point bootstraps sys.path to MODELCTL_HOME from its depth; imports
use dotted paths. Registry command[] for python models points at
${MODELCTL_HOME}/mc/servers/<file>.py. EXCEPTION: the omnivoice server is
tts_omnivoice.py NOT omnivoice.py, because it does "from omnivoice import
OmniVoice" (k2-fsa pip pkg) and a file named omnivoice.py would self-shadow
the library import and crash at startup.

VENV POLICY: one shared venv by default; separate venv only on real dependency
conflict. All venvs live under `venvs/` at the project root (e.g. `venvs/venv`
from base.txt, `venvs/venv-paddle` from paddle.txt where PaddlePaddle's CUDA
runtime conflicts with PyTorch). install.sh builds into `$HOME_DIR/venvs/$v`
(VENV_REQ map); .gitignore covers the whole `venvs/` dir.

Architecture: the registry is read in exactly one place,
mc.core.registry.load_registry(path, strict), shared by modelctl.py, gateway,
and dashboard. Models bind 127.0.0.1 ONLY; the gateway (port 8080) is the
single LAN-facing service and also serves /dashboard. The gateway unit runs as
root so its modelctl auto-loads need no privilege config anywhere in the
stack. Generated model units run as mc.core.deploy.user(): MODELCTL_USER/MC_USER
env > owner of $MODELCTL_HOME > first login account (uid>=1000) > root;
zero-config on a fresh single-user box. No firewall rules are generated at all. install.sh is
idempotent, touches only venvs + the modelctl symlink + one unit file,
auto-detects GPU CUDA arch for the llama.cpp build; MODELS.md maps every
registry entry to its upstream weight source. Read-only modelctl commands work
non-root; load/unload/switch require root.

Gitignored (never versioned): live `registry.yaml`, the whole `venvs/` tree,
`*.bak*`, `__pycache__/`, and `logs/` (live tap request logs). Committed
template: `registry.example.yaml`. There is NO per-box config file (no
`deploy.json`); every box-specific value resolves from env at load, so nothing
box-specific is ever committed.
Pitfall: `git add -f <file>` SILENTLY stages nothing when an ancestor dir is
fully gitignored (rc=0, no error). Stage such files with
`git update-index --add --cacheinfo 100644,$(git hash-object -w <f>),<path>`.

## Runtime settings (no config file)

mc/core/deploy.py resolves every box-specific value from env at load and caches it in memory for the process lifetime; nothing is hardcoded or generated on disk.
- service user (unit `User=`): MODELCTL_USER / MC_USER, else owner of $MODELCTL_HOME, else first login account (uid>=1000), else root
- llama-server binary: MODELCTL_LLAMA_SERVER / MC_LLAMA_SERVER, else first llama-server on PATH
- dashboard control token: MODELCTL_TOKEN / MC_TOKEN, else EMPTY (every mutating /api/* action and log read is refused). On rvlab the gateway unit pins it via a systemd drop-in `Environment=` line; set it there to keep the dashboard usable.

## Workflow: add a new model

1. Get the weights. Match the quant the box already runs (e.g. Unsloth
   UD-Q4_K_M GGUFs). `hf download <repo> <file> --local-dir <dir>` verifies
   sha256. Confirm GGUF magic: `xxd -l 16 <file>` must start with `GGUF`.
   Download target lives under /models/<kind>/ (e.g. /models/llm/<Model>/).
2. Pick a FREE port. Gateway holds 8080; models occupy 808x. List taken ports
   first: `ss -tlnp | grep -oE ':[0-9]+$' | sort -u`. Do not guess.
3. Back up the registry before editing (`cp registry.yaml registry.yaml.bak`), and DELETE that backup once you have verified the edit (valid parse + resolved commands). Never leave .bak litter in the tree; git is the durable history.
   NOTE: `modelctl.load_registry()` takes NO strict kwarg (that is mc.core.registry's); modelctl.py wraps it.
4. Add the registry entry. Edit with Python json (not sed) so you do not break
   structure or ownership. Required fields: kind, description, path, port,
   vram_mib (estimate; auto-calibrated on first real load), ram_gib,
   load_seconds, limits{memory_high,cpu_quota}, enabled:true. Optional:
   workdir, env{}, gpu_index, action_path (torch servers), no_calibrate,
   args{} + extra[] (llama models: the launch flags; see step 5), flat knobs
   for torch servers (task/conf/iou, device/threshold, ...), pinned (set by
   `modelctl pin`), command[] (NON-LLAMA servers only). NEVER store health_url
   (derived from port: http://127.0.0.1:<port>/health) or a per-model `user`
   (units run as mc.core.deploy.user()).
5. Put every model parameter in the REGISTRY ENTRY (single home). llama models:
   `args{}` (every server flag verbatim: ctx, offload, threads, parallel, ALL
   sampling params, spec flags, reasoning budget) + optional `extra[]`
   (value-less flags / extra files); modelctl launches:
   llama-server --model <path> --host 127.0.0.1 --port <registry port> + args
   + extra. Torch servers: flat knobs their server reads.
6. Verify WITHOUT touching the GPU (all safe, no changes):
   - `python3 -c "import yaml; yaml.safe_load(open('registry.yaml'))"` (valid YAML)
   - Print the exact launch command modelctl will build (no start): the
     `_resolve_command` one-liner in Pitfalls below
   - `sudo modelctl list`  (new id appears, state `-`)
   - `sudo modelctl check <id>`  (dry-run space check. It reports NOT-FIT while
     the current LLM occupies the card; expected and correct.)
   - Gateway sees it: `curl -s http://127.0.0.1:8080/v1/models` includes the id.
7. Hand the user the switch command for a terminal that is not this session:
   `sudo modelctl switch <id>`.
8. Leave the tree clean before calling it done: delete every temp file, backup, and test artifact you created (untracked-but-harmless litter is NOT acceptable). The repo should look like only the intended change exists.

## Code style (user rule)

Project .py files carry NO comments and NO docstrings, including shebangs
kept only where the file is executed directly. When editing or generating
code for this project, write it comment-free; do not restore removed ones.

## Pitfalls

- **For llama-server models the REGISTRY ENTRY's args/extra IS the launch
  command.** _resolve_command prefers the entry's `args{}` + `extra[]` and
  builds: llama-server --model <path> --host 127.0.0.1 --port <registry port>
  + every args entry + extra (non-flag extras resolved via models_path). A
  configs/<id>.yaml with a `model:` key is only consulted when the entry has no
  args/extra; if neither exists it falls through to command[], so an entry with
  none of these launches nothing. Non-llama (torch) servers run their registry
  command[] verbatim; their knobs live as flat keys in the entry and are read
  via config.entry(). Confirm what will launch without touching the GPU:
  `python3 -c "import sys; sys.path.insert(0,'<MODELCTL_HOME>'); import modelctl; r=modelctl.load_registry(); print(' '.join(modelctl._resolve_command('<id>', r['models']['<id>'])))"`
  To verify the WHOLE fleet at once, loop:
  `for mid, e in r["models"].items(): print(mid, " ".join(modelctl._resolve_command(mid, e)))`
- **The registry file must parse before anything else works.** Every modelctl
  command, the gateway, and the dashboard load it at startup; one stray
  character from a half-finished hand-edit breaks all of them. After ANY manual
  registry edit (yours or the user's), validate first:
  `python3 -c "import yaml; yaml.safe_load(open('registry.yaml'))"`.
- **Quote YAML-1.1-ambiguous string values in the registry (`on`, `off`,
  `yes`, `no`, `true`, `false`).** PyYAML's safe_load reads a bare `on` as
  boolean True, so an unquoted `-fa: on` becomes `-fa true` (flash-attn off)
  and the unit drifts. Always write these values quoted (`-fa: 'on'`).
  modelctl.py's save_registry force-quotes such strings via a ruamel str
  representer, so its own saves no longer corrupt them; but hand-edits and any
  other writer still must quote them.
- **The gateway caches the registry in-process at startup.** Converting or
  renaming the registry file does NOT reach a running mc-gateway: it keeps
  pointing at the old path and serves an EMPTY fleet (`/v1/models` returns
  `data: []`) while every model service stays up. After any registry-file
  rename/conversion, restart it: `sudo systemctl restart mc-gateway.service`
  (cheap; models stay loaded), then confirm `/v1/models` lists the fleet.
- **The user hand-edits registry/configs mid-refactor and leaves intermediate
  states.** When asked to "do the same for all models", diff live files against
  git HEAD (and `.bak*`) first to see exactly what changed, then complete the
  pattern fleet-wide rather than re-deriving it from scratch. Preserve their
  exact values: fix only what breaks validity (e.g. an args block that makes
  registry.yaml unparseable becomes `args{}` + sibling `extra[]`), never
  reconstruct content from your own assumptions.
- **Consolidation tasks: merge, prove, then delete.** When asked to fold
  redundant config files into a surviving file, first move EVERY key/value
  from each redundant file into the survivor and assert programmatically that
  every one landed with its exact value; make consumers read from the survivor
  and verify they work with the old files absent (hide them, re-run); only then
  delete. Deleting before proving absorption is how data gets lost.
- **`--spec-type draft-mtp` only works if the GGUF EMBEDS the MTP head
  (nextn.* tensors).** Not every Qwen GGUF carries it. Before copying spec
  flags from another model, inspect the tensor list and grep for `nextn`: zero
  nextn tensors means OMIT every `--spec-type`/`--spec-*` flag. (The C++
  `llama-gguf r <file> n` aborts on an assert here; use the python `gguf`
  reader: `from gguf import GGUFReader; r = GGUFReader(path);
  any(n.startswith("nextn") for n in (t.name for t in r.tensors))`.)
- **MoE "A3B" models are fast but need ALL weights resident in VRAM.** A
  35B-A3B Q4_K_M GGUF is ~22 GB; a 32 GB card cannot co-run two such LLMs.
  Active-params is a speed story, not a memory story.
- **`vram_mib` is an estimate.** modelctl recalibrates it from the real VRAM
  delta on first successful load. Seed it from file size + a comparable model
  and do not obsess over exactness.
- **A colliding port breaks the health check silently.** The unit waits until
  load timeout then stops. Always confirm the port is free before picking it.
- **Preserve registry.yaml ownership.** modelctl's save_registry chowns the
  file back to the original owner, but if you edit it as root outside
  modelctl, chown it back to the user or it becomes unwritable later.
- **Gateway venv runs Starlette 1.6: an ASGI middleware that buffers the
  request must PARK on later `receive()` calls, never answer with an immediate
  `http.disconnect`.** In this version `StreamingResponse.__call__` (ASGI spec
  <2.4 path) runs the body stream and a `listen_for_disconnect(receive)` task
  in one cancelling task group; answering that listener's second receive() with
  a disconnect cancels the whole response before any body chunk is sent, so the
  client gets an empty 200 (uvicorn logs "ASGI callable returned without
  completing response"). The tap middleware (`tap_mw.py`) serves the buffered
  request once then awaits a never-set `asyncio.Event` until cancelled. Also:
  return the async receive *function*, not a coroutine object.
- **Tap logging is on by default** (gateway middleware, per-model NDJSON under
  `$MODELCTL_HOME/logs/<model>/`, daily gzip archive + prune). Dashboard API:
  `/dashboard/api/logs[/{mid}/files|tail|search]` and `POST /api/logs/sweep`.
  Config: `logs/tap.json` or `MC_TAP_ENABLED=0` to disable. It is streaming-
  safe (forwards chunks as they arrive); only request bodies are buffered.
- **Tap log only records COMPLETED requests** (`dur_ms` = total wall time).
  An in-flight generation is invisible until it lands or errors. Absence of a
  new tap entry + GPU at 0% means the request never completed, not that no
  request was sent. Use this to distinguish "still generating" (GPU ~100%, no
  new entry yet) from "hung" (GPU 0%, no new entry).
- **llama-server can deadlock mid-generation** (observed with MTP speculative
  decoding on very long contexts). The process stays resident in VRAM but the
  HTTP handler thread blocks forever: GPU drops to 0%, `/v1/models` and
  `/health` time out, no new tap entry ever lands. Fix:
  `sudo systemctl restart model-<id>.service` (default TimeoutStopSec=90s,
  SIGTERM then SIGKILL frees VRAM even when the process is wedged). Clients
  that detect TCP drop auto-retry; clients with no read-timeout hang until the
  connection is killed. After restart, expect ~2 min of `503 Loading model`
  while weights reload before requests succeed again.
- **Memory-pressure swap thrash (second "GPU at 0%" mode).** Distinct from the
  CUDA deadlock above: the process is in `D` state with WCHAN=
  `folio_wait_bit_common` (uninterruptible disk I/O wait), not a blocked futex.
  Sustained ~200 MB/s reads from the model's storage device (`iostat -d -x`)
  show the kernel re-faulting evicted pages back in. Root cause: system RAM is
  nearly full with the model's RSS + KV cache for large contexts, and swap was
  too small to absorb the overflow without immediate re-eviction. Fix: grow the
  swapfile so evicted pages have room to stay put.
- **Gateway header-wait window is `MC_UPSTREAM_CONNECT_TIMEOUT + 30`, not the
  read timeout.** The streaming path wraps `client.send()` (waiting for response
  HEADERS) in `asyncio.wait_for(..., UPSTREAM_CONNECT_TIMEOUT + 30)`; default =
  60s. llama.cpp sends no bytes until prefill finishes, so any model whose prompt
  prefill exceeds the window gets a 502 "upstream timeout" (tap log shows exact
  ~60.04s durations). For long-context models raise it via drop-in
  `/etc/systemd/system/mc-gateway.service.d/timeout.conf` with
  `Environment="MC_UPSTREAM_CONNECT_TIMEOUT=..."` (+ daemon-reload + restart
  mc-gateway; model stays loaded). rvlab currently runs 3600 for both CONNECT and
  READ (worst-case qwen38 prefill ~29 min at full 262k ctx).
- **The gateway (`mc-gateway.service`) can wedge independently of the model.**
  llama-server on :8081 still answers while the front door on :8080 times out
  entirely. Diagnosis signature: `systemctl status mc-gateway` shows active,
  but every thread is `S` with WCHAN=`0` (blocked on a futex), near-zero CPU
  delta over minutes, and `ss -tnp | grep 8080` shows a pile of CLOSE-WAIT
  sockets the process never reaped. The proxy uses a shared `httpx.AsyncClient`
  with connect/read timeouts plus a total streaming deadline (env:
  MC_UPSTREAM_CONNECT_TIMEOUT=30, MC_UPSTREAM_READ_TIMEOUT=600,
  MC_UPSTREAM_TOTAL_DEADLINE=3600) and aborts upstream on client disconnect.
  If the wedge signature recurs it is a NEW bug; restart still clears it
  (`sudo systemctl restart mc-gateway.service`, cheap: model stays loaded).
  Verify with a fast `/dashboard/api/state` response before declaring it fixed.
- **Fix root causes on this stack; do NOT paper over with watchdogs/auto-
  restarts.** When a component wedges, propose and apply the underlying fix:
  timeouts + client-disconnect detection in the gateway proxy, right-sized
  RAM/swap so memory pressure cannot recur, an up-to-date llama.cpp that does
  not deadlock. A systemd `WatchdogSec` or auto-restart only delays detection
  of the same bug eating in-flight work; the user explicitly rejects band-aids
  ("fix the gushing wound, don't slap a bandaid on it"). Reserve restarts for
  clearing an active wedge, not as the fix.
- **Never shrink model config to "fix" memory pressure.** The user wants full
  native context and parallel >= 2 kept; llama.cpp pre-allocates each slot's
  FULL n_ctx KV cache at startup, which may exceed system RAM by design - that
  is FINE as long as swap absorbs the overflow without thrashing. If memory
  pressure reappears, size RAM/swap to fit the reservation; do not propose
  cutting `-c` or `--parallel`.
- **Moving a venv dir breaks console-script shebangs.** `python3 -m venv`
  bakes an ABSOLUTE interpreter path into every bin/<script> first line, and
  they may point at ancient pre-move homes that no longer exist. After moving:
  rewrite each bin/* shebang to the new absolute path (pyvenv.cfg home= and
  _virtualenv.pth are relative and fine), then prove with `<new>/bin/python -c
  "import <key pkg>"` per venv before touching consumers.
- **Venv move checklist (every consumer must point at the new root):** live
  registry.yaml command[] paths, every live systemd unit that runs a venv
  python followed by `systemctl daemon-reload`, install.sh build dir + its
  gateway unit template, .gitignore, registry.example.json tokens, README,
  requirements headers. Prove end-to-end by loading a torch server and
  confirming it serves from the new path (its traceback site-packages line
  shows the home).
- **Working over SSH:** do not inline multi-line Python through `ssh host
  'python3 - <<EOF'`: nested quotes/brackets get mangled by the shell layers.
  Write the script locally, then `scp it host:/tmp/x.py && ssh host 'python3
  /tmp/x.py'`.
- **modelctl.py MUST keep its python3 shebang.** `/usr/local/bin/modelctl` is a symlink to it, so without `#!/usr/bin/env python3` on line 1 the CLI (and the gateway's `subprocess.run(["modelctl", "load", ...])` auto-load) fail with Exec format error. If you rewrite modelctl.py, keep that first line.

## Quick dry-run (no GPU change)

    python3 -c "import sys; sys.path.insert(0,'<MODELCTL_HOME>'); import modelctl; r=modelctl.load_registry(); print(' '.join(modelctl._resolve_command('<id>', r['models']['<id>'])))"
    sudo modelctl list
    sudo modelctl check <id>

These prove the model is registered, its launch command is correct, and it is
wired into the space checker, without loading anything or risking the session.
