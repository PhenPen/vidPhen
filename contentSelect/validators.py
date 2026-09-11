import re

_YOUTUBE_RE = re.compile(
    r"^(https?://)?(www\.|m\.|music\.)?(youtube\.com/(watch\?.*v=|playlist\?.*list=|shorts/)|youtu\.be/)[\w\-]+",
    re.IGNORECASE,
)

_FORMAT_RE = re.compile(r"^(\d+[+\-/]?)+$", re.IGNORECASE)


def is_valid_url(url):
    """Best-effort YouTube URL check (video, playlist, shorts, youtu.be)."""
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    return bool(_YOUTUBE_RE.search(url))


def is_valid_format_id(format_id):
    """Accept 'best', 'bv*+ba/b', '250', '247+250', 'bestaudio' etc."""
    if not format_id or not isinstance(format_id, str):
        return False
    fid = format_id.strip()
    if fid in ("best", "bestaudio", "bestvideo", "bv*+ba/b", "b", "bestaudio/best"):
        return True
    return bool(_FORMAT_RE.match(fid))


def parse_items(items_str):
    """Parse '1,4,6' -> '1,4,6' normalized. Returns None if invalid."""
    if not items_str or not isinstance(items_str, str):
        return None
    parts = [p.strip() for p in items_str.split(",")]
    if not parts:
        return None
    cleaned = []
    for p in parts:
        if not p.isdigit() or int(p) < 1:
            return None
        cleaned.append(str(int(p)))
    if not cleaned:
        return None
    return ",".join(cleaned)


def parse_range(range_str):
    """Parse '2-19' -> (2, 19). Returns None if invalid."""
    if not range_str or "-" not in range_str:
        return None
    try:
        begin_s, end_s = range_str.split("-", 1)
        begin, end = int(begin_s.strip()), int(end_s.strip())
        if begin < 1 or end < begin:
            return None
        return (begin, end)
    except ValueError:
        return None


def parse_url_list(text):
    """Split pasted text on commas/whitespace/newlines. Returns (good, bad)."""
    import re as _re
    if not text or not isinstance(text, str):
        return ([], [])
    raw = [p.strip().strip('"').strip("'") for p in _re.split(r"[\s,;]+", text)]
    raw = [p for p in raw if p]
    good, bad, seen = [], [], set()
    for item in raw:
        if item in seen:
            continue
        seen.add(item)
        if is_valid_url(item):
            good.append(item)
        else:
            bad.append(item)
    return (good, bad)
