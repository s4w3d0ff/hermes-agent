---
name: web-apps
description: Build single-file web apps (HTML/JS/CSS) that plug into existing projects — OpenCV.js, data viz, tuners, dashboards.
version: 1.1.0
author: Centaur
platforms: [linux, macos, windows]
---

# Web Apps

Build self-contained single-file HTML apps that load external libraries and work standalone. No build step, no bundler, no npm. Just an HTML file served from a local server.

## When to Use

- Tuners/visual editors for existing pipeline parameters
- Dashboard or monitoring view for a project's data
- One-off internal tools (no user-facing, no auth)
- Visual comparison tools (side-by-side before/after)

## Pattern: Single HTML File + Local Server

```
project/
  app/
    index.html          # Everything in one file
```

Serve with Python:
```bash
cd project/app && python -m http.server 8090
```

Open `http://localhost:8090/`

## Key Pattern: Async External Library Loading

When loading libraries that initialize asynchronously via `<script src>`, the global symbol may exist but not be ready. There are two patterns depending on the library's API.

### Pattern 1: Poll for Symbol Readiness

For libraries where you can detect readiness by checking a property:

```html
<script src="https://example.com/library.js"></script>
<script>
function waitForLibrary() {
  if (typeof Library !== "undefined" && Library.ready) {
    initApp();
  } else {
    setTimeout(waitForLibrary, 100);
  }
}

function initApp() {
  var lib = new Library();
  // ... rest of setup
}
</script>
```

### Pattern 2: Module Callback (OpenCV.js / Emscripten)

Libraries built with Emscripten/WASM expose a `Module` object. Configure callbacks BEFORE loading the script:

```html
<script src="library.js"></script>
<script>
// MUST be defined before <script src="..."> loads
var Module = {
  onRuntimeInitialized: function() {
    console.log("Library runtime ready");
    initApp();
  },
  onAbort: function(what) {
    console.error("Library abort:", what);
  },
  setStatus: function(text) {
    // Optional: show loading progress
  }
};

function initApp() {
  // Library globals like cv.* are fully available here
}
</script>
```

### Pattern for Lazy Module-Level Access

If you reference library properties at module scope (like `cv.THRESH_BINARY` in a constant object), defer with a getter:

```javascript
var cvCache = null;
function getCV() {
  if (!cvCache) {
    cvCache = {
      "THRESH_BINARY": cv.THRESH_BINARY || 0,
      // ... all library refs here
    };
  }
  return cvCache;
}
// Then use getCV()[key] instead of direct access
```

## Style Rules

- **No build step.** No webpack, vite, npm install. Inline everything.
- **CDN for external libs** only when no local copy exists. Pin version.
- **Dark theme default** for internal tools. `background: #1a1a2e; color: #e0e0e0`.
- **Grid layout** for side-by-side previews. `display: grid; grid-template-columns: repeat(auto-fill, minmax(420px, 1fr));`
- **CSS custom properties** for theming if needed beyond dark/light.

## Debugging Checklist

- Browser console is the primary debugger. Check `http://localhost:8090/` — no devtools panel available.
- Look for `ReferenceError` — usually means library not loaded yet (missing poll) or function name mismatch.
- Look for `TypeError` — usually means calling a method on an object that's still empty/undefined.
- **Async fetch timing in console**: `browser_console` reads happen immediately. If the page uses `fetch()` to load data, DOM state may not be populated yet when you read it. Wrap verification in a `setTimeout` or Promise: `new Promise(r => setTimeout(() => r(document.getElementById("x").value), 600))`.

## Pitfalls

