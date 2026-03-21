import logging
from pathlib import Path

from telegram import InputFile

logger = logging.getLogger(__name__)


def load_photo(path: Path) -> InputFile | None:
    """
    Open a local photo file safely.
    Returns None (with a warning) if the file does not exist.
    Caller is responsible for closing the file handle after send.
    """
    resolved = path.resolve()
    if not resolved.is_file():
        logger.warning("Photo not found: %s", resolved)
        return None
    return InputFile(open(resolved, "rb"), filename=resolved.name)


def object_photo_paths(photos_dir: Path, obj_photo_id: str) -> list[Path]:
    """Return the 1-3 numbered photo paths for a given art object."""
    return [
        photos_dir / f"{obj_photo_id}_Object_{i}.jpg"
        for i in range(1, 4)
        if (photos_dir / f"{obj_photo_id}_Object_{i}.jpg").is_file()
    ]


def route_map_path(scrins_dir: Path, exc_id: int) -> Path:
    return scrins_dir / f"marshrut_{exc_id}.png"


def way_to_path(scrins_dir: Path, obj_id: int, from_obj_id: int) -> Path:
    return scrins_dir / f"wayToObj_{obj_id}_From_{from_obj_id}.png"
