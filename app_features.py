"""
SlideCraft — additional feature routes.

Registered by app.py via register_feature_routes(app, ctx). Keeps the main
file lean while adding: master slide / theme, palette extraction, .slidecraft
portable zip, auto-save heartbeat (Lite build — no audio, no video, no rembg).
"""

import base64
import io
import json
import shutil
import uuid
import zipfile
from pathlib import Path
from flask import jsonify, request, send_file
from werkzeug.utils import secure_filename
from PIL import Image
from collections import Counter


def register_feature_routes(app, ctx):
    """ctx = dict of shared paths/helpers from app.py:
         BASE_DIR, SLIDES_DIR, ORIGINALS_DIR, DATA_FILE, UPLOAD_DIR,
         EXPORT_DIR, load_data, save_data, _get_slide_files,
         _safe_name, _data_lock, _set_deck_name, _get_deck_name,
         MAX_OVERLAY_IMG_BYTES
    """
    BASE_DIR     = ctx["BASE_DIR"]
    SLIDES_DIR   = ctx["SLIDES_DIR"]
    DATA_FILE    = ctx["DATA_FILE"]
    EXPORT_DIR   = ctx["EXPORT_DIR"]
    UPLOAD_DIR   = ctx["UPLOAD_DIR"]
    load_data    = ctx["load_data"]
    save_data    = ctx["save_data"]
    get_slides   = ctx["_get_slide_files"]
    safe_name    = ctx["_safe_name"]
    data_lock    = ctx["_data_lock"]

    THEMES_DIR  = BASE_DIR / "themes_saved"
    THEMES_DIR.mkdir(exist_ok=True)
    MASTER_FILE = BASE_DIR / "master_slide.json"

    # ─── Speaker notes (dedicated GET/POST so the notes pane is self-contained)
    @app.route("/api/notes/<int:num>", methods=["GET"])
    def get_notes(num):
        data = load_data()
        return jsonify({"notes": data.get(str(num), {}).get("notes", "")})

    @app.route("/api/notes/<int:num>", methods=["POST"])
    def set_notes(num):
        payload = request.get_json(silent=True) or {}
        text = payload.get("notes", "")
        if not isinstance(text, str):
            return jsonify({"error": "notes must be a string"}), 400
        with data_lock:
            data = json.loads(DATA_FILE.read_text()) if DATA_FILE.exists() else {}
            entry = data.get(str(num), {"overlays": [], "notes": ""})
            entry["notes"] = text[:20000]
            data[str(num)] = entry
            DATA_FILE.write_text(json.dumps(data, indent=2))
        return jsonify({"ok": True})

    @app.route("/api/notes/all", methods=["GET"])
    def get_all_notes():
        data = load_data()
        return jsonify({str(k): v.get("notes", "") for k, v in data.items()})

    # ─── Master slide / theme: header/footer text + brand colors applied to all
    @app.route("/api/master", methods=["GET"])
    def get_master():
        if MASTER_FILE.exists():
            try:
                return jsonify(json.loads(MASTER_FILE.read_text()))
            except json.JSONDecodeError:
                pass
        return jsonify({
            "header": "", "footer": "", "showPageNumbers": False,
            "primaryColor": "#2563EB", "accentColor": "#A78BFA",
            "fontFamily": "Inter", "logoDataUrl": "",
        })

    @app.route("/api/master", methods=["POST"])
    def set_master():
        payload = request.get_json(silent=True) or {}
        clean = {
            "header":          str(payload.get("header", ""))[:200],
            "footer":          str(payload.get("footer", ""))[:200],
            "showPageNumbers": bool(payload.get("showPageNumbers", False)),
            "primaryColor":    str(payload.get("primaryColor", "#2563EB"))[:9],
            "accentColor":     str(payload.get("accentColor", "#A78BFA"))[:9],
            "fontFamily":      str(payload.get("fontFamily", "Inter"))[:64],
            "logoDataUrl":     str(payload.get("logoDataUrl", ""))[:2_000_000],
        }
        MASTER_FILE.write_text(json.dumps(clean, indent=2))
        return jsonify({"ok": True})

    # ─── Palette extraction: pull dominant colors from a slide
    @app.route("/api/palette/<int:num>", methods=["GET"])
    def palette(num):
        slides = get_slides()
        if num < 1 or num > len(slides):
            return jsonify({"error": "Invalid slide"}), 400
        try:
            img = Image.open(slides[num - 1]).convert("RGB")
            # Downsample for speed
            img.thumbnail((200, 200))
            # Quantize to 8 colors then read palette
            quant = img.quantize(colors=8, method=Image.Quantize.MAXCOVERAGE)
            pal = quant.getpalette()[: 8 * 3]
            counts = Counter(quant.getdata()).most_common(8)
            colors = []
            for idx, _count in counts:
                r, g, b = pal[idx * 3:idx * 3 + 3]
                colors.append("#{:02X}{:02X}{:02X}".format(r, g, b))
            return jsonify({"colors": colors})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/palette/deck", methods=["GET"])
    def palette_deck():
        """Aggregate palette across all slides — first 5 most-common colors."""
        slides = get_slides()
        if not slides:
            return jsonify({"colors": []})
        bucket = Counter()
        for sf in slides[:20]:  # cap for speed
            try:
                img = Image.open(sf).convert("RGB")
                img.thumbnail((120, 120))
                q = img.quantize(colors=6)
                pal = q.getpalette()[:6 * 3]
                for idx, count in Counter(q.getdata()).most_common(6):
                    r, g, b = pal[idx * 3:idx * 3 + 3]
                    bucket[(r // 16 * 16, g // 16 * 16, b // 16 * 16)] += count
            except OSError:
                continue
        top = [c for c, _ in bucket.most_common(8)]
        return jsonify({
            "colors": ["#{:02X}{:02X}{:02X}".format(*c) for c in top],
        })

    # ─── .slidecraft portable archive (slides + data + master + comments)
    @app.route("/api/deck/export-portable", methods=["POST"])
    def export_portable():
        out_name = f"deck_{uuid.uuid4().hex[:8]}.slidecraft"
        out_path = EXPORT_DIR / out_name
        manifest = {
            "version": 1,
            "deck_name": ctx["_get_deck_name"](),
            "created": uuid.uuid4().hex,
        }
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))
            for sf in get_slides():
                zf.write(sf, f"slides/{sf.name}")
            if DATA_FILE.exists():
                zf.write(DATA_FILE, "slide_data.json")
            comments = BASE_DIR / "comments.json"
            if comments.exists():
                zf.write(comments, "comments.json")
            if MASTER_FILE.exists():
                zf.write(MASTER_FILE, "master_slide.json")
        return send_file(str(out_path), as_attachment=True,
                         download_name="deck.slidecraft")

    @app.route("/api/deck/import-portable", methods=["POST"])
    def import_portable():
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        f = request.files["file"]
        if not f.filename.lower().endswith(".slidecraft"):
            return jsonify({"error": "Only .slidecraft archives"}), 400

        UPLOAD_DIR.mkdir(exist_ok=True)
        archive = UPLOAD_DIR / secure_filename(f.filename)
        f.save(str(archive))

        try:
            with zipfile.ZipFile(archive) as zf:
                names = zf.namelist()
                if "manifest.json" not in names:
                    return jsonify({"error": "Missing manifest.json"}), 400
                # Wipe + restore
                for old in SLIDES_DIR.glob("slide-*.jpg"):
                    old.unlink()
                for member in names:
                    if member.startswith("slides/") and member.endswith(".jpg"):
                        target = SLIDES_DIR / Path(member).name
                        target.write_bytes(zf.read(member))
                if "slide_data.json" in names:
                    DATA_FILE.write_bytes(zf.read("slide_data.json"))
                if "comments.json" in names:
                    (BASE_DIR / "comments.json").write_bytes(zf.read("comments.json"))
                if "master_slide.json" in names:
                    MASTER_FILE.write_bytes(zf.read("master_slide.json"))
                meta = json.loads(zf.read("manifest.json").decode())
                if meta.get("deck_name"):
                    ctx["_set_deck_name"](meta["deck_name"])
            return jsonify({"ok": True, "num_slides": len(get_slides())})
        except zipfile.BadZipFile:
            return jsonify({"error": "Corrupt .slidecraft archive"}), 400

    # ─── Auto-save heartbeat (server-side mirror so restart restores in-flight)
    AUTOSAVE_FILE = BASE_DIR / "autosave.json"

    @app.route("/api/autosave", methods=["POST"])
    def autosave():
        payload = request.get_json(silent=True) or {}
        if not isinstance(payload, dict):
            return jsonify({"error": "Bad payload"}), 400
        # Cap at 5MB serialized
        s = json.dumps(payload)[:5_000_000]
        AUTOSAVE_FILE.write_text(s)
        return jsonify({"ok": True})

    @app.route("/api/autosave", methods=["GET"])
    def get_autosave():
        if not AUTOSAVE_FILE.exists():
            return jsonify({})
        try:
            return jsonify(json.loads(AUTOSAVE_FILE.read_text()))
        except json.JSONDecodeError:
            return jsonify({})

    return {
        "themes_dir": THEMES_DIR,
        "master_file": MASTER_FILE,
    }