- **Async script loading**: `<script src="...">` does NOT guarantee synchronous execution completion. Always poll for the global symbol.
- **Module-level references to library globals**: Constants initialized at parse time will fail if the library hasn't loaded. Use lazy getters.
- **File protocol CORS**: Opening `file://` instead of `http://localhost:8090/` breaks XHR/fetch and some CDN scripts. Always use a local server.
- **OpenCV.js memory**: Every `cv.Mat`, `cv.Size`, `cv.Scalar` created must be `.delete()`d. Leaks cause page crashes after many iterations.
- **OpenCV.js WASM hangs silently**: The docs.opencv.org build embeds WASM as base64 in the JS file. It downloads successfully (10MB+) but hangs during WASM instantiation with no console error — the loading spinner just never resolves. `var Module.onRuntimeInitialized` also gets overwritten by OpenCV.js itself since it does `var Module = typeof cv !== "undefined" ? cv : {}`. **Fix**: Use a Flask/FastAPI backend to run real Python preprocessing instead of OpenCV.js in-browser. Serve base64-encoded PNGs via JSON API. This is the recommended pattern for image processing tuners.
- **Module object gets overwritten by OpenCV.js**: Even if you define `var Module = {...}` before `<script src>`, OpenCV.js re-declares it with `var Module = typeof cv !== "undefined" ? cv : {}`. Your callbacks are lost. If you must use OpenCV.js in-browser, fall back to polling `cv.Mat` readiness (Pattern 1), not module callbacks.
- **Async file loading + DOM element race condition**: When FileReader loads files asynchronously, DOM elements created inside the async callback won't exist when later code tries to query them. **Fix**: create all DOM panels synchronously BEFORE starting async reads. Then use a counter/guard — only call processing functions when `readsDone >= totalReads` AND all images have loaded (`img.naturalWidth > 0`). Never assume canvas elements exist just because you started reading files.
- **Server port conflicts leave stale processes**: Old HTTP servers keep running after code changes, serving outdated pages. Always check what's bound to the port before starting a new one (`netstat -ano | grep :PORT`), kill the old process (`taskkill //PID X //F` on Windows, `kill -9 PID` on Unix), then start fresh. If you see the right HTML content but wrong behavior, the old server is likely still running.
- **Flask `/` route needs explicit handler**: Flask's implicit static file serving does NOT handle `/` automatically. Define `@app.route("/")` explicitly with `send_from_directory()`. Setting `static_folder="."` or `None` alone won't create a root route.
- **Flask route order matters**: Routes must be registered before calling `app.run()`. If you modify routes after start, the server needs to restart — Flask does not hot-reload routes in production mode.
- **Flask `cv2.imread()` does not accept BytesIO on Windows**: On Windows, `cv2.imread()` requires a filesystem path and rejects `io.BytesIO` entirely with `Expected 'filename' to be a str or path-like object`. **Fix:** use `cv2.imdecode(np.frombuffer(data, np.uint8), mode)` instead. Always use `imdecode` for in-memory image loading on Windows.
- **THRESH_OTSU requires single-channel input**: `cv2.THRESH_BINARY | cv2.THRESH_OTSU` fails on 3-channel (CV_8UC3) images with error mentioning `src_type == CV_8UC1 || src_type == CV_16UC1`. When preprocessing pipeline allows disabling grayscale, ensure input to `apply_profile()` is already decoded as grayscale (`cv2.IMREAD_GRAYSCALE`).
- **Canvas `.toDataURL()` is on canvas element, not context**: Call `canvas.toDataURL()`, NOT `ctx.toDataURL()`. The 2D context object has no `.toDataURL()` method — only the canvas element does.
- **Flask base64 decode strips data URI prefix**: When receiving image data from browser as `"data:image/jpeg;base64,..."`, strip the prefix before decoding: `image_bytes.split(",", 1)[1]`. Passing raw data URL to `base64.b64decode()` raises an error.
- **Flask process stale-kill pattern (Windows)**: When you restart a Flask server on port 8091 and get connection refused, old processes may still be bound. They won't appear in Hermes `process(action='list')`. Use `netstat -ano | grep :PORT` to find PIDs, then `taskkill //PID X //F` to kill them before starting fresh.
- **Flask debug mode for hidden tracebacks**: When `/apply` returns 500 with no visible error and `debug=False`, restart with `debug=True` (or `app.run(debug=True)`) to see the actual Python traceback in server output. This is how you find `cv2.imread()` failures, type errors, etc.
- **Server-side segmentation over client-side cropping**: Do NOT use JavaScript canvas operations to crop header/footer regions from images for processing. Canvas-based crops produce unreliable results (wrong offsets, JPEG artifacts, empty-looking segments). Instead, send the full image once to a server endpoint that handles segmentation internally using the actual Python pipeline functions (e.g., `segment_card()` from preprocessing.py). The server should accept one image, segment it with real OpenCV/NumPy, apply the profile to each segment, and return all results in one response.
- **Orphaned code after large HTML patches**: When replacing a large block of JavaScript in index.html (e.g., replacing old multi-request processing with new single-request flow), the closing braces from the old code can be left orphaned if the patch boundary doesn't align perfectly. Always read the area around your patch and verify no leftover `}).catch(` or stray `}` remains. Check for syntax errors immediately after applying large patches.
- **Stale hardcoded PROFILES dict drifts from server**: The frontend must NEVER contain a local copy of profile values. It fetches them from the server API (`GET /profiles` for names, `GET /profile/<name>` for values). A stale `var PROFILES = {...}` in HTML will silently populate controls with wrong values — users see scale_factor=8 when the real profiles all use 4. **Fix**: delete the local dict entirely. Initialize `PROFILES={}`, load profile names from `/profiles`, and fetch each profile's params via `fetch("/profile/" + name)` before calling `buildControls(name)`. This applies on initial load AND on every profile change event.

