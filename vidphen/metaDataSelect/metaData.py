# Video/playlist metadata preview via yt-dlp (no download)
import json
import subprocess
from functools import lru_cache


def format_duration(raw):
    """Convert seconds (eg '658') to '10m 58s'. Hours when needed."""
    try:
        total = int(float(str(raw).strip()))
    except (TypeError, ValueError, OverflowError):
        return "unknown"
    if total < 0:
        return "unknown"
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


def _inspect(url, options):
    try:
        result = subprocess.run(
            ["yt-dlp", *options, "--dump-single-json", "--skip-download",
             "--socket-timeout", "10", "--", url],
            capture_output=True, encoding="utf-8", errors="replace", timeout=45,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if isinstance(data, dict):
                return data
    except (OSError, subprocess.TimeoutExpired, ValueError):
        pass
    return None


@lru_cache(maxsize=256)
def inspect_video(url):
    """Return metadata, formats, and captions from a single lookup."""
    data = _inspect(url, ["--no-playlist"])
    if data is None or "entries" in data:
        return None
    return {
        "title": data.get("title") or url,
        "uploader": data.get("uploader"),
        "duration": data.get("duration"),
        "url": data.get("webpage_url") or url,
        "language": data.get("language"),
        "formats": [
            {key: fmt.get(key) for key in ("format_id", "ext", "resolution", "height", "acodec", "vcodec")}
            for fmt in (data.get("formats") or [data]) if isinstance(fmt, dict)
        ],
        "subtitles": sorted(data.get("subtitles") or {}),
        "automatic_captions": sorted(set(data.get("automatic_captions") or {}) - {"live_chat"}),
    }


def fetch(url, quiet=False):
    info = inspect_video(url)
    if not quiet:
        if info:
            print(f"Title: {info['title']}")
            print(f"Uploader: {info['uploader'] or 'unknown'}")
            print(f"Duration: {format_duration(info['duration'])}")
        else:
            print(f"Could not inspect video: {url}")
    return info


@lru_cache(maxsize=32)
def _inspect_playlist(url):
    data = _inspect(url, ["--yes-playlist", "--flat-playlist"])
    if data is None or not isinstance(data.get("entries"), list):
        return None
    entries = []
    for index, entry in enumerate(data["entries"], 1):
        entry = entry or {}
        entries.append({
            "index": entry.get("playlist_index") or index,
            "url": entry.get("webpage_url") or entry.get("url"),
        })
    return {"title": data.get("title") or url, "count": len(entries), "url": url, "entries": entries}


def fetch_playlist(url, quiet=False):
    info = _inspect_playlist(url)
    if not quiet:
        if info:
            print(f"Playlist: {info['title']}")
            print(f"Videos: {info['count']}")
        else:
            print(f"Could not inspect playlist: {url}")
    return info
