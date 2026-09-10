import subprocess

# To show video
def video(url):
    while True: 
        videoFormatInput = input("Download best quality format(B) or select for format personally(S) : ").upper()
        if videoFormatInput == "B" :
            return "best"
        elif videoFormatInput == "S" :
            return videoFormat(url)
        else:
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
            video_ID = input('Select file to download using ID in this format eg 250 : ')
            break
        elif separate_or_together == "T" :
            video_ID = input('Select a video and audio file using ID in this format eg 247+250 : ')
            break
        else:
            print("Invalid Selection.Try again")
    return video_ID