---
name: scheduled-job-operations
description: Enumerate and debug recurring Linux jobs (cron, timers).
platforms: [linux]
metadata:
  hermes:
    tags: [cron, scheduler, systemd-timers, automation, debugging, linux]
---

# Scheduled Job Operations

Recurring work on this class of host lives in FOUR schedulers; "what cron jobs are here" means all four. A job that exists in a crontab is not proof it runs - verify by execution evidence, never by entry existence alone.

## 1. Enumerate Every Scheduler

```bash
# User crontab (current user)
crontab -l

# System cron: /etc/crontab + drop-ins + run-parts payloads
cat /etc/crontab; ls -la /etc/cron.d/; cat /etc/cron.d/*
ls /etc/cron.hourly /etc/cron.daily /etc/cron.weekly /etc/cron.monthly

# systemd timers (system + user) - often where the real daily work lives
sudo systemctl list-timers --all --no-pager
systemctl --user list-timers --all --no-pager

# Hermes' own scheduler (separate from all of the above)
hermes cron list
```

Interpretation pitfalls:

-   On Ubuntu, `/etc/crontab` and `cron.d` entries that run `run-parts /etc/cron.daily|weekly|monthly` are usually gated on anacron being ABSENT (`test -x /usr/sbin/anacron || ...`). When anacron exists (default), those lines are no-ops; the actual daily/weekly/monthly work runs via `anacron.service` or a systemd timer. Report both layers so the user sees what actually executes.
-   `/etc/cron.hourly` is frequently empty even though its crontab entry fires every hour - that's normal, not a failure.
-   Inactive timers (no NEXT time) are stopped units; list them separately from active ones.

## 2. Verify a Job Actually Runs

A crontab/systemd entry proves the schedule exists, not that the job succeeds:

1.  **Execute it exactly as the scheduler will** - same user, same invocation path (direct executable path for cron, not `bash script.sh`, which masks missing +x). Confirm exit code AND a state change (new log line, new commit, new file).
2.  **Check the job's own log timestamps.** If expected runs are missing from the log while the crontab entry is present, the launches were failing silently - see §3.
3.  **Cross-reference scheduler journal entries:** `journalctl --since -48h | grep CRON` shows cron opening/closing a session and logging `(user) CMD (...)` even when the exec itself fails (e.g., Permission denied). Session-opened + closed with no job-side output = silent launch failure.
4.  For systemd timers: `systemctl list-timers` LAST-run times plus `journalctl -u <service>` for run outcomes.

## 3. Silent-Failure Modes and Root-Cause Fixes

Cron without a configured MTA **discards stdout/stderr** - broken jobs can fail every single run with zero visible trace. The classic modes:

| Symptom | Root cause | Fix at root (not workaround) |
|---|---|---|
| Launch logged in journal, nothing in job log, runs stopped after a reinstall/restore/migration | Script lost its execute bit; exec dies "Permission denied" before any output | `chmod +x <script>` AND - if the script lives in a git repo - commit the mode change so future restores stay executable (see below) |
| Same as above but it keeps recurring after every clone/restore | Repo stores the file at mode 100644; worktree restore reproduces non-executable | `git ls-files -s <script>` to confirm stored mode; local `chmod +x`, then commit - it lands as "mode change 100644 => 100755". Never fix this only in the working tree. |
| Job runs fine interactively, fails under cron with cryptic missing-binary errors | Cron's minimal PATH/env differs from login shell | Use absolute paths in crontab; export needed vars inside the job or in the crontab header |
| Script dies mid-way, no partial output visible | `set -euo pipefail` + discarded stderr | Run manually once to surface the failing line; add a trap/redirect of stderr into the job's own log file so future failures are self-documenting |

## 4. Creating Jobs (minimal, verifiable)

-   Prefer an existing scheduler over adding a new layer: user work → user crontab or `hermes cron`; distro maintenance → systemd timers/anacron. Don't stack duplicate mechanisms for the same job.
-   For anything where "it ran" must be provable later, make the job itself append timestamped lines to its own log file (cron will not keep output for you).
-   After creating or fixing a job: run it once manually as the scheduler would (§2), confirm exit 0 + state change + log line. Only then report success.

## Completion Standard

A scheduled-job task is complete when: every scheduler was enumerated (not just "crontab"), each claimed-running job has execution evidence (log line or journal entry at an expected timestamp), and any fix was verified by a manual run in the scheduler's exact invocation form. Report which jobs are stock-distro vs custom, and call out silent no-ops (anacron-gated run-parts, empty cron.hourly) so the user isn't miscounting active work.

### **Never use em-dashes anywhere**

Zero exceptions. Use `. `, `; `, `, ` or split into two sentences instead. Replace any occurrence with an alternative. Em-dash do not render properly in many text editors and applications, making source-code/documentation or output hard to read and should be avoided at all costs.