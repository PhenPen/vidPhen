"""Consumer-friendly quality presets. MP4/H264 preferred, always with fallback.

User presses 1-11. App translates to yt-dlp format strings.
Raw IDs like 247+250 only live behind 11) Advanced.
"""

# (choice, label, format_id)
OPTIONS = [
    ("1", "Best (auto, MP4 if possible)",
     "bv*[ext=mp4][vcodec^=avc1]+ba/b[ext=mp4]/bv*+ba/b/best"),
    ("2", "4K - 2160p MP4",
     "bv*[height<=2160][ext=mp4][vcodec^=avc1]+ba/b[height<=2160][ext=mp4]/bv*[height<=2160]+ba/b[height<=2160]/b/best"),
    ("3", "2K - 1440p MP4",
     "bv*[height<=1440][ext=mp4][vcodec^=avc1]+ba/b[height<=1440][ext=mp4]/bv*[height<=1440]+ba/b[height<=1440]/b/best"),
    ("4", "Full HD - 1080p MP4",
     "bv*[height<=1080][ext=mp4][vcodec^=avc1]+ba/b[height<=1080][ext=mp4]/bv*[height<=1080]+ba/b[height<=1080]/b/best"),
    ("5", "HD - 720p MP4",
     "bv*[height<=720][ext=mp4][vcodec^=avc1]+ba/b[height<=720][ext=mp4]/bv*[height<=720]+ba/b[height<=720]/b/best"),
    ("6", "480p MP4",
     "bv*[height<=480][ext=mp4][vcodec^=avc1]+ba/b[height<=480][ext=mp4]/bv*[height<=480]+ba/b[height<=480]/b/best"),
    ("7", "360p MP4",
     "bv*[height<=360][ext=mp4][vcodec^=avc1]+ba/b[height<=360][ext=mp4]/bv*[height<=360]+ba/b[height<=360]/b/best"),
    ("8", "240p/144p - tiny",
     "bv*[height<=240][ext=mp4][vcodec^=avc1]+ba/b[height<=240][ext=mp4]/bv*[height<=240]+ba/b[height<=240]/b/best"),
    ("9", "Audio - choose type next",
     "AUDIO_ASK"),
    ("10", "Audio original quick (no convert)",
     "bestaudio/best"),
    ("11", "8K - 4320p (rare, giant files)",
     "bv*[height<=4320][ext=mp4][vcodec^=avc1]+ba/b[height<=4320][ext=mp4]/bv*[height<=4320]+ba/b[height<=4320]/b/best"),
]

_AUDIO_OPTIONS = [
    ("1", "MP3 (works everywhere)", "mp3"),
    ("2", "M4A (Apple/phone)", "m4a"),
    ("3", "OPUS (small)", "opus"),
    ("4", "WAV (big, editing)", "wav"),
    ("5", "FLAC (best quality, big)", "flac"),
    ("6", "Original - no convert, fastest", None),
]

_FORMATS = {choice: fmt for choice, _, fmt in OPTIONS}


def show_menu():
    from contentSelect.ui import close_section, open_section
    open_section()
    print("What quality?")
    for choice, label, _ in OPTIONS:
        print(f"{choice}) {label}")
    print("12) Advanced - type ID yourself")


def get_format(choice):
    """Return format_id for menu choice 1-10, or None."""
    return _FORMATS.get(str(choice).strip())


def picked_height(fmt):
    """Extract height limit (eg 1080) from a preset format string. None = Best/audio."""
    import re as _re
    if not fmt or not isinstance(fmt, str):
        return None
    if fmt in ("AUDIO_ASK", "bestaudio", "bestaudio/best"):
        return None
    m = _re.search(r"height<=(\d+)", fmt)
    return int(m.group(1)) if m else None


def get_max_height(url):
    """Best-effort max available height for a video. None if unknown."""
    import re as _re
    from contentSelect.tableShort import parse_formats, table_short
    table = table_short(url, quiet=True)
    if not table:
        return None
    heights = []
    for entry in parse_formats(table):
        res = entry.get("resolution", "")
        m = _re.search(r"(\d{3,4})[x×](\d{3,4})", res)
        if m:
            try:
                heights.append(int(m.group(2)))
                continue
            except ValueError:
                pass
        m = _re.search(r"\b(\d{3,4})p\d?\b", res + " " + entry.get("note", ""))
        if m:
            try:
                heights.append(int(m.group(1)))
            except ValueError:
                pass
    heights = [h for h in heights if 100 <= h <= 4320]
    return max(heights) if heights else None


def show_audio_menu():
    from contentSelect.ui import open_section
    open_section()
    print("Which audio file?")
    for choice, label, _ in _AUDIO_OPTIONS:
        print(f"{choice}) {label}")


def ask_audio_type():
    """After picking Audio: return (format_id, extra_args)."""
    from contentSelect.ui import close_section, prompt
    show_audio_menu()
    codes = {c: code for c, _, code in _AUDIO_OPTIONS}
    while True:
        choice = prompt("Pick 1-6 : ").strip()
        if choice not in codes:
            print("Invalid Selection. Try again")
            continue
        code = codes[choice]
        close_section()
        if code is None:
            return ("bestaudio/best", [])
        return ("bestaudio", ["--extract-audio", "--audio-format", code])


def ask_fallback_policy():
    """If a video lacks the picked quality. Returns 'auto'/'ask'/'skip'."""
    from contentSelect.ui import close_section, open_section, prompt
    open_section()
    print("If a video doesn't have the picked quality?")
    print("1) Auto use best below it (fast)")
    print("2) Ask me each time")
    print("3) Skip that video")
    while True:
        choice = prompt("Pick 1-3 : ").strip()
        if choice in ("1", "2", "3"):
            close_section()
            return {"1": "auto", "2": "ask", "3": "skip"}[choice]
        print("Invalid Selection. Try again")
