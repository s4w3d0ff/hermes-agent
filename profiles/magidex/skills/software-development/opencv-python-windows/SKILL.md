---
name: opencv-python-windows
category: software-development
description: Server-side Python OpenCV on Windows via Flask. Avoids broken client-side OpenCV.js with Windows-specific quirks (imdecode, profile coercion, data URI stripping).
tags: [opencv, windows, flask, image-processing, python]
---

# opencv-python-windows

Server-side image processing using Python OpenCV on Windows, served via Flask or similar framework. Avoids client-side OpenCV.js entirely.

## When to use

- Building an image processing app where the frontend handles UI only
- OpenCV.js fails silently (async WASM overwrites `Module.onRuntimeInitialized` callbacks)
- Need deterministic pipeline matching existing Python preprocessing code

## Core pattern

1. Frontend: load images as base64 data URIs, POST to server via XHR/fetch
2. Server: decode → process with OpenCV → encode result → return base64 JSON
3. Pipeline: match `preprocessing.py` exactly — grayscale → invert → denoise → border pad → scale → CLAHE → gamma → sharpen → blur → threshold → adaptive fallback

## Critical Windows quirk

`cv2.imread()` does NOT accept BytesIO on Windows. Must use:

```python
nparr = np.frombuffer(img_data, np.uint8)
img_np = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
```

For color images: `cv2.IMREAD_COLOR`, then convert to grayscale with `cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)` when pipeline expects single-channel.

## Profile coercion

JS slider values come as strings from JSON. Coerce before passing to `apply_profile`:

- Booleans: `bool(v)` or `v == "true"`
- Integers: `int(v)` (block_size, C, threshold, denoise_strength, border_pad_px, blur_kernel)
- Floats: `float(v)` (clahe_clip_limit, gamma, sharpen_strength, scale_factor)
- Strings: keep as-is for scale_mode, threshold_mode

## Windows process management (CRITICAL)

Hermes `process(action='kill')` only kills Hermes-managed processes. Windows zombie Python servers remain listening on the port even after Hermes list is empty. Always follow this sequence:

1. Kill all managed processes: `process(action='list')` → kill each
2. Kill by PID: `taskkill //PID <pid> //F` for every PID from `netstat`
3. Verify clean: `netstat -ano | grep ":<port>" | grep LISTEN` — must return nothing
4. Only then start fresh server

Example full cycle:
```bash
# 1. Kill managed processes (if any)
process(action='list') → kill each session_id

# 2. Find and kill all PIDs on the port
netstat -ano | grep ":8091" | grep LISTEN
# kills all PIDs listed

# 3. Verify
netstat -ano | grep ":8091" | grep LISTEN || echo "PORT FREE"

# 4. Start fresh (one server only)
cd ~/.hermes/magidex/tuner && python.exe server.py
```

**Never start a new server while an older one is still running on the same port.** Multiple zombies cause stale cache, wrong code serving, and confusing errors. This is a first-class constraint — zero tolerance for process accumulation.

## Architecture pitfalls

1. **Never crop small image regions client-side** — canvas-to-dataURL with JPEG compression corrupts small footer/header slices. Send full card once, segment server-side.
2. **Segmentation is fixed** — `preprocessing.py` uses hardcoded 11.1% top / 89% bottom. Do not adjust these values.
3. **THRESH_OTSU requires single-channel input** — convert to grayscale before applying OTSU fallback.
4. **Debug mode for server errors** — Flask suppresses tracebacks with `debug=False`. Enable debug temporarily to see actual error messages, then disable for production.
5. **Missing imports cause silent 500s** — When adding endpoints that call functions from imported modules, forgetting the import causes immediate 500 errors. Always verify a new endpoint works with a minimal curl test before browser testing.

## Reference data URI stripping

Frontend sends `data:image/jpeg;base64,<encoded>`. Strip prefix before decoding:

```python
if "," in image_bytes:
    image_bytes = image_bytes.split(",", 1)[1]
img_data = base64.b64decode(image_bytes)
```

## Minimal Flask server structure

```python
from flask import Flask, jsonify, request, send_from_directory
import cv2, numpy as np, base64

app = Flask(__name__, static_folder=None)

@app.route("/")
def serve():
    return send_from_directory(".", "index.html")

@app.route("/apply", methods=["POST"])
def apply():
    data = request.json
    image_bytes = data["image"]
    if "," in image_bytes:
        image_bytes = image_bytes.split(",", 1)[1]
    
    img_data = base64.b64decode(image_bytes)
    nparr = np.frombuffer(img_data, np.uint8)
    img_np = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    
    result = apply_profile(img_np, data["profile"])  # your pipeline function
    
    _, buf = cv2.imencode(".png", result)
    encoded = base64.b64encode(buf).decode()
    return jsonify({"image": "data:image/png;base64," + encoded})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8091, debug=False)
```