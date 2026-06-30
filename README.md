# SlideCraft Lite

A low-RAM fork of SlideCraft focused on **logo removal**, **Edstellar text removal**,
and the toolbar features used in daily editing. Designed to run on 4 GB RAM
laptops with a ~250 MB install and < 2s cold start.

## What it does

- Upload **PDF** (PyMuPDF, no poppler) or **PPTX** (LibreOffice required)
- **Remove Logo** — OpenCV TELEA inpaint, pixel-perfect
- **Edstellar Text Remove** — instant via PDF text-layer cache
- **Detect & Remove watermark** — brand keywords + URL/email/domain + corner similarity
- Edit: Apply, Save, Undo, Redo, Duplicate, Delete
- Slide tools: Duplicate, PNG export, Print, Delete
- Export: PPTX / PDF / PNG-zip — **hard 10 MB cap**, iteratively re-rendered to fit
- Present mode (F5)
- Insert: image, shape, icon (QR), text overlays

## What was cut (and why)

| Cut | Reason |
|---|---|
| EasyOCR + torch (~2 GB) | Heaviest dep; image-only PPTX falls back to manual rect |
| rembg + onnx (~500 MB) | Background-removal rarely used |
| MoviePy + ffmpeg | Video tab out of scope for slide editor |
| Audio narration | Not in toolbar |
| Google Slides export, OAuth, AI panel | Cloud features cut to keep local-only |
| Bulk upload endpoint | Per user request |
| pdf2image fallback | PyMuPDF covers all cases |

## Quality contract

Lite is **byte-comparable to upstream** for kept features. The drops are
footprint cuts, not quality cuts:

- Inpainting: `cv2.INPAINT_TELEA` (unchanged)
- PDF render: 2.5× / 240 DPI (unchanged)
- Watermark dedup: prefers tight text bboxes over wide corner strips (unchanged)
- Overlay baking: cross-platform font resolution + PIL ImageDraw (unchanged)
- Export size: iterative re-render under 10 MB cap (unchanged)

## Run

```powershell
# Windows
run.bat
```

App at http://127.0.0.1:5050. For LAN access: `set HOST=0.0.0.0` before `run.bat`.

## Requirements

- Python 3.10+
- LibreOffice (only for PPTX upload + PDF export from PPTX source). PDF upload + every export work without it.

## Tests

```powershell
.venv\Scripts\python.exe -m pytest tests/ -ra
```

## License

MIT (inherited from upstream).
