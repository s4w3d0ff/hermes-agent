# Windows OpenCV Quirks

## cv2.imread() does not accept BytesIO on Windows

`cv2.imread()` requires a filesystem path. On Windows it rejects `io.BytesIO` objects entirely with:

```
cv2.error: OpenCV(4.13.0) :-1: error: (-5:Bad argument) in function 'imread'
> Expected 'filename' to be a str or path-like object
```

**Fix:** Use `cv2.imdecode()` with numpy:

```python
import cv2
import numpy as np
import io

# Wrong (fails on Windows):
img = cv2.imread(io.BytesIO(data), cv2.IMREAD_GRAYSCALE)

# Correct:
nparr = np.frombuffer(data, np.uint8)
img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)  # or cv2.IMREAD_COLOR
```

This is the ONLY way to load images from memory on Windows. Always use `imdecode` for in-memory image loading.

## THRESH_OTSU requires single-channel input

OpenCV's `cv2.THRESH_BINARY | cv2.THRESH_OTSU` only works on 1-channel (grayscale) images:

```
cv2.error: OpenCV(4.13.0) ... THRESH_OTSU mode: 'src_type == CV_8UC1 || src_type == CV_16UC1'
> where 'src_type' is 16 (CV_8UC3)
```

When the preprocessing pipeline allows disabling grayscale via sliders, ensure input to `apply_profile()` is already grayscale. In Flask servers, decode as grayscale directly:

```python
img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)  # not IMREAD_COLOR
```
