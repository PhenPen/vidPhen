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
    ("9", "Audio MP3 only",
     "bestaudio"),
    ("10", "Audio original (no convert, faster)",
     "bestaudio/best"),
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
