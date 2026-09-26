---
name: rvlab-model-management
description: Add, load, switch, or verify models on rvlab via modelctl.
metadata:
  hermes:
    tags: [linux-sysadmin, modelctl, gpu, llama-cpp, rvlab]
---
## What you are driving

modelctl is a GPU model orchestrator on rvlab (192.168.8.164, TWO cards: GPU0
= RTX 3060 12 GB, GPU1 = Tesla PG500-216 32 GB). It loads/unloads/switches
generative-AI models and manages their VRAM budget. Run as root:
`sudo modelctl <status|list|load|unload|switch|check|pin|unpin>`.

GPUs and index namespaces (verify before touching):
- Registry `gpu_index` uses NVIDIA-SMI order: 0 = 3060 12GB, 1 = Tesla 32GB.
  Global registry `gpu_index` (currently 1 = Tesla) is the default; a per-model
  `gpu_index` wins over the global one. Small models (ocr, yolo26,
  pp-doclayout, whisper, omnivoice) are pinned to the 3060 (index 0); the
  LLMs (qwen38, qwen36) to the Tesla (index 1).
- CUDA enumeration order (FastestFirst) is REVERSED on rvlab: CUDA device 0
  = Tesla, CUDA 1 = 3060. CUDA_VISIBLE_DEVICES in a model's registry env{}
  uses THIS order, so a Tesla-pinned model has gpu_index: 1 and
  CUDA_VISIBLE_DEVICES=0 (see qwen38). Do not "fix" one to match the other.
- Confirm: `nvidia-smi -L` (smi order) and
  `/models/modelctl/venv/bin/python -c 'import torch; [print(i, torch.cuda.get_device_name(i)) for i in range(torch.cuda.device_count())]'`
  (CUDA order).

Key paths:
- Binary: /usr/local/bin/modelctl (real code: /models/modelctl/modelctl.py)
- Registry: /models/modelctl/registry.json  (add/remove models here)
- Per-model launch config: /models/modelctl/configs/<id>.yaml
- Generated units: /etc/systemd/system/model-<id>.service  (do not hand-edit)
- README (authoritative field docs): /models/modelctl/README.md
- Gateway: /models/modelctl/mc/servers/gateway.py on :8080, fronts every
  model and auto-loads by registry id; serves the dashboard at /dashboard
  (mc/servers/dashboard.py, multi-GPU since Sep 2026: per-GPU cards,
  gpu.gpus[] in /api/state, per-model GPU column, history keys
  gpu<N>_util/mem/total).

NOTE: source lives at /models/modelctl (moved from /opt/modelctl in Sep 2026;
the old tree was deleted). All systemd units point at the new path.

## Git repo (prepped Sep 2026, NOT yet pushed)

Local git repo in `/models/modelctl` (origin = github.com:s4w3d0ff/modelctl,
deploy key at ~/.ssh/id_ed25519). REMOTE STATE: default branch is `master`
(= 5433507); stale pre-refactor `main` deleted. LOCAL WORK (Sep 2026, unpushed):
branch `feat/reproducible-config` = pushed tip; on top, branch
`feat/repo-cleanup` (PUSHED to origin Sep 2026): repo cleanup (5 commits:
python reorganized into a package, dead servers/venvs/comfyui removed, docs
rewritten) plus multi-GPU pin work in modelctl.py (all_gpus, model_gpu_index,
pin/unpin), qwen38 ctx 262144, the dashboard multi-GPU UI (commit a29317e),
the gateway request-logging tap (fed6b81: mc/servers/tap.py + tap_mw.py,
log API in dashboard.py, README section), and CLI multi-GPU awareness +
pin/unpin with qwen38 ctx 262144 (tip 86113c0). Pushed via
`GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=accept-new" git push origin
feat/repo-cleanup`; local and remote are in sync, working tree clean.

REPO LAYOUT (post-cleanup): `modelctl.py` at root; package under `mc/`. NO mc_/srv_
prefixes on modules (folder already says what it is):
  mc/core/{paths,registry,deploy,config}.py   shared library
  mc/servers/{gateway,dashboard,yolo26,whisper,pp_doclayout,tts_omnivoice}.py
  mc/tools/verify_models.py                   fleet verifier
Every entry point bootstraps sys.path to MODELCTL_HOME from its depth; imports use
dotted paths (from mc.core import config / from mc.core.paths import ...). Registry
command[] for python models points at ${MODELCTL_HOME}/mc/servers/<file>.py. EXCEPTION:
the omnivoice server is tts_omnivoice.py NOT omnivoice.py, because it does
"from omnivoice import OmniVoice" (k2-fsa pip pkg) and a file named omnivoice.py would
self-shadow the library import and crash at startup. The comfyui/ checkout + node pack
are GONE (removed with the image/audio servers).

