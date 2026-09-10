from contentSelect import video,playlist
from downloadSelect import downloaderVideo,downloaderPlaylist
from subtitleSelect import subsVideo



def main():
    # Video or Playlist selection
    print("Enter V for Video and P for Playlist")
    while True:
        content = input("Download Video or Playlist : ").upper()
        if content == "V":
            while True:
                try : url = input("Enter Youtube Video URL : ")
                except KeyboardInterrupt:
                    print("\nProcess Interrupted by User. Exiting...")
                    return
                else:
                    break
            ID = video.video(url)
            downloaderVideo.downloader(ID,url)
            subsVideo.subs(url)
            break
        elif content == "P":
            while True:
                try : url = input("Enter Youtube Playlist URL : ")
                except KeyboardInterrupt:
                    print("\nProcess Interrupted by User. Exiting...")
                    return
                else:
                    break
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