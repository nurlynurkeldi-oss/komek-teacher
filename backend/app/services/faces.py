"""Local face recognition for attendance (nothing leaves this computer).

Models (OpenCV Zoo, in backend/models/face/):
  * YuNet  - finds faces and 5 landmarks in a photo
  * SFace  - turns an aligned face into a 128-number "face print"
Two face prints of the same person have a high cosine similarity; SFace's reference threshold is 0.363.
"""
import threading
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

from ..config import BACKEND_DIR

MODEL_DIR = BACKEND_DIR / "models" / "face"
DETECTOR_FILE = MODEL_DIR / "face_detection_yunet_2023mar.onnx"
RECOGNIZER_FILE = MODEL_DIR / "face_recognition_sface_2021dec.onnx"

MATCH_THRESHOLD = 0.363   # SFace reference: same person above this
SURE_THRESHOLD = 0.45     # above this we call the match "confident"; between -> "check"
MAX_SIDE = 2560           # class photos are scaled down to this (keeps small faces detectable)
MIN_FACE_PX = 24          # ignore detections smaller than this

_lock = threading.Lock()  # OpenCV DNN objects are not thread-safe
_detector = None
_recognizer = None


class FaceError(ValueError):
    """A problem the teacher can fix (no face, several faces, models missing...)."""


def models_ready() -> bool:
    return DETECTOR_FILE.exists() and RECOGNIZER_FILE.exists()


def _models():
    global _detector, _recognizer
    if _detector is None:
        if not models_ready():
            raise FaceError("models_missing")
        _detector = cv2.FaceDetectorYN.create(str(DETECTOR_FILE), "", (320, 320), 0.75, 0.3, 5000)
        _recognizer = cv2.FaceRecognizerSF.create(str(RECOGNIZER_FILE), "")
    return _detector, _recognizer


def load_image(path: Path, max_side: int = MAX_SIDE) -> np.ndarray:
    """Read a photo as BGR, respecting the phone's EXIF orientation."""
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        if max(im.size) > max_side:
            im.thumbnail((max_side, max_side))
        return cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)


def detect(img: np.ndarray) -> list[np.ndarray]:
    """All faces in the image (each row: box x,y,w,h + 5 landmarks + score), biggest first."""
    det, _ = _models()
    h, w = img.shape[:2]
    with _lock:
        det.setInputSize((w, h))
        _, faces = det.detect(img)
    if faces is None:
        return []
    rows = [f for f in faces if f[2] >= MIN_FACE_PX and f[3] >= MIN_FACE_PX]
    return sorted(rows, key=lambda f: -(f[2] * f[3]))


def embed(img: np.ndarray, face: np.ndarray) -> np.ndarray:
    """Normalized 128-number face print."""
    _, rec = _models()
    with _lock:
        crop = rec.alignCrop(img, face)
        feat = rec.feature(crop).flatten().astype(np.float32)
    return feat / (np.linalg.norm(feat) + 1e-9)


def thumbnail_jpeg(img: np.ndarray, face: np.ndarray, size: int = 160) -> bytes:
    """Small square picture of the face (for the teacher's list)."""
    x, y, w, h = [float(v) for v in face[:4]]
    cx, cy, side = x + w / 2, y + h / 2, max(w, h) * 1.5
    x0, y0 = int(max(0, cx - side / 2)), int(max(0, cy - side / 2))
    x1, y1 = int(min(img.shape[1], cx + side / 2)), int(min(img.shape[0], cy + side / 2))
    crop = cv2.resize(img[y0:y1, x0:x1], (size, size))
    ok, buf = cv2.imencode(".jpg", crop, [cv2.IMWRITE_JPEG_QUALITY, 88])
    return buf.tobytes() if ok else b""


def box_1000(face: np.ndarray, img: np.ndarray) -> list[int]:
    """Face box as [ymin, xmin, ymax, xmax] in 0..1000 of the image (same format the UI already draws)."""
    h, w = img.shape[:2]
    x, y, bw, bh = [float(v) for v in face[:4]]
    return [
        int(max(0, y) / h * 1000), int(max(0, x) / w * 1000),
        int(min(h, y + bh) / h * 1000), int(min(w, x + bw) / w * 1000),
    ]


def enroll_from_photo(path: Path) -> tuple[np.ndarray, bytes]:
    """A portrait for enrollment must contain exactly one clear face."""
    img = load_image(path, max_side=1600)
    faces = detect(img)
    if not faces:
        raise FaceError("no_face")
    if len(faces) > 1 and faces[1][2] * faces[1][3] > 0.35 * faces[0][2] * faces[0][3]:
        raise FaceError("many_faces")
    return embed(img, faces[0]), thumbnail_jpeg(img, faces[0])


def match(face_prints: list[np.ndarray], people: dict[str, list[np.ndarray]]):
    """Assign faces to people: best pairs first, each face and each person used once.

    Returns one entry per face: (name or None, similarity).
    """
    pairs = []
    for fi, fp in enumerate(face_prints):
        for name, prints in people.items():
            if prints:
                score = max(float(np.dot(fp, p)) for p in prints)
                if score >= MATCH_THRESHOLD:
                    pairs.append((score, fi, name))
    pairs.sort(reverse=True)
    result: list[tuple[str | None, float]] = [(None, 0.0)] * len(face_prints)
    used_faces, used_people = set(), set()
    for score, fi, name in pairs:
        if fi in used_faces or name in used_people:
            continue
        result[fi] = (name, score)
        used_faces.add(fi)
        used_people.add(name)
    # for unmatched faces keep their best (below-threshold) score for information
    for fi, fp in enumerate(face_prints):
        if result[fi][0] is None and people:
            best = max((float(np.dot(fp, p)) for ps in people.values() for p in ps), default=0.0)
            result[fi] = (None, best)
    return result


def to_list(v: np.ndarray) -> list[float]:
    return [round(float(x), 6) for x in v]


def from_list(v) -> np.ndarray:
    a = np.asarray(v, dtype=np.float32)
    return a / (np.linalg.norm(a) + 1e-9)