VENV POLICY: one shared venv by default; separate venv only on real dependency
conflict. Fleet now has exactly TWO: `venv` (base.txt: gateway, dashboard,
yolo26, whisper, omnivoice) and `venv-paddle` (paddle.txt: pp-doclayout, because
PaddlePaddle's CUDA runtime conflicts with PyTorch). The old venv-acestep/-nemo/
-uocr/-comfy were deleted (~36 GB freed; 53G -> 17G total). install.sh VENV_REQ map
now lists only [venv]=base.txt and [venv-paddle]=paddle.txt. The code is
config-driven and box-agnostic: paths resolve from mc_paths (MODELCTL_HOME/
MODELS_ROOT + ${...} tokens) and per-box settings from mc_deploy (env vars or
gitignored deploy.json). No LAN scoping exists anymore.

Architecture (portable refactor, verified live): the registry is read in exactly
one place, mc_registry.load_registry(path, strict), shared by modelctl.py,
mc/servers/gateway.py, mc/servers/dashboard.py and the ComfyUI node pack. Models bind 127.0.0.1
ONLY; the gateway (port 8080) is the single LAN-facing service and also serves
the dashboard at /dashboard (mc-dashboard.service no longer exists). The
gateway unit runs as root so its modelctl auto-loads need no privilege config
anywhere in the stack. Generated model units run as mc_deploy.user():
MODELCTL_USER env > deploy.json "user" > first login account (uid>=1000) > root;
zero-config on a fresh single-user box. No firewall rules are generated at all.
install.sh is idempotent, touches only venvs + the modelctl symlink + one unit
file, auto-detects GPU CUDA arch for the llama.cpp build; MODELS.md maps every
registry entry to its upstream weight source. Read-only modelctl commands work
non-root; load/unload/switch require root.

Pushing: from rvlab use `GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=accept-new" git push origin <branch>` (deploy key, no token on box). Changing the
repo's DEFAULT branch or deleting it needs the GitHub API, which the deploy key
cannot do; run that from a machine with `gh` authed as s4w3d0ff:
`gh api -X PATCH repos/s4w3d0ff/modelctl -f default_branch=master`. Default is
now `master`; never recreate a `main` branch here.

Gitignored (never versioned): live `registry.json`, `deploy.json`, all
`venv*/`, `*.bak*`, `__pycache__/`, the whole `comfyui/` upstream checkout
(own `.git`), and `logs/` (live tap request logs). Committed templates:
`registry.example.json` (tokenized), `configs/*.yaml`. Only our node pack file
inside comfyui is tracked: `comfyui/custom_nodes/ComfyUI-modelctl/__init__.py`.

Pitfall: `git add -f <file>` SILENTLY stages nothing when an ancestor dir is
fully gitignored (rc=0, no error). Stage such files with
`git update-index --add --cacheinfo 100644,$(git hash-object -w <f>),<path>`.

## SELF-REFERENCE GATE (read first, every time)

This agent runs OFF the gateway. The LLM it runs on is a loaded registry model.
`modelctl switch <other-llm>` or `unload` of the currently-loaded LLM will
SEVER THIS SESSION (the agent loses its own inference backend).

Consequences for "add a model" requests:
- Registering a model (edit registry + config, dry-run verify) is SAFE and does
  not touch the GPU. Do this freely.
- Actually LOADING a model that needs the whole VRAM while the current LLM is
  resident requires switching off the current LLM, which ends this session.
  Do NOT `switch`/`unload` the current LLM unilaterally. Verify your own
  backend first, register the model, run the dry-run checks, then hand the user
  `sudo modelctl switch <id>` to run from another terminal (or get explicit
  approval to switch and note the session will drop).

Find out which LLM you are running on: `sudo modelctl list` (the LOADED row)
and/or `cat ~/.hermes/config.yaml` (base_url points at the :8080 gateway).

## Workflow: add a new model

1. Get the weights. Match the quant the box already runs (this box uses Unsloth
   UD-Q4_K_M GGUFs). `hf download <repo> <file> --local-dir <dir>` verifies
   sha256. Confirm GGUF magic: `xxd -l 16 <file>` must start with `GGUF`.
   Download target lives under /models/<kind>/ (e.g. /models/llm/<Model>/).
2. Pick a FREE port. Gateway holds 8080; models occupy 808x. List taken ports
   first: `ss -tlnp | grep -oE ':[0-9]+$' | sort -u`. Do not guess.
3. Back up the registry before editing:
   `cp /models/modelctl/registry.json /models/modelctl/registry.json.bak-$(date +%Y%m%d)`
4. Add the registry entry. Edit with Python json (not sed) so you do not break
   structure or ownership. Required fields: kind, description, path,
   command=[binary] (FALLBACK ONLY, see pitfall), port, health_url, vram_mib
   (estimate; auto-calibrated on first real load), ram_gib, load_seconds,
   limits{memory_high,cpu_quota}, enabled:true. Optional: workdir, env{},
   action_path, api_style, no_calibrate. Do NOT set a per-model `user`
   field; units run as mc_deploy.user() (first login user by default).
5. CREATE /models/modelctl/configs/<id>.yaml. This is what ACTUALLY launches a
   llama-server model. Copy an existing config field-for-field (e.g. qwen38.yaml)
   and change model_path, port, sampling, and spec flags. See
   references/modelctl-config-anatomy.md.
6. Verify WITHOUT touching the GPU (all safe, no changes):
   - `python3 -c "import json; json.load(open('/models/modelctl/registry.json'))"`
     (valid JSON)
   - Print the exact launch command modelctl will build (no start):
     `python3 <skill>/scripts/resolve_modelcmd.py <id>`  (see scripts/)
   - `sudo modelctl list`  (new id appears, state `-`)
   - `sudo modelctl check <id>`  (dry-run space check. It will report NOT-FIT
     while the current LLM occupies the card; that is expected and correct, not
     a bug.)
   - Gateway sees it: `curl -s http://127.0.0.1:8080/v1/models` includes the id.
7. Hand the user the switch command for a terminal that is not this session:
   `sudo modelctl switch <id>`.

## Pitfalls

- **The registry `command[]` is a FALLBACK, not the launch command, for
  llama-server models.** modelctl rebuilds the launch from
  configs/<id>.yaml: server_binary + `--model <model_path>` + every option that
  has a `flag:` + `extra_args`. A registry entry with a full command but no
  YAML launches with NO flags (bare binary) and will misbehave. Always create
  the YAML, then confirm with resolve_modelcmd.py. Non-llama-server models
  (torch servers) use the registry command verbatim and have no YAML.
- **`--spec-type draft-mtp` only works if the GGUF EMBEDS the MTP head
  (nextn.* tensors).** Not every Qwen GGUF carries it. Before copying spec
  flags from another model, inspect the tensor list and grep for `nextn`:
  zero nextn tensors means OMIT every `--spec-type`/`--spec-*` flag. See
  references/modelctl-config-anatomy.md for the exact inspection snippet.
  (The C++ `llama-gguf r <file> n` aborts on an assert here; use the python
  `gguf` reader instead.)
- **MoE "A3B" models are fast but need ALL weights resident in VRAM.** A
  35B-A3B Q4_K_M GGUF is ~22 GB; a 32 GB card cannot co-run two such LLMs.
  Active-params is a speed story, not a memory story.
- **`vram_mib` is an estimate.** modelctl recalibrates it from the real VRAM
  delta on first successful load. Seed it from file size + a comparable model
  and do not obsess over exactness.
- **A colliding port breaks the health check silently.** The unit waits until
  load timeout then stops. Always confirm the port is free before picking it.
- **Preserve registry.json ownership.** modelctl's save_registry chowns the
  file back to the original owner, but if you edit it as root outside
  modelctl, chown it back to the user or it becomes unwritable later.
- **Never put box-specific values in committed files.** The repo is prepped to
  be pushed private; every blob in history is scanned for s4w3d0ff / rvlab /
  192.168.* / enp4s0 before committing. registry.example.json must stay fully
  tokenized with no user/workdir/lan keys (those live in gitignored
deploy.json). If you regenerate it from the live registry, strip dead top-level
  lan_iface/lan_subnet keys first.
- **Gateway venv runs Starlette 1.6: an ASGI middleware that buffers the request
  must PARK on later `receive()` calls, never answer with an immediate
  `http.disconnect`.** In this version `StreamingResponse.__call__` (ASGI spec
  <2.4 path) runs the body stream and a `listen_for_disconnect(receive)` task in
  one cancelling task group; answering that listener's second receive() with a
  disconnect cancels the whole response before any body chunk is sent, so the
  client gets an empty 200 (uvicorn logs "ASGI callable returned without
  completing response"). The tap middleware (`tap_mw.py`) serves the buffered
  request once then awaits a never-set `asyncio.Event` until cancelled. Also:
  return the async receive *function*, not a coroutine object.
- **Tap logging is on by default** (gateway middleware, per-model NDJSON under
  `$MODELCTL_HOME/logs/<model>/`, daily gzip archive + prune). Dashboard API:
  `/dashboard/api/logs[/{mid}/files|tail|search]` and `POST /api/logs/sweep`.
  Config: `logs/tap.json` or `MC_TAP_ENABLED=0` to disable. It is streaming-
  safe (forwards chunks as they arrive); only request bodies are buffered.

## Quick dry-run (no GPU change)

    python3 <skill>/scripts/resolve_modelcmd.py <id>
    sudo modelctl list
    sudo modelctl check <id>

These prove the model is registered, its launch command is correct, and it is
wired into the space checker, without loading anything or risking the session.
