"""Turn stored files into Claude content blocks.

- PDF          -> document block (Claude reads text, formulas and pictures in the PDF)
- JPG/PNG/...  -> image block (downscaled, so phone photos stay within API limits)
- DOCX / PPTX  -> extracted text (+ embedded pictures for PPTX/DOCX, up to a limit)
- TXT / MD     -> text
"""
import base64
import io
from pathlib import Path

from PIL import Image, ImageOps

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
MAX_IMAGE_SIDE = 1600       # px, long edge
MAX_EMBEDDED_IMAGES = 6     # pictures pulled out of a single docx/pptx


def _image_block(raw: bytes) -> dict | None:
    try:
        img = Image.open(io.BytesIO(raw))
        img = ImageOps.exif_transpose(img)  # phone photos: respect orientation
        img.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE))
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
    except Exception:
        return None
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": "image/jpeg", "data": base64.b64encode(buf.getvalue()).decode()},
    }


def _docx(path: Path) -> tuple[str, list[bytes]]:
    import docx

    d = docx.Document(str(path))
    parts = [p.text for p in d.paragraphs if p.text.strip()]
    for table in d.tables:
        for row in table.rows:
            parts.append(" | ".join(c.text.strip() for c in row.cells))
    images = [
        rel.target_part.blob for rel in d.part.rels.values() if "image" in rel.reltype
    ][:MAX_EMBEDDED_IMAGES]
    return "\n".join(parts), images


def _pptx(path: Path) -> tuple[str, list[bytes]]:
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE

    prs = Presentation(str(path))
    parts, images = [], []
    for i, slide in enumerate(prs.slides, 1):
        parts.append(f"--- Slide {i} ---")
        for shape in slide.shapes:
            if shape.has_text_frame and shape.text_frame.text.strip():
                parts.append(shape.text_frame.text)
            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE and len(images) < MAX_EMBEDDED_IMAGES:
                images.append(shape.image.blob)
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame.text.strip():
            parts.append("Notes: " + slide.notes_slide.notes_text_frame.text)
    return "\n".join(parts), images


def file_to_blocks(path: Path, original_name: str) -> list[dict]:
    """Content blocks for one file, preceded by a short label naming the file."""
    ext = Path(original_name).suffix.lower()
    label = {"type": "text", "text": f"[File: {original_name}]"}
    try:
        if ext == ".pdf":
            data = base64.b64encode(path.read_bytes()).decode()
            return [label, {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": data}}]
        if ext in IMAGE_EXT:
            block = _image_block(path.read_bytes())
            return [label, block] if block else [label, {"type": "text", "text": "(image could not be read)"}]
        if ext in (".docx", ".pptx"):
            text, pics = (_docx if ext == ".docx" else _pptx)(path)
            blocks = [label, {"type": "text", "text": text or "(no text)"}]
            blocks += [b for b in (_image_block(p) for p in pics) if b]
            return blocks
        if ext in (".txt", ".md"):
            return [label, {"type": "text", "text": path.read_text(encoding="utf-8", errors="replace")}]
    except Exception as e:  # corrupted / password-protected file
        return [label, {"type": "text", "text": f"(file could not be read: {e})"}]
    return [label, {"type": "text", "text": "(unsupported file type, skipped)"}]
