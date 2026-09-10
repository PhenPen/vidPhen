from contentSelect import video,playlist
from contentSelect.validators import is_valid_url
from downloadSelect import downloaderVideo,downloaderPlaylist
from subtitleSelect import subsVideo



def _prompt_url(prompt):
    while True:
        try:
            url = input(prompt).strip()
        except KeyboardInterrupt:
            print("\nProcess Interrupted by User. Exiting...")
            return None
        if is_valid_url(url):
            return url
        print("Invalid YouTube URL. Try again")



def main():
    # Video or Playlist selection
    print("Enter V for Video and P for Playlist")
    while True:
        content = input("Download Video or Playlist : ").upper()
        if content == "V":
            url = _prompt_url("Enter Youtube Video URL : ")
            if url is None:
                return
            ID = video.video(url)
            downloaderVideo.downloader(ID,url)
            subsVideo.subs(url)
            break
        elif content == "P":
            url = _prompt_url("Enter Youtube Playlist URL : ")
            if url is None:
                return
            ID = playlist.playlist(url)
            downloaderPlaylist.downloader(ID,url)
            try:
                from subtitleSelect import subsPlaylist
                if hasattr(subsPlaylist, "subs"):
                    subsPlaylist.subs(url)
                else:
                    subsVideo.subs(url)
            except ImportError:
                subsVideo.subs(url)
            break
        else:
            print("Not a valid content selection. Try Again")


    #os.system(f'yt-dlp -F "{url}"') #Could have used os.system here but subprocess seems better

if __name__ == "__main__":
    main()