# Flask 500 Debugging (Windows)

## Pattern: `/apply` or `/process_card` returns 500 in <50ms

Response arrives too fast for preprocessing to run → crash on import or route setup.

### Common causes

1. **Missing import** — endpoint calls a function not imported from module
   ```python
   # BROKEN: segment_card() called but never imported
   header, footer = segment_card(img_gray)
   
   # FIX: add to import line
   from scanner.preprocessing import apply_profile, segment_card, PROFILES as PY_PROFILES
   ```

2. **`cv2.imread()` on BytesIO** — fails silently on Windows
   ```python
   # BROKEN
   img = cv2.imread(BytesIO(data))  # → None
   
   # FIX: use imdecode + numpy
   nparr = np.frombuffer(data, np.uint8)
   img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
   ```

3. **`THRESH_OTSU` on 3-channel image** — grayscale slider disabled in frontend
   ```python
   # BROKEN: user disables grayscale via UI → OTSU fails on color image
   _, result = cv2.threshold(img, -1, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
   
   # FIX: force grayscale before thresholding
   img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
   ```

## Debug workflow

```bash
# 1. Kill zombies (check for MULTIPLE PIDs)
netstat -ano | grep ":809" | grep LISTEN
# → shows all PIDs on port 809x

# 2. Kill ALL of them
taskkill //PID <pid1> //F && taskkill //PID <pid2> //F

# 3. Verify port free
netstat -ano | grep ":809" | grep LISTEN || echo "FREE"

# 4. Start with debug=True to see tracebacks
sed -i 's/debug=False/debug=True/' server.py
python server.py &

# 5. Check terminal output for actual error
```

## Key principle

When Flask returns 500 in <100ms, it's not the pipeline — it's a setup/import/runtime crash. The preprocessing pipeline takes seconds. Sub-100ms errors are always import bugs, missing functions, or type mismatches on entry.