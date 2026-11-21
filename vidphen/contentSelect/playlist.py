from vidphen.contentSelect.quality import get_format, show_menu
from vidphen.contentSelect.video import videoFormat
from vidphen.metaDataSelect.metaData import fetch_playlist
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
    info = fetch_playlist(url, quiet=True)
    if info:
        sample = next((entry["url"] for entry in info["entries"] if entry["url"]), None)
        if sample:
            print("Showing formats from the first available entry. Format IDs can vary by video.")
            return videoFormat(sample)
    print("Could not list formats for a playlist entry.")
    return "bv*+ba/b"
