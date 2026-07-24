---
name: dev-server
description: "Manage development servers — start, stop, restart, verify lifecycle. Covers Flask, Express, FastAPI, and similar dev servers on Windows/Linux/macOS."
version: 1.0.0
metadata:
  hermes:
    tags: [development, server, lifecycle, flask, express, fastapi]
---

# Dev Server Management

Start, stop, restart, and verify development servers across frameworks and platforms.

## Windows Process Lifecycle (CRITICAL)

Windows PID reuse means `process(action='list')` is UNRELIABLE for checking if a port is free. The old process may have exited but its PID may still be associated with the port in netstat output.

### Correct restart workflow

1. **Check what's on the port:**
   ```bash
   netstat -ano | grep ":<PORT>" | grep LISTEN
   ```

2. **Kill ALL PIDs found** (not just the first one):
   ```bash
   taskkill //PID <pid1> //F && taskkill //PID <pid2> //F
   ```

3. **Verify port is truly free:**
   ```bash
   netstat -ano | grep ":<PORT>" | grep LISTEN || echo "PORT FREE"
   ```
   DO NOT proceed unless this step confirms the port is free. If output shows PIDs, kill them again and re-check.

4. **Start fresh server:**
   ```bash
   cd <project-dir> && python server.py &  # or node server.js &
   ```

5. **Verify new server responds:**
   ```bash
   curl -s http://localhost:<PORT>/health | head -c 200
   ```

### Never do this

- Starting a new server without confirming port is free
- Assuming `process(action='list')` returning empty means port is clear
- Killing only one PID when multiple are listening on the same port
- Using `&` in foreground terminal — use `terminal(background=true)` instead

## Linux/macOS Process Lifecycle

```bash
# Find PIDs on port
lsof -i :<PORT> -t

# Kill all
kill -9 $(lsof -i :<PORT> -t)

# Verify free
lsof -i :<PORT> || echo "FREE"

# Start fresh
cd <project-dir> && python server.py &
```

## Debug Mode for Error Visibility

Flask: `debug=True` shows tracebacks in terminal. FastAPI/Express: enable verbose logging with environment variables or CLI flags. Without debug mode, 500 errors return no details — always check the server terminal output or stderr.

## Common Patterns

### Health endpoint
Most frameworks have built-in health checks. For Flask without routes:
```python
@app.route("/health")
def health():
    return "ok"
```

### Graceful shutdown
Always kill by PID, not by name. Process names like `python` or `node` are ambiguous — they match interpreter processes, background jobs, and unrelated scripts. Always use `netstat` to find the specific PID on the port you care about.

## Related Skills

- **camofox-browser** — Use when testing dev servers from browser context