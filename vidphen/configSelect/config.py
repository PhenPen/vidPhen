import json
from pathlib import Path

from vidphen.contentSelect.ui import prompt


def get_config_path():
    """Cross-platform config file location."""
    return Path.home() / ".config" / "phenTube" / "config.json"


def _legacy_config_paths():
    """Old Windows-only config locations to migrate from."""
    return [
        Path(r"C:\Users\HP\AppData\Roaming\yt-dlp\config.txt"),
        Path.home() / "AppData" / "Roaming" / "yt-dlp" / "config.txt",
    ]


def _read_legacy_path(filepath):
    r"""Parse old `-o "path\%(title)s.%(ext)s"` format. Returns path or None."""
    try:
        with open(filepath, mode="r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if line.startswith("-o"):
                    # Format: -o "DOWNLOAD_PATH\%(title)s.%(ext)s"
                    remainder = line[2:].strip().strip('"')
                    if "%(" in remainder:
                        download_path = remainder.split("%(")[0].rstrip("\\/")
                        if download_path:
                            return download_path
    except OSError:
        return None
    return None


def _load_config():
    filepath = get_config_path()
    if filepath.exists():
        try:
            with open(filepath, mode="r", encoding="utf-8") as file:
                data = json.load(file)
                if isinstance(data, dict) and data.get("download_dir"):
                    return data["download_dir"]
        except (OSError, ValueError):
            pass
    # Migrate legacy config if present
    for legacy in _legacy_config_paths():
        if legacy.exists():
            migrated = _read_legacy_path(legacy)
            if migrated:
                return migrated
    return None


def _save_config(download_dir):
    filepath = get_config_path()
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, mode="w", encoding="utf-8") as file:
        json.dump({"download_dir": download_dir}, file, indent=2)


def set_default_location(download_dir):
    """Validate, create, and persist download dir. Returns normalized str path."""
    download_path = Path(download_dir).expanduser()
    download_path.mkdir(parents=True, exist_ok=True)
    normalized = str(download_path)
    _save_config(normalized)
    return normalized


def default_location():
    saved = _load_config()
    if saved:
        # Ensure dir still exists (re-create if deleted)
        try:
            Path(saved).expanduser().mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        return saved
    downloadPath = prompt("Enter default location for downloads : ").strip().strip('"')
    return set_default_location(downloadPath)


