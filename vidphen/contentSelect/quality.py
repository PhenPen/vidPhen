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
    ("9", "Audio only",
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

# Height cap per video preset choice. None = Best (no cap).
_HEIGHTS = {
    "1": None,
    "2": 2160,
    "3": 1440,
    "4": 1080,
    "5": 720,
    "6": 480,
    "7": 360,
    "8": 240,
    "11": 4320,
}

_AVAIL_CACHE = {}


def show_menu():
    from vidphen.contentSelect.ui import close_section, open_section
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


def get_available(url):
    """One lookup: {max_height|None, has_video, has_audio, unknown}.

    Results cached per URL for the run so menus and fallback checks
    never pay for the same lookup twice.
    """
    import re as _re
    from vidphen.contentSelect.tableShort import parse_formats, table_short
    if url in _AVAIL_CACHE:
        return _AVAIL_CACHE[url]
    table = table_short(url, quiet=True)
    if not table:
        avail = {"max_height": None, "has_video": True, "has_audio": True, "unknown": True}
        _AVAIL_CACHE[url] = avail
        return avail
    heights, has_video, has_audio = [], False, False
    for entry in parse_formats(table):
        text = f"{entry.get('resolution', '')} {entry.get('note', '')}"
        if "audio" in text.lower():
            has_audio = True
        m = _re.search(r"(\d{3,4})[x×](\d{3,4})", text)
        if m:
            try:
                heights.append(int(m.group(2)))
                has_video = True
                continue
            except ValueError:
                pass
        m = _re.search(r"\b(\d{3,4})p\d?\b", text)
        if m:
            try:
                heights.append(int(m.group(1)))
                has_video = True
            except ValueError:
                pass
    heights = [h for h in heights if 100 <= h <= 4320]
    if heights:
        has_video = True
    if not has_video and not has_audio:
        has_video, has_audio = True, True
    avail = {
        "max_height": max(heights) if heights else None,
        "has_video": has_video,
        "has_audio": has_audio,
        "unknown": False,
    }
    _AVAIL_CACHE[url] = avail
    return avail


def _option_kind(choice, fmt):
    if choice == "9":
        return ("audio_ask",)
    if choice == "10":
        return ("audio_orig",)
    return ("fmt", fmt)


def build_options(avail):
    """Compact menu mapping for an availability dict.

    Returns list of (label, kind) where kind is ("fmt", id),
    ("audio_ask",), ("audio_orig",) or ("advanced",). Pure (testable).
    """
    if avail.get("unknown"):
        items = [(label, _option_kind(choice, fmt)) for choice, label, fmt in OPTIONS]
        items.append(("Advanced - type ID yourself", ("advanced",)))
        return items
    if not avail.get("has_video", True):
        return [
            ("Best (auto)", ("fmt", _FORMATS["1"])),
            ("Audio - choose type next", ("audio_ask",)),
            ("Audio original quick (no convert)", ("audio_orig",)),
            ("Advanced - type ID yourself", ("advanced",)),
        ]
    max_h = avail.get("max_height")
    items = []
    for choice, label, fmt in OPTIONS:
        cap = _HEIGHTS.get(choice)
        if choice == "1" or (cap is not None and (max_h is None or cap <= max_h)):
            items.append((label, ("fmt", fmt)))
        elif choice in ("9", "10"):
            items.append((label, _option_kind(choice, fmt)))
    items.append(("Advanced - type ID yourself", ("advanced",)))
    return items


def show_options(options, note=""):
    """Print a compact numbered menu. Returns {number: kind}."""
    from vidphen.contentSelect.ui import open_section
    open_section()
    print("What quality?" + (f" ({note})" if note else ""))
    mapping = {}
    for i, (label, kind) in enumerate(options, 1):
        print(f"{i}) {label}")
        mapping[str(i)] = kind
    return mapping


def show_audio_menu():
    from vidphen.contentSelect.ui import open_section
    open_section()
    print("Which audio file?")
    for choice, label, _ in _AUDIO_OPTIONS:
        print(f"{choice}) {label}")


def ask_audio_type():
    """After picking Audio: return (format_id, extra_args)."""
    from vidphen.contentSelect.ui import close_section, prompt
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
    from vidphen.contentSelect.ui import close_section, open_section, prompt
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
