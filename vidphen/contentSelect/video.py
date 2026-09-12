from vidphen.contentSelect.quality import get_format, show_menu
from vidphen.contentSelect.tableShort import table_short
from vidphen.contentSelect.ui import prompt
from vidphen.contentSelect.validators import is_valid_format_id

# To show video - returns (format_id, extra_args)
def video(url):
    from vidphen.contentSelect.quality import ask_audio_type, build_options, get_available, show_options
    from vidphen.contentSelect.ui import close_section
    avail = get_available(url)
    if avail.get("unknown"):
        return _static_pick(url)
    if avail.get("max_height"):
        note = f"best available: {avail['max_height']}p"
    elif not avail.get("has_video", True):
        note = "audio-only source"
    else:
        note = ""
    mapping = show_options(build_options(avail), note)
    top = str(len(mapping))
    while True:
        choice = prompt(f"Pick 1-{top} : ").strip()
        kind = mapping.get(choice)
        if kind is None:
            print("Invalid Selection. Try again")
            continue
        close_section()
        if kind[0] == "fmt":
            return (kind[1], [])
        elif kind[0] == "audio_ask":
            return ask_audio_type()
        elif kind[0] == "audio_orig":
            return ("bestaudio/best", [])
        else:
            return _advanced_pick(url)


def _static_pick(url):
    """Full static menu when availability is unknown."""
    from vidphen.contentSelect.quality import ask_audio_type, get_format, show_menu
    from vidphen.contentSelect.ui import close_section
    show_menu()
    while True:
        choice = prompt("Pick 1-12 : ").strip()
        if choice == "12":
            fmt = videoFormat(url)
            close_section()
            return (fmt, ["--extract-audio", "--audio-format", "mp3"] if fmt == "bestaudio" else [])
        if choice == "9":
            return ask_audio_type()
        fmt = get_format(choice)
        if fmt:
            close_section()
            return (fmt, ["--extract-audio", "--audio-format", "mp3"] if fmt == "bestaudio" else [])
        print("Invalid Selection. Try again")


def _advanced_pick(url):
    fmt = videoFormat(url)
    return (fmt, ["--extract-audio", "--audio-format", "mp3"] if fmt == "bestaudio" else [])

# To select video format (Advanced) - single ID prompt, eg 250 or 247+250
def videoFormat(url) :
    if table_short(url) is None:
        return "best"

    while True :
        video_ID = prompt('Type format ID (eg 250 for one file, 247+250 for video+audio) : ').strip()
        if is_valid_format_id(video_ID):
            break
        print("Invalid format ID. Try again")
    return video_ID