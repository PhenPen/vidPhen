from vidphen.contentSelect.quality import get_format, show_menu
from vidphen.contentSelect.tableShort import table_short
from vidphen.contentSelect.ui import prompt
from vidphen.contentSelect.validators import is_valid_format_id

# To show video - returns (format_id, extra_args)
def video(url):
    from contentSelect.quality import ask_audio_type
    show_menu()
    while True:
        choice = prompt("Pick 1-12 : ").strip()
        if choice == "12":
            fmt = videoFormat(url)
            from contentSelect.ui import close_section
            close_section()
            return (fmt, ["--extract-audio", "--audio-format", "mp3"] if fmt == "bestaudio" else [])
        if choice == "9":
            return ask_audio_type()
        fmt = get_format(choice)
        if fmt:
            from contentSelect.ui import close_section
            close_section()
            return (fmt, ["--extract-audio", "--audio-format", "mp3"] if fmt == "bestaudio" else [])
        print("Invalid Selection. Try again")

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