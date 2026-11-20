"""File Storage: saves uploaded documents.

The prototype stores files on local disk (backend/data/uploads). The interface
(save / open_path / delete) is kept small so it can be swapped for S3 / MinIO later.
"""
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from ..config import settings

ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx",
    ".txt", ".md", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".mp4", ".mp3", ".zip",
}
# Files the AI can read (teacher material and student work). HEIC (iPhone) is converted to JPEG on upload.
AI_READABLE_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt", ".md", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".heic", ".heif"}
HEIC_EXTENSIONS = {".heic", ".heif"}


def _heic_to_jpeg(path: Path) -> Path:
    from PIL import Image, ImageOps
    from pillow_heif import register_heif_opener

    register_heif_opener()
    target = path.with_suffix(".jpg")
    with Image.open(path) as img:
        ImageOps.exif_transpose(img).convert("RGB").save(target, format="JPEG", quality=90)
    path.unlink(missing_ok=True)
    return target


class LocalStorage:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    async def save(self, file: UploadFile, folder: str | int, allowed: set[str] = ALLOWED_EXTENSIONS) -> tuple[str, int]:
        ext = Path(file.filename or "").suffix.lower()
        if ext not in allowed:
            raise HTTPException(400, f"File type not allowed: {ext or '?'}")
        (self.root / str(folder)).mkdir(parents=True, exist_ok=True)
        stored_name = f"{folder}/{uuid.uuid4().hex}{ext}"
        limit = settings.max_upload_mb * 1024 * 1024
        size = 0
        target = self.root / stored_name
        with target.open("wb") as out:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > limit:
                    out.close()
                    target.unlink(missing_ok=True)
                    raise HTTPException(413, f"File larger than {settings.max_upload_mb} MB")
                out.write(chunk)
        if ext in HEIC_EXTENSIONS:
            try:
                target = _heic_to_jpeg(target)
            except Exception:
                target.unlink(missing_ok=True)
                raise HTTPException(400, "Could not read the HEIC photo")
            stored_name = f"{folder}/{target.name}"
            size = target.stat().st_size
        return stored_name, size

    def save_bytes(self, data: bytes, folder: str | int, ext: str = ".jpg") -> str:
        """Store generated content (e.g. a face thumbnail) and return its stored name."""
        (self.root / str(folder)).mkdir(parents=True, exist_ok=True)
        stored_name = f"{folder}/{uuid.uuid4().hex}{ext}"
        (self.root / stored_name).write_bytes(data)
        return stored_name

    def open_path(self, stored_name: str) -> Path:
        path = (self.root / stored_name).resolve()
        if self.root.resolve() not in path.parents or not path.exists():
            raise HTTPException(404, "File not found")
        return path

    def delete(self, stored_name: str) -> None:
        (self.root / stored_name).unlink(missing_ok=True)


storage = LocalStorage(settings.storage_dir)
