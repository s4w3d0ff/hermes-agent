---
name: rvlab-model-management
description: Add, load, switch, or verify models on rvlab via modelctl.
metadata:
  hermes:
    tags: [linux-sysadmin, modelctl, gpu, llama-cpp, rvlab]
---
## What you are driving

modelctl is a single-GPU model orchestrator on rvlab (192.168.8.164, one 32 GB
Tesla card). It loads/unloads/switches generative-AI models and manages their
VRAM budget. Run as root: `sudo modelctl <status|list|load|unload|switch|check>`.

Key paths:
- Binary: /usr/local/bin/modelctl (real code: /models/modelctl/modelctl.py)
- Registry: /models/modelctl/registry.json  (add/remove models here)
- Per-model launch config: /models/modelctl/configs/<id>.yaml
- Generated units: /etc/systemd/system/model-<id>.service  (do not hand-edit)
- README (authoritative field docs): /models/modelctl/README.md
- Gateway: /models/modelctl/srv_gateway.py on :8080, fronts every model and
  auto-loads by registry id.

NOTE: source lives at /models/modelctl (moved from /opt/modelctl in Sep 2026;
the old tree was deleted). All systemd units point at the new path.

## Git repo (versioned since Sep 2026)

Code is versioned at `github.com/s4w3d0ff/modelctl` (PRIVATE). Local git repo
lives in `/models/modelctl`, branch `main`. Push works over SSH: the box's
`~/.ssh/id_ed25519` is registered as a repo deploy key (no token on the box).

What is NOT versioned (gitignored): live `registry.json` (calibrated sizes +
box-local paths), all `venv*/`, `*.bak*`, `__pycache__/`, and the whole
`comfyui/` upstream checkout (it has its own `.git`). The sanitized template
is `registry.example.json`. Only our node pack file inside comfyui is tracked:
`comfyui/custom_nodes/ComfyUI-modelctl/__init__.py`.

LAN scoping for generated units reads registry top-level keys `lan_subnet`
and `lan_iface` (set on this box to 192.168.8.0/24 / enp4s0); if unset, no
ufw scoping is emitted. Configs reference the generic binary path
`/usr/local/bin/llama-server`, which is a symlink to
/opt/llama.cpp/build/bin/llama-server.

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
   command=[binary] (FALLBACK ONLY, see pitfall), workdir, user, port,
   health_url, vram_mib (estimate; auto-calibrated on first real load),
   ram_gib, load_seconds, limits{memory_high,cpu_quota}, enabled:true.
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

## Quick dry-run (no GPU change)

    python3 <skill>/scripts/resolve_modelcmd.py <id>
    sudo modelctl list
    sudo modelctl check <id>

These prove the model is registered, its launch command is correct, and it is
wired into the space checker, without loading anything or risking the session.
