# SlideCraft Lite — Agent Context

## Purpose
Low-RAM fork of [slidecraft](../slidecraft) focused on **logo + watermark removal**
and the toolbar features actually used in the day-to-day editing flow. Designed
to run on 4 GB RAM laptops, cold-start < 2s, total install ~250 MB.

## What's KEPT vs full SlideCraft

| Feature | Lite | Notes |
|---|---|---|
| PDF upload (PyMuPDF) | yes | Primary path. No poppler. 2.5x scale. |
| PPTX upload | yes | Requires LibreOffice (optional system dep). |
| Remove Logo | yes | OpenCV TELEA inpaint, full fidelity |
| Edstellar Text Remove | yes | PDF text-layer path only (instant, accurate) |
| Detect and Remove watermark | yes | Corner similarity + PDF text + URL/email/domain regex |
| Apply / Save | yes | Identical to upstream |
| Undo / Redo | yes | Same history snapshot mechanism |
| Slide Duplicate / Delete | yes | Identical |
| PNG export, Print | yes | Identical |
| Export PPTX / PDF / PNG-zip | yes | Hard 10 MB cap, iterative re-render |
| Present mode | yes | Identical |
| Insert Image / Shape / Icon (QR) / Text | yes | Identical |

| Dropped from full build | Why |
|---|---|
| EasyOCR (torch ~2 GB) | Heaviest dep; image-only PPTX without PDF text falls back to manual rect |
| rembg (onnx ~500 MB) | Background-removal rarely used; cut for footprint |
| MoviePy / video tab | ffmpeg dep; out of scope for slide editor |
| Audio narration | Not in toolbar |
| Google Slides export, OAuth, AI panel | Cloud features — keep local-only |
| Bulk endpoint | Per user request |
| pdf2image fallback | PyMuPDF covers all PDF cases |

## Stack
- Backend: Python 3.10+, Flask 3.x, python-pptx, Pillow, OpenCV-headless, PyMuPDF, qrcode
- Frontend: Vanilla JS, HTML/CSS — no framework, no build step
- PDF: PyMuPDF only (fitz)
- PPTX to PDF: LibreOffice (optional — only needed for PPTX upload + PDF export from PPTX source)

## How to Run
```powershell
# Windows
run.bat                  # auto-creates .venv on first run

# Tests
.venv\Scripts\python.exe -m pytest tests/ -ra
```

Always use `.venv\Scripts\python.exe` — system Python lacks PyMuPDF.

## Slide Numbering
Always 3-digit zero-padded: `slide-001.jpg`, `f"slide-{n:03d}.jpg"`, JS `.padStart(3,'0')`.

## Export size cap
`MAX_EXPORT_MB=10` is the default and is the contract — every export must fit.
`_fit_export_under_cap()` iteratively re-renders at smaller (scale, quality) pairs
until size <= cap. Do not loosen this without updating docs in the same commit.

## Quality contract
The lite build must produce byte-comparable output to the full build for the
kept features. The drops are footprint cuts, not quality cuts:
- Inpainting still uses `cv2.INPAINT_TELEA`
- PDF still rendered at 2.5x (240 DPI)
- Watermark detection still prefers tight text bboxes over wide corner strips
- Overlay baking still uses cross-platform font resolution + PIL ImageDraw

## What to Avoid
- Never re-introduce easyocr, rembg, or moviepy at module scope
- Never reduce PDF render scale below 2.5x for "performance"
- Never raise the export cap above 10 MB without explicit user request
- Never use `request.json` — Flask 3.x raises 415. Use `request.get_json(force=True, silent=True)`
- Never use 2-digit slide padding

## Env Vars
| Var | Default | Notes |
|---|---|---|
| HOST | 127.0.0.1 | Set 0.0.0.0 for LAN |
| PORT | 5050 | |
| MAX_EXPORT_MB | 10 | Hard cap — every export iteratively re-rendered to fit |
| MAX_PDF_PAGES | 300 | Refuse larger PDFs (RAM safety) |
| MAX_UPLOAD_MB | 1024 | Per-request upload cap |
