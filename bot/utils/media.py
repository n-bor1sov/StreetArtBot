import logging
from pathlib import Path

from telegram import InputFile

logger = logging.getLogger(__name__)


def load_photo(path: Path) -> InputFile | None:
    """
    Build an InputFile for a local image.
    Returns None (with a warning) if the file does not exist.
    """
    resolved = path.resolve()
    if not resolved.is_file():
        logger.warning("Photo not found: %s", resolved)
        return None
    # PTB/httpx expect a file-like or bytes, not a raw Path (Path has no .read()).
    return InputFile(resolved.read_bytes(), filename=resolved.name)


def object_photo_paths(
    photos_dir: Path,
    obj_photo_id: str,
    *,
    object_id: int | None = None,
) -> list[Path]:
    """Return the 1-3 numbered photo paths for a given art object."""

    def _paths_for(prefix: str) -> list[Path]:
        return [
            photos_dir / f"{prefix}_Object_{i}.jpg"
            for i in range(1, 4)
            if (photos_dir / f"{prefix}_Object_{i}.jpg").is_file()
        ]

    pid = obj_photo_id.strip()
    if pid:
        found = _paths_for(pid)
        if found:
            return found
    if object_id is not None:
        return _paths_for(str(object_id))
    return []


def route_map_path(scrins_dir: Path, exc_id: int) -> Path:
    return scrins_dir / f"marshrut_{exc_id}.png"


def way_to_path(scrins_dir: Path, obj_id: int, from_obj_id: int) -> Path:
    return scrins_dir / f"wayToObj_{obj_id}_From_{from_obj_id}.png"
