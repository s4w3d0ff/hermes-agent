---
name: rvlab
description: "rvlab server (192.168.8.164): hardware, access, quirks."
metadata:
  hermes:
    tags: [linux-sysadmin, rvlab, gpu]
---
rvlab is a LAN GPU box running modelctl (see the `modelctl` skill for tool
knowledge). Facts about THIS machine only.

## Hardware and access

- IP 192.168.8.164, Ubuntu 24.04, user s4w3d0ff, SSH key auth (`ssh rvlab`
  alias in ~/.ssh/config). Rate-limited against SSH probing: batch commands,
do not hammer it.
- TWO GPUs (NVIDIA-SMI order): GPU0 = RTX 3060 12 GB, GPU1 = Tesla PG500-216
  32 GB. CUDA enumeration is REVERSED on this box (FastestFirst): CUDA device
  0 = Tesla, CUDA 1 = 3060. So a model pinned to the Tesla has registry
  gpu_index: 1 and env CUDA_VISIBLE_DEVICES=0; do not "fix" one to match the
  other.
- RAM 32 GB + /swapfile on ext4 root (currently 16 GB). To resize:
  `sudo swapoff /swapfile && sudo fallocate -l <SIZE> /swapfile && sudo mkswap
  /swapfile && sudo swapon /swapfile`; the fstab entry persists since the path
  is unchanged. Verify with `swapon --show` and `free -m | grep Swap`.
- llama.cpp lives at /opt/llama.cpp (git repo tracking ggml-org/llama.cpp);
  build dir `/opt/llama.cpp/build` holds a CMakeCache with all flags, and
  `/usr/local/bin/llama-server` is a SYMLINK into `build/bin/`, so rebuilding
  in place upgrades the live binary. To upgrade: `git fetch origin && git
  checkout -B <branch> origin/master`, then in build/: `cmake ..` (reuses
  cached flags) + `make llama-server -j16` (~8-10 min), restart the model
  service, verify with `llama-server --version` and the `system_fingerprint`
  field in API responses. The tree is kept current enough to support the
  clef decision-model architecture (LLM_ARCH_CLEF) and the /v1/systemone
  endpoint; if a new model arch fails to load with "unknown model
  architecture", upgrade llama.cpp first.

## Fleet layout (verify before touching)

Multi-model fleet, all on the two GPUs:
- qwen38: Qwen3.8-27B dense UD-Q4_K_M GGUF, Tesla (gpu_index 1), port 8081,
  PINNED. This is the primary LLM.
- swift15: Swift 1.5 Qwen3.8-27B GSQ-RCO IQ2_XS (ukisai hybrid attn),
  3060 (gpu_index 0), port 8082. Usually UNLOADED; load on demand.
- clef: Cloudflare clef-flash 9B decision model, bartowski Q4_K_M GGUF,
  3060 (gpu_index 0), port 8083, with the f16 mmproj for image input.
  It is a DECISION model: it serves /v1/systemone (typed decisions), not
  chat/completions. Reachable via gateway :8080/v1/systemone with
  {"model":"clef",...}. Weights under /models/llm/Cloudflare-clef-flash/.
Global registry gpu_index is 1 (Tesla default). Confirm live state with
`sudo modelctl list`. The 3060 holds swift15 and/or clef; the Tesla holds
qwen38.

## Git repo

Local git repo in /models/modelctl (origin = github.com:s4w3d0ff/modelctl,
deploy key at ~/.ssh/id_ed25519). Default branch is `master`; never recreate a
`main`. USER RULE: never change the default branch and never commit or push
directly onto it; all work happens on feature branches. Push from rvlab with
`GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=accept-new" git push origin <branch>`.
The user hand-edits the live tree between sessions, so check `git status
--short` and `git log origin/<branch>..HEAD` before assuming state.

## Inference backend dependency

This agent session may run ON a model served by rvlab. Check
~/.hermes/config.yaml base_url first: if it points at the rvlab gateway (8080),
then `modelctl switch <other-llm>` or `unload` of the currently-loaded LLM will
SEVER THIS SESSION (the agent loses its own inference backend). Consequences:
registering a model (edit registry, dry-run verify) is SAFE and does not touch
the GPU; do that freely. Actually loading a full-VRAM model while the current
LLM is resident requires switching it off, which ends this session. Do NOT
switch/unload the current LLM unilaterally; hand the user `sudo modelctl switch
<id>` for another terminal (or get explicit approval). Find what is loaded:
`sudo modelctl list` (the LOADED row).
