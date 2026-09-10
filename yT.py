from contentSelect import video,playlist
from contentSelect.validators import is_valid_url
from downloadSelect import downloaderVideo,downloaderPlaylist
from metaDataSelect.metaData import fetch
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



def _confirm_preview(url):
    """Show title/channel/length (or playlist count) and ask to proceed."""
    from contentSelect.ui import close_section, open_section
    open_section()
    try:
        if "list=" in url:
            from metaDataSelect.metaData import fetch_playlist
            info = fetch_playlist(url)
        else:
            info = fetch(url)
    except Exception:
        info = None
    if not info:
        print("Could not preview this link. Proceed anyway?")
        while True:
            choice = input("Continue? (y/n) : ").upper()
            if choice == "Y":
                close_section()
                return True
            elif choice == "N":
                close_section()
                return False
            else:
                print("Invalid Selection. Try again")
    while True:
        choice = input("Download this? (y/n) : ").upper()
        if choice == "Y":
            close_section()
            return True
        elif choice == "N":
            print("Cancelled.")
            close_section()
            return False
        else:
            print("Invalid Selection. Try again")


def _ask_another():
    """Return True to go again, False to exit."""
    while True:
        try:
            choice = input("Download another? (y/n) : ").upper()
        except KeyboardInterrupt:
            print("\nProcess Interrupted by User. Exiting...")
            return False
        if choice == "Y":
            return True
        elif choice == "N":
            print("Bye!")
            return False
        else:
            print("Invalid Selection. Try again")


def main():
    # Video or Playlist selection, loop until user quits
    while True:
        print("Enter V for Video and P for Playlist")
        try:
            content = input("Download Video or Playlist (or Q to quit) : ").upper()
        except KeyboardInterrupt:
            print("\nProcess Interrupted by User. Exiting...")
            return
        if content == "Q":
            print("Bye!")
            return
        if content == "V":
            url = _prompt_url("Enter Youtube Video URL : ")
            if url is None:
                return
            if not _confirm_preview(url):
                if not _ask_another():
                    return
                continue
            ID = video.video(url)
            downloaderVideo.downloader(ID,url)
            subsVideo.subs(url)
        elif content == "P":
            url = _prompt_url("Enter Youtube Playlist URL : ")
            if url is None:
                return
            if not _confirm_preview(url):
                if not _ask_another():
                    return
                continue
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
        else:
            print("Not a valid content selection. Try Again")
            continue
        if not _ask_another():
            return


if __name__ == "__main__":
    main()