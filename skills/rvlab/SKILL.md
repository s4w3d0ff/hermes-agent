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
  field in API responses.

## Fleet layout (verify before touching)

Small models (paddleocr-vl/ocr, yolo26, pp-doclayout, whisper, omnivoice) are
pinned to the 3060 (gpu_index 0); the LLMs (qwen38 dense 27B, qwen36 MoE
A3B) run on the Tesla (gpu_index 1). Global registry gpu_index is 1. Confirm
live state with `nvidia-smi -L` and `sudo modelctl list`.

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
