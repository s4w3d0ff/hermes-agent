---
name: para-wake
description: "Use when working on the para-wake wake-word project."
category: devops
metadata:
  hermes:
    tags: [para-wake, parallella, wake-word, sysadmin]
---
# para-wake operations

Always-on UDP wake-word detector on a Parallella (Zynq A9 + Epiphany). C daemon
`para_waked` ingests 16-bit PCM over UDP, runs an openWakeWord ONNX pipeline via
the in-repo `onnxmini` runtime, and POSTs captured utterances to the rvlab
gateway for Whisper transcription.

## Repo + branches
- Path: `/home/s4w3d0ff/Projects/para-wake`. Remote origin = github.com/s4w3d0ff/para-wake.
- Active work happens on `feat/mini-onnx` (the C ONNX runtime + daemon). `master`
  is scaffold-only. Work and push on the feature branch; never commit to master
  directly (user standing rule: default branch stays clean, all work on branches).

## Build / test / deploy (dev host)
- `make` builds `para_waked` + `tests/out/test_onnxmini` natively (x86 here).
- `make test` runs the C pipeline against checked-in onnxruntime refs in
  `tests/refs/`; passes when max_abs_diff < 1e-4. Regenerate refs with
  `make tests/refs/ref_<name>.txt` (needs a python venv with onnxruntime+numpy).
- Deploy + native-build on the board: `make BOARD=parallella1 board`
  (rsyncs tree, builds there). Board = parallella1 @ 192.168.8.165.

## Running para_waked for a test
- Env knobs: `PW_PORT` (9000), `PW_STATE_DIR` (events.jsonl + utterances/),
  `PW_GATEWAY`, `PW_THRESHOLD`, `PW_DEBUG=1` (per-datagram/chunk trace to stderr).
- Stream a clip in from the dev host:
  `python3 tools/sender.py tests/audio/test_keyword.wav --host <ip> --port 9000`
  (real-time pace; add `--speed N` to accelerate, `--loop`, `--mute`).
- A wake fires at score>=threshold for PWAKE_DEF_PATIENCE consecutive chunks;
  the session then captures pre-roll + trailing-silence and writes a WAV + one
  events.jsonl line. Verify by reading `$PW_STATE_DIR/events.jsonl`.

## Quirks that cost time (verify live, don't assume)
- `para_waked` IGNORES SIGTERM and SIGINT (`signal(..., SIG_IGN)` in main). A
  plain `kill <pid>` does nothing; you must `kill -9`. Stale daemons from earlier
  runs keep port 9000 bound and silently swallow your test stream. Always check
  `pgrep -x para_waked` before launching, and kill old ones with `-9`.
- Launching the daemon over SSH: a backgrounded `para_waked` (nohup/setsid) keeps
  the SSH channel open on these old OpenSSH servers, so the launch command hangs
  until timeout even though the daemon started fine. Treat that hang as expected;
  verify in a SEPARATE ssh call (`head -1 <log>`, `ss -ulpn | grep :9000`).
- The dev host has no system onnxruntime; use a venv for ref regeneration.

## Gateway transcription status (check, don't assume)
`para_waked` POSTs to `$PW_GATEWAY/v1/audio/transcriptions` (model=whisper). If the
rvlab gateway has no whisper model registered, this returns 404 and para_waked
handles it gracefully: WAV is kept, event logged with `http:404`, transcript null.
So an events.jsonl line with `http:404` is expected behavior, not a daemon bug. To
get real transcripts the gateway needs a whisper model loaded (see rvlab/modelctl).
