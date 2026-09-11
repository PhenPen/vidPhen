from contentSelect import video,playlist
from contentSelect.validators import is_valid_url, parse_url_list
from downloadSelect import downloaderVideo,downloaderPlaylist
from downloadSelect.runner import ask_base_dir
from metaDataSelect.metaData import fetch, format_duration
from subtitleSelect.sub_langs import plan_subs



def _prompt_url_list(prompt):
    """Paste one per line (empty line finishes); commas/spaces also ok."""
    print(prompt)
    print("(Paste one link per line, empty line to finish. Commas work too.)")
    lines = []
    while True:
        try:
            line = input("> " if lines else "Enter Youtube Video URLs : ")
        except KeyboardInterrupt:
            print("\nProcess Interrupted by User. Exiting...")
            return None
        if not line.strip():
            break
        lines.append(line)
    return parse_url_list("\n".join(lines))


def _preview_batch(urls):
    """Numbered preview section. Returns list of (url, info)."""
    from contentSelect.ui import close_section, open_section
    open_section()
    print(f"{len(urls)} video(s) found:")
    infos = []
    for i, url in enumerate(urls, 1):
        try:
            info = fetch(url, quiet=True)
        except Exception:
            info = None
        infos.append((url, info))
        if info:
            print(f"{i}) {info['title']} - {format_duration(info['duration'])}")
        else:
            print(f"{i}) {url} - preview failed")
    close_section()
    return infos


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
            parsed = _prompt_url_list("Enter Youtube Video URLs : ")
            if parsed is None:
                return
            good, bad = parsed
            if bad:
                print(f"Skipped {len(bad)} invalid link(s):")
                for b in bad:
                    print(f"  - {b}")
            if not good:
                print("No valid video links. Try again")
                continue
            _preview_batch(good)
            while True:
                batch_choice = input(f"Download these {len(good)} video(s)? (y/n) : ").upper()
                if batch_choice in ("Y", "N"):
                    break
                print("Invalid Selection. Try again")
            if batch_choice == "N":
                print("Cancelled.")
                if not _ask_another():
                    return
                continue
            ID = video.video(good[0])
            sub_mode, sub_args = plan_subs()
            base_dir = ask_base_dir()
            ok, failed = 0, 0
            for i, url in enumerate(good, 1):
                print(f"--- Video {i}/{len(good)} ---")
                try:
                    rc = downloaderVideo.downloader(ID, url, sub_mode=sub_mode, sub_args=sub_args, base_dir=base_dir)
                except Exception as e:
                    print(f"Video {i} failed: {e}")
                    rc = 1
                if rc == 0:
                    ok += 1
                else:
                    failed += 1
            print(f"Done: {ok} ok, {failed} failed out of {len(good)}")
        elif content == "P":
            url = _prompt_url("Enter Youtube Playlist URL : ")
            if url is None:
                return
            if not _confirm_preview(url):
                if not _ask_another():
                    return
                continue
            ID = playlist.playlist(url)
            sub_mode, sub_args = plan_subs()
            downloaderPlaylist.downloader(ID, url, sub_mode=sub_mode, sub_args=sub_args)
        else:
            print("Not a valid content selection. Try Again")
            continue
        if not _ask_another():
            return


if __name__ == "__main__":
    main()