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
