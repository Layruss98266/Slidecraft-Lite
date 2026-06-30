# SlideCraft Lite

A low-RAM fork of SlideCraft focused on **logo removal**, **Edstellar text
removal**, and the toolbar features used in daily editing. Designed to run on
4 GB RAM laptops with a ~250 MB install and < 2 s cold start.

## What it does

- Upload **PDF** (PyMuPDF, no poppler) or **PPTX** (LibreOffice required)
- **PDF page-range picker** on upload — render `1-10,20-25` instead of all 150 pages
- **Remove Logo** — OpenCV TELEA inpaint, pixel-perfect
- **Edstellar Text Remove** — 3-tier detector:
  1. PDF text-layer cache (instant, exact)
  2. Cross-slide pixel similarity (OCR-free, works on rasterized PPTX wordmarks)
  3. Tesseract OCR (optional — only when the binary is installed)
- **Detect & Remove watermark** — brand keywords + URL/email/domain regex + corner similarity + **custom brand-keyword input**
- **Folder batch** — process every PPTX *and* PDF in a local folder
- **Recent files** — last 5 decks in a dropdown next to Upload
- **Before / After compare** — draggable split slider against the pre-edit copy
- Edit: Apply, Save, Undo, Redo, Duplicate, Delete
- Slide tools: Duplicate, PNG export, Print, Delete
- Export: PPTX / PDF / PNG-zip — **hard 10 MB cap**, iteratively re-rendered to fit
- Present mode (F5)
- Insert: image, shape, icon (QR), text overlays
- Image filters, templates, version history, notes, comments, `.slidecraft` portable archive

## What was cut (and why)

| Cut | Reason |
|---|---|
| EasyOCR + torch (~2 GB) | Replaced with optional Tesseract + OCR-free cross-slide detection |
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
- PDF render: 2.5x / 240 DPI (unchanged)
- Watermark dedup: prefers tight text bboxes over wide corner strips (unchanged)
- Overlay baking: cross-platform font resolution + PIL ImageDraw (unchanged)
- Export size: iterative re-render under 10 MB cap (unchanged)

## Low-end PC budget

- Cold start < 2 s — no torch, onnx, ffmpeg, or poppler imports
- Cross-slide Edstellar detector: 8 small crops as float32 ≈ 2 MB peak
- PDF render: 7–10 MB pixmap per page, released between iterations
- `MAX_PDF_PAGES=300`, `MAX_EXPORT_MB=10` cap any blow-up
- Tesseract binary is optional; PDF text cache + cross-slide pixel detector run without it

## Run

```cmd
run.bat        :: first run — creates venv, installs ~250 MB
start.bat      :: subsequent runs — fast path, no dep re-check
```

App at http://127.0.0.1:5050. For LAN access: `set HOST=0.0.0.0` before `run.bat`.

## Requirements

- **Python 3.10+** (required)
- **LibreOffice** (optional) — only for PPTX upload + PDF export from PPTX source. PDF upload + every export work without it.
  - Windows: `winget install TheDocumentFoundation.LibreOffice`
  - Mac: `brew install --cask libreoffice`
  - Linux: `apt install libreoffice`
- **Tesseract OCR** (optional) — only for OCR on image-only PPTX. PDFs use the text-layer cache automatically.
  - Windows: `winget install UB-Mannheim.TesseractOCR`
  - Mac: `brew install tesseract`
  - Linux: `apt install tesseract-ocr`

## Tests

```cmd
.venv\Scripts\python.exe -m pytest tests/ -ra
```

## License

MIT (inherited from upstream).
