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


def _ask_scope(what):
    """Same settings for all vs per video. Returns 'all' or 'per'."""
    while True:
        choice = input(f"{what} for all videos? 1) Same for all 2) Pick per video : ").strip()
        if choice == "1":
            return "all"
        elif choice == "2":
            return "per"
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
            infos = _preview_batch(good)
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
            if len(good) > 1:
                quality_scope = _ask_scope("Quality")
                subs_scope = _ask_scope("Subtitles")
            else:
                quality_scope, subs_scope = "all", "all"
            if quality_scope == "all":
                ID = video.video(good[0])
                from contentSelect.quality import ask_fallback_policy, picked_height
                _picked_fmt = ID[0] if isinstance(ID, tuple) else ID
                if picked_height(_picked_fmt) is None:
                    fallback_policy = "auto"
                else:
                    fallback_policy = ask_fallback_policy()
            else:
                ID = None
                fallback_policy = "auto"
            if subs_scope == "all":
                sub_mode, sub_args = plan_subs()
            else:
                sub_mode, sub_args = "none", []
            base_dir = ask_base_dir()
            titles = {url: (info["title"] if info else url) for url, info in infos}
            ok, failed, skipped = 0, 0, 0
            for i, url in enumerate(good, 1):
                print(f"--- Video {i}/{len(good)}: {titles.get(url, url)} ---")
                cur_ID = ID
                if quality_scope == "per":
                    print(f"Quality for video {i}/{len(good)}:")
                    cur_ID = video.video(url)
                cur_mode, cur_args = sub_mode, sub_args
                if subs_scope == "per":
                    print(f"Subtitles for video {i}/{len(good)}:")
                    cur_mode, cur_args = plan_subs()
                from contentSelect.quality import get_max_height, picked_height
                _fmt = cur_ID[0] if isinstance(cur_ID, tuple) else cur_ID
                _picked = picked_height(_fmt)
                if _picked:
                    _max = get_max_height(url)
                    if _max and _max < _picked:
                        if fallback_policy == "skip":
                            print(f"Skipped: best is {_max}p, picked {_picked}p")
                            skipped += 1
                            continue
                        elif fallback_policy == "ask":
                            from contentSelect.ui import close_section, open_section
                            open_section()
                            print(f"Video {i}/{len(good)}: {titles.get(url, url)}")
                            print(f"Picked: {_picked}p | Best available: {_max}p")
                            print("1) Download lower for this video")
                            print("2) Skip this video")
                            print("3) Lower for this + all remaining")
                            while True:
                                fc = input("Pick 1-3 : ").strip()
                                if fc in ("1", "2", "3"):
                                    break
                                print("Invalid Selection. Try again")
                            close_section()
                            if fc == "2":
                                skipped += 1
                                continue
                            if fc == "3":
                                fallback_policy = "auto"
                        else:
                            print(f"Note: {_max}p used (picked {_picked}p not available)")
                try:
                    rc = downloaderVideo.downloader(cur_ID, url, sub_mode=cur_mode, sub_args=cur_args, base_dir=base_dir)
                except Exception as e:
                    print(f"Video {i} failed: {e}")
                    rc = 1
                if rc == 0:
                    ok += 1
                else:
                    failed += 1
            if skipped:
                print(f"Done: {ok} ok, {failed} failed, {skipped} skipped out of {len(good)}")
            else:
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