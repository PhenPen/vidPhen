import subprocess

from contentSelect.quality import get_format, show_menu
from contentSelect.validators import is_valid_format_id

# To show playlist - returns (format_id, extra_args)
def playlist(url) :
    from contentSelect.quality import ask_audio_type
    from contentSelect.ui import close_section
    print("Quality applies to all videos in the playlist.")
    show_menu()
    while True:
        choice = input("Pick 1-11 : ").strip()
        if choice == "11":
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


# To select playlist video format
def playlistFormat(url) :
    try:
        subprocess.run(['yt-dlp', '-F', url])
    except FileNotFoundError:
        print("yt-dlp command not found. Install it with: pip install yt-dlp")
        return "bv*+ba/b"

    print()
    print("Download video and audio file together for a video in playlist or a single file")
    print("For together files, Enter T " \
    "For a single file, Enter S")

    while True : 
        separate_or_together = input("Enter Together(T) or Separate(S) : ").upper()
        if separate_or_together == "S": 
            playlist_ID = input('Select file to download using ID in this format eg 250 : ').strip()
            if is_valid_format_id(playlist_ID):
                break
            print("Invalid format ID. Try again")
        elif separate_or_together == "T" :
            playlist_ID = input('Select a video and audio file using ID in this format eg 247+250 : ').strip()
            if is_valid_format_id(playlist_ID):
                break
            print("Invalid format ID. Try again")
        else:
            print("Invalid Selection.Try again")
    return playlist_ID