# SlideCraft Lite — Agent Context

## Purpose
Low-RAM fork of [slidecraft](../slidecraft) focused on **logo + watermark removal**
and the toolbar features actually used in the day-to-day editing flow. Designed
to run on 4 GB RAM laptops, cold-start < 2s, total install ~250 MB.

## What's KEPT vs full SlideCraft

| Feature | Lite | Notes |
|---|---|---|
| PDF upload (PyMuPDF) | yes | Primary path. No poppler. 2.5x scale. Page-range picker. |
| PPTX upload | yes | Requires LibreOffice (optional system dep). |
| Remove Logo | yes | OpenCV TELEA inpaint, full fidelity |
| Edstellar Text Remove | yes | 3-tier: PDF text cache → cross-slide pixel similarity → Tesseract |
| Detect and Remove watermark | yes | Corner similarity + PDF text + URL/email/domain regex + custom brand keywords |
| Folder batch | yes | Accepts both PPTX and PDF in the same run |
| Recent files | yes | localStorage, last 5 decks, "Recent" dropdown next to Upload |
| Before / After compare | yes | Draggable split slider, original from `_originals/` |
| OCR (optional) | yes | Tesseract via pytesseract — only fires when binary is installed |
| Apply / Save | yes | Identical to upstream |
| Undo / Redo | yes | Same history snapshot mechanism |
| Slide Duplicate / Delete | yes | Identical |
| PNG export, Print | yes | Identical |
| Export PPTX / PDF / PNG-zip | yes | Hard 10 MB cap, iterative re-render |
| Present mode | yes | Identical |
| Insert Image / Shape / Icon (QR) / Text | yes | Identical |
| Image filters | yes | Brightness / contrast / blur / grayscale / sepia / 6 presets |
| Templates / Version history / Notes / Comments | yes | All localStorage + JSON |
| Auto-save heartbeat | yes | Every 8 s when dirty → `/api/autosave` |
| `.slidecraft` portable archive | yes | export-portable / import-portable |

| Dropped from full build | Why |
|---|---|
| EasyOCR (torch ~2 GB) | Heaviest dep; replaced by optional Tesseract (~80 MB, ext binary) |
| rembg (onnx ~500 MB) | Background-removal rarely used; cut for footprint |
| MoviePy / video tab | ffmpeg dep; out of scope for slide editor |
| Audio narration | Not in toolbar |
| Google Slides export, OAuth, AI panel | Cloud features — keep local-only |
| Bulk endpoint | Per user request |
| pdf2image fallback | PyMuPDF covers all PDF cases |

## Stack
- Backend: Python 3.10+, Flask 3.x, python-pptx, Pillow, OpenCV-headless, PyMuPDF, qrcode, pytesseract
- Frontend: Vanilla JS, HTML/CSS — no framework, no build step
- PDF: PyMuPDF only (fitz)
- PPTX to PDF: LibreOffice (optional — only needed for PPTX upload + PDF export from PPTX source)
- OCR: Tesseract (optional — install separately; pytesseract is a wrapper)

## How to Run
```powershell
# Windows
run.bat                  # auto-creates .venv on first run
start.bat                # fast path (skips dep check if .venv exists)

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

## Edstellar Text Remove — 3-tier detector
For each slide the route tries, in order:

1. **PDF text-layer cache** (`pdf_text.json`) — instant, exact bbox. Only present for PDF uploads.
2. **Cross-slide pixel similarity** in the top-left zone — sample up to 8 slides, stack their TL crops as gray float32, per-pixel std-dev across slides; pixels with `std < 6` AND `mean < 180` (dark + identical-across-slides) are the wordmark. Morph-dilate strokes, take the bbox, confirm ink on the per-slide ROI. OCR-free, ~100 ms for a 15-slide deck. Catches PPTX decks where the wordmark is rasterized into every slide image.
3. **Tesseract OCR** on the TL crop — only when the binary is installed. The route returns `ocr_unavailable_slides: N` for slides that fell through all three tiers; the JS surfaces the install hint.

## PDF page-range
`POST /api/upload` accepts an optional `pages` form field (`'1-10,15,20-25'`). Threaded through `_render_pdf_to_images` AND `_extract_pdf_text_layer` so the cache aligns with the rendered subset.

## Quality contract
The lite build must produce byte-comparable output to the full build for the
kept features. The drops are footprint cuts, not quality cuts:
- Inpainting still uses `cv2.INPAINT_TELEA`
- PDF still rendered at 2.5x (240 DPI)
- Watermark detection still prefers tight text bboxes over wide corner strips
- Overlay baking still uses cross-platform font resolution + PIL ImageDraw

## Low-end PC budget
- Cold start < 2 s (no torch/onnx/ffmpeg imports)
- Cross-slide TL stack: 8 small crops as float32 ≈ 2 MB peak
- PDF render: ~7–10 MB pixmap per page (released between iterations)
- Default `MAX_PDF_PAGES=300` and `MAX_EXPORT_MB=10` cap any blow-up
- Tesseract binary is optional; running without it still gives PDF text + cross-slide pixel detection

## What to Avoid
- Never re-introduce easyocr, rembg, or moviepy at module scope
- Never reduce PDF render scale below 2.5x for "performance"
- Never raise the export cap above 10 MB without explicit user request
- Never use `request.json` — Flask 3.x raises 415. Use `request.get_json(force=True, silent=True)`
- Never use 2-digit slide padding
- Never re-pre-load Tesseract eagerly — `tesseract_available()` caches a one-time `get_tesseract_version()` probe

## Env Vars
| Var | Default | Notes |
|---|---|---|
| HOST | 127.0.0.1 | Set 0.0.0.0 for LAN |
| PORT | 5050 | |
| MAX_EXPORT_MB | 10 | Hard cap — every export iteratively re-rendered to fit |
| MAX_PDF_PAGES | 300 | Refuse larger PDFs (RAM safety) |
| MAX_UPLOAD_MB | 1024 | Per-request upload cap |
| WATERMARK_BRAND_KEYWORDS | `edstellar` | Comma-separated; merged with the per-request `extra_keywords` body field |

## Routes (71 total)
New since first push: `/api/ocr-status`, `/api/ocr/<num>`, `/api/ocr-all`, `/api/slide/<num>/original.jpg`. Folder accepts both PPTX and PDF. Detect-watermark accepts `extra_keywords`. Upload accepts `pages`.
