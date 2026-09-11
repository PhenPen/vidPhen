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
    print("11) Advanced - type ID yourself")


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
    import subprocess
    try:
        result = subprocess.run(['yt-dlp', '-F', url], capture_output=True, text=True)
    except FileNotFoundError:
        return None
    if result.returncode != 0:
        return None
    heights = []
    for m in _re.finditer(r"(\d{3,4})[x×](\d{3,4})", result.stdout or ""):
        try:
            heights.append(int(m.group(2)))
        except ValueError:
            pass
    for m in _re.finditer(r"\b(\d{3,4})p\d?\b", result.stdout or ""):
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
    from contentSelect.ui import close_section
    show_audio_menu()
    codes = {c: code for c, _, code in _AUDIO_OPTIONS}
    while True:
        choice = input("Pick 1-6 : ").strip()
        if choice not in codes:
            print("Invalid Selection. Try again")
            continue
        code = codes[choice]
        close_section()
        if code is None:
            return ("bestaudio/best", [])
        return ("bestaudio", ["--extract-audio", "--audio-format", code])
