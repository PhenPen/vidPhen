import subprocess

from contentSelect.quality import get_format, show_menu
from contentSelect.validators import is_valid_format_id

# To show video
def video(url):
    show_menu()
    while True:
        choice = input("Pick 1-11 : ").strip()
        if choice == "11":
            return videoFormat(url)
        fmt = get_format(choice)
        if fmt:
            return fmt
        print("Invalid Selection. Try again")

# To select video format
def videoFormat(url) :
    try:
        subprocess.run(['yt-dlp', '-F', url])
    except FileNotFoundError:
        print("yt-dlp command not found. Install it with: pip install yt-dlp")
        return "best"

    print()
    print("Download either a video and audio file together or a single file")
    print("For together files, Enter T " \
    "For a single file, Enter S")

    while True : 
        separate_or_together = input("Enter Together(T) or Separate(S) : ").upper()
        if separate_or_together == "S": 
            video_ID = input('Select file to download using ID in this format eg 250 : ').strip()
            if is_valid_format_id(video_ID):
                break
            print("Invalid format ID. Try again")
        elif separate_or_together == "T" :
            video_ID = input('Select a video and audio file using ID in this format eg 247+250 : ').strip()
            if is_valid_format_id(video_ID):
                break
            print("Invalid format ID. Try again")
        else:
            print("Invalid Selection.Try again")
    return video_ID