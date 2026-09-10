import subprocess

from contentSelect.validators import is_valid_format_id

# To show playlist
def playlist(url) :
    while True:
        playlistFormatInput = input("Download best quality for all playlist videos(B) or select format personally(S) : ").upper()

        if playlistFormatInput == "B":
            return "bv*+ba/b" # Best video and best audio stream, if it falls, /b means use best combined file as fallback
        elif playlistFormatInput == "S" :
            return playlistFormat(url)
        else:
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