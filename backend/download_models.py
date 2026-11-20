"""Download the face recognition models (OpenCV Zoo) into backend/models/face/.

Run once locally, and automatically during the Render build:
    python download_models.py
Files that are already present with the right size are skipped.
"""
import sys
import urllib.request
from pathlib import Path

BASE = "https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models"
MODELS = {
    # file name: (url, minimum expected size in bytes)
    "face_detection_yunet_2023mar.onnx": (f"{BASE}/face_detection_yunet/face_detection_yunet_2023mar.onnx", 200_000),
    "face_recognition_sface_2021dec.onnx": (f"{BASE}/face_recognition_sface/face_recognition_sface_2021dec.onnx", 30_000_000),
}
TARGET = Path(__file__).resolve().parent / "models" / "face"


def main() -> int:
    TARGET.mkdir(parents=True, exist_ok=True)
    for name, (url, min_size) in MODELS.items():
        path = TARGET / name
        if path.exists() and path.stat().st_size >= min_size:
            print(f"ok   {name} (already present)")
            continue
        print(f"get  {name} ...", flush=True)
        tmp = path.with_suffix(".part")
        urllib.request.urlretrieve(url, tmp)
        if tmp.stat().st_size < min_size:  # e.g. a Git LFS pointer instead of the real file
            tmp.unlink()
            print(f"FAIL {name}: downloaded file is too small", file=sys.stderr)
            return 1
        tmp.replace(path)
        print(f"ok   {name} ({path.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
