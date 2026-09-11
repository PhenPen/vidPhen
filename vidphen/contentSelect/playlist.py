from vidphen.contentSelect.quality import get_format, show_menu
from vidphen.contentSelect.tableShort import table_short
from vidphen.contentSelect.ui import prompt
from vidphen.contentSelect.validators import is_valid_format_id

# To show playlist - returns (format_id, extra_args)
def playlist(url) :
    from vidphen.contentSelect.quality import ask_audio_type
    from vidphen.contentSelect.ui import close_section
    print("Quality applies to all videos in the playlist.")
    show_menu()
    while True:
        choice = prompt("Pick 1-12 : ").strip()
        if choice == "12":
            fmt = playlistFormat(url)
            close_section()
            return (fmt, ["--extract-audio", "--audio-format", "mp3"] if fmt == "bestaudio" else [])
        if choice == "9":
            return ask_audio_type()
        fmt = get_format(choice)
        if fmt:
            close_section()
            return (fmt, ["--extract-audio", "--audio-format", "mp3"] if fmt == "bestaudio" else [])
        print("Invalid selection. Try again")


# To select playlist video format (Advanced) - single ID prompt
def playlistFormat(url) :
    if table_short(url) is None:
        return "bv*+ba/b"

    while True :
        playlist_ID = prompt('Type format ID (eg 250 for one file, 247+250 for video+audio) : ').strip()
        if is_valid_format_id(playlist_ID):
            break
        print("Invalid format ID. Try again")
    return playlist_ID