## Pattern: Flask Backend + HTML Frontend (Recommended for Image Processing)

For image preprocessing tuners or any app that needs actual OpenCV/NumPy processing, skip OpenCV.js entirely. Use a minimal Flask server as the processing engine and keep the frontend as pure HTML/JS.

```
project/
  tuner/
    index.html          # Pure HTML/JS — reads sliders, sends images to /apply
    server.py           # Flask app that imports your actual pipeline
```

Frontend workflow:
1. User selects profile → read values from DOM
2. On slider change → `fetch("/apply", { body: JSON.stringify({ image: dataUrl, profile }) })`
3. Server runs `scanner/preprocessing.apply_profile()` with real Python → returns base64 PNG
4. Frontend draws result on `<canvas>`

Profile sync: NEVER keep a local copy of profile values in the frontend. Fetch from `GET /profile/<name>` on init and on every profile change. The server is the single source of truth.

Server skeleton (single-image endpoint):
```python
from flask import Flask, request, jsonify
import base64, cv2, numpy as np
app = Flask(__name__, static_folder=".")

@app.route("/apply", methods=["POST"])
def apply():
    data = request.json
    img_data = base64.b64decode(data["image"].split(",")[1])
    gray = cv2.imdecode(np.frombuffer(img_data, np.uint8), cv2.IMREAD_GRAYSCALE)
    result = apply_profile(gray, data["profile"])  # from scanner/preprocessing.py
    _, buf = cv2.imencode(".png", result)
    return jsonify({"image": "data:image/png;base64," + base64.b64encode(buf).decode()})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8091, debug=False)
```

Server pattern for multi-segment output (header+footer):
```python
@app.route("/process_card", methods=["POST"])
def process_card():
    """Accept full card image, segment header/footer, apply profile to each."""
    data = request.json
    img_data = base64.b64decode(data["image"].split(",")[1])
    nparr = np.frombuffer(img_data, np.uint8)
    
    # Decode as color for original display
    img_color = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    img_gray = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)
    
    # Segment using pipeline's own function
    header, footer = segment_card(img_gray)
    
    # Process each segment
    hdr_result = apply_profile(header.copy(), data["profile"])
    ftr_result = apply_profile(footer.copy(), data["profile"])
    
    return jsonify({
        "original": encode_png(img_color),
        "header": encode_png(hdr_result),
        "footer": encode_png(ftr_result),
    })
```

## Pattern: Profile Type Coercion

Frontend sends slider values as strings. Backend must coerce to Python types before passing to `apply_profile()`.

```python
def _coerce_profile(data):
    """Coerce JS string values to proper Python types."""
    p = {}
    for k, v in data.items():
        if k == "adaptive_threshold":
            if not v:
                p["adaptive_threshold"] = None
                continue
            at = {}
            for ak, av in v.items():
                if ak in ("block_size", "C"):
                    at[ak] = int(av)
                else:
                    at[ak] = av
            p["adaptive_threshold"] = at
        elif k == "scale_mode" or k == "threshold_mode":
            p[k] = str(v) if v else None
        elif k in ("grayscale", "invert"):
            p[k] = bool(v)
        elif k == "blur_kernel":
            p[k] = int(v)
        elif k == "threshold":
            p[k] = int(v) if v not in (None, "", -1) else -1
        elif k == "clahe_clip_limit":
            p[k] = float(v)
        elif k in ("gamma", "sharpen_strength"):
            p[k] = float(v)
        elif k in ("denoise_strength",):
            p[k] = int(v)
        elif k in ("border_pad_px",):
            p[k] = int(v)
        elif k == "scale_factor":
            p[k] = float(v)
        else:
            p[k] = v
    return p
```