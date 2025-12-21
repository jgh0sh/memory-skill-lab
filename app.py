import io
import os

from flask import Flask, jsonify, request, send_file
from PIL import Image

try:
    import fitz  # PyMuPDF

    HAS_PYMUPDF = True
except Exception:
    HAS_PYMUPDF = False


app = Flask(__name__)

DEFAULT_MAX_SIDE = int(os.environ.get("MAX_SIDE", "1024"))


def _parse_max_side():
    raw = request.form.get("max_side") or request.args.get("max_side")
    if raw is None or raw == "":
        return DEFAULT_MAX_SIDE, None
    try:
        value = int(raw)
    except ValueError:
        return None, "max_side must be an integer"
    if value <= 0:
        return None, "max_side must be greater than zero"
    return value, None


def _resize_raster(image_bytes, fmt, max_side):
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            img.load()
            img.thumbnail((max_side, max_side), Image.LANCZOS)
            output = io.BytesIO()
            if fmt == "JPEG":
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")
                img.save(output, format="JPEG", quality=85, optimize=True)
                return output.getvalue(), "image/jpeg", "jpg", None
            img.save(output, format="PNG", optimize=True)
            return output.getvalue(), "image/png", "png", None
    except Exception:
        return None, None, None, "unable to decode image"


def _resize_pdf(pdf_bytes, max_side):
    if not HAS_PYMUPDF:
        return None, "PDF support requires PyMuPDF. Install it with `pip install pymupdf`."
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        out = fitz.open()
        try:
            for page in doc:
                rect = page.rect
                scale = min(max_side / max(rect.width, rect.height), 1.0)
                new_rect = fitz.Rect(0, 0, rect.width * scale, rect.height * scale)
                new_page = out.new_page(width=new_rect.width, height=new_rect.height)
                new_page.show_pdf_page(new_rect, doc, page.number)
            return out.tobytes(), None
        finally:
            out.close()
    finally:
        doc.close()


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.post("/resize")
def resize():
    if "file" not in request.files:
        return jsonify(error="missing file field named 'file'"), 400

    upload = request.files["file"]
    data = upload.read()
    if not data:
        return jsonify(error="empty upload"), 400

    max_side, error = _parse_max_side()
    if error:
        return jsonify(error=error), 400

    if data[:4] == b"%PDF":
        output_bytes, error = _resize_pdf(data, max_side)
        if error:
            return jsonify(error=error), 400
        return send_file(
            io.BytesIO(output_bytes),
            mimetype="application/pdf",
            as_attachment=False,
            download_name="resized.pdf",
        )

    try:
        with Image.open(io.BytesIO(data)) as img:
            fmt = (img.format or "").upper()
    except Exception:
        fmt = ""

    if fmt not in ("JPEG", "PNG"):
        return jsonify(error="unsupported file type; use JPG, PNG, or PDF"), 400

    output_bytes, mimetype, ext, error = _resize_raster(data, fmt, max_side)
    if error:
        return jsonify(error=error), 400
    return send_file(
        io.BytesIO(output_bytes),
        mimetype=mimetype,
        as_attachment=False,
        download_name=f"resized.{ext}",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
