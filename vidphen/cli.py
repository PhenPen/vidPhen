from vidphen.contentSelect import ui, video,playlist
from vidphen.contentSelect.validators import is_valid_url, parse_url_list
from vidphen.downloadSelect import downloaderVideo,downloaderPlaylist
from vidphen.downloadSelect.runner import ask_base_dir
from vidphen.metaDataSelect.metaData import fetch, format_duration
from vidphen.subtitleSelect.sub_langs import plan_subs, plan_subs_only



def _prompt_url_list(prompt_text):
    """Paste one per line (empty line finishes); commas/spaces also ok."""
    print(prompt_text)
    print("(Paste one link per line, empty line to finish. Commas work too.)")
    lines = []
    while True:
        line = ui.prompt(f"Link {len(lines) + 1} (empty line to finish) : ")
        if not line.strip():
            break
        lines.append(line)
    return parse_url_list("\n".join(lines))


def _ask_count(what):
    """1) One vs 2) Multiple. Returns 'one' or 'many'."""
    while True:
        choice = ui.prompt(f"How many {what}? 1) One 2) Multiple : ").strip()
        if choice == "1":
            return "one"
        elif choice == "2":
            return "many"
        print("Invalid Selection. Try again")


def _prompt_single_url(prompt_text):
    """Single link prompt. Returns ([url], []) like _prompt_url_list."""
    while True:
        url = ui.prompt(prompt_text).strip()
        if is_valid_url(url):
            return ([url], [])
        print("Invalid link. Paste a video link and try again")


def _preview_batch(urls):
    """Numbered preview section. Returns list of (url, info)."""
    from vidphen.contentSelect.ui import close_section, open_section
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


def _ask_scope(what):
    """Same settings for all vs per video. Returns 'all' or 'per'."""
    while True:
        choice = ui.prompt(f"{what} for all videos? 1) Same for all 2) Pick per video : ").strip()
        if choice == "1":
            return "all"
        elif choice == "2":
            return "per"
        print("Invalid Selection. Try again")


def _ask_another():
    """Return True to go again, False to exit."""
    while True:
        choice = ui.prompt("Download another? (y/n) : ").upper()
        if choice == "Y":
            return True
        elif choice == "N":
            print("Bye!")
            return False
        else:
            print("Invalid Selection. Try again")


def _settings_menu():
    """View/change app settings. Returns when user picks Back."""
    from vidphen.configSelect.config import _load_config, get_config_path
    from vidphen.contentSelect.ui import close_section, open_section
    while True:
        open_section()
        print("Settings")
        print(f"Saved folder : {_load_config() or '(not set yet)'}")
        print(f"Config file  : {get_config_path()}")
        print("1) Change default download folder")
        print("2) Open config file location")
        print("3) Check for yt-dlp updates")
        print("4) Back")
        choice = ui.prompt("Pick 1-4 : ").strip()
        if choice == "1":
            from vidphen.configSelect.config import set_default_location
            raw = ui.prompt("Enter new default folder : ").strip().strip('"')
            try:
                saved = set_default_location(raw)
            except OSError as e:
                print(f"Could not use that folder: {e}")
                close_section()
                continue
            print(f"Saved. New default: {saved}")
            close_section()
        elif choice == "2":
            import os
            import sys
            path = get_config_path()
            print(f"Config lives at: {path}")
            try:
                if sys.platform == "win32":
                    os.startfile(path.parent)
                elif sys.platform == "darwin":
                    import subprocess
                    subprocess.run(["open", path.parent])
                else:
                    import subprocess
                    subprocess.run(["xdg-open", path.parent])
            except OSError:
                pass
            close_section()
        elif choice == "3":
            from vidphen.doctor import check_ytdlp_update
            check_ytdlp_update()
            close_section()
        elif choice == "4":
            close_section()
            return
        else:
            print("Invalid Selection. Try again")
            close_section()


def _handle_subtitles_videos():
    """Subtitles-only flow for videos. No quality prompt."""
    if _ask_count("videos") == "one":
        good, bad = _prompt_single_url("Enter video URL : ")
    else:
        good, bad = _prompt_url_list("Enter video URLs : ")
    if bad:
        print(f"Skipped {len(bad)} invalid link(s):")
        for b in bad:
            print(f"  - {b}")
    if not good:
        print("No valid video links. Try again")
        return
    infos = _preview_batch(good)
    while True:
        batch_choice = ui.prompt(f"Download subtitles for these {len(good)} video(s)? (y/n) : ").upper()
        if batch_choice in ("Y", "N"):
            break
        print("Invalid Selection. Try again")
    if batch_choice == "N":
        print("Cancelled.")
        return
    if len(good) > 1:
        subs_scope = _ask_scope("Subtitles")
    else:
        subs_scope = "all"
    if subs_scope == "all":
        sub_mode, sub_args = plan_subs_only(good[0] if len(good) == 1 else None)
    else:
        sub_mode, sub_args = "none", []
    if sub_mode == "none" and subs_scope == "all":
        print("Continuing without subtitles.")
        return
    base_dir = ask_base_dir()
    titles = {url: (info["title"] if info else url) for url, info in infos}
    ok, failed, skipped = 0, 0, 0
    for i, url in enumerate(good, 1):
        print(f"--- Subtitles {i}/{len(good)}: {titles.get(url, url)} ---")
        cur_mode, cur_args = sub_mode, sub_args
        if subs_scope == "per":
            print(f"Subtitles for video {i}/{len(good)}:")
            cur_mode, cur_args = plan_subs_only(url)
        if cur_mode == "none":
            print("Skipped: no subtitles.")
            skipped += 1
            continue
        try:
            rc = downloaderVideo.downloader("best", url, sub_mode=cur_mode, sub_args=cur_args, base_dir=base_dir)
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


def _handle_subtitles_playlists():
    """Subtitles-only flow for playlists. No quality prompt."""
    if _ask_count("playlists") == "one":
        good, bad = _prompt_single_url("Enter playlist URL : ")
    else:
        good, bad = _prompt_url_list("Enter playlist URLs : ")
    if bad:
        print(f"Skipped {len(bad)} invalid link(s):")
        for b in bad:
            print(f"  - {b}")
    if not good:
        print("No valid playlist links. Try again")
        return
    from vidphen.contentSelect.ui import close_section as _close, open_section as _open
    from vidphen.metaDataSelect.metaData import fetch_playlist
    _open()
    print(f"{len(good)} playlist(s) found:")
    pl_infos = []
    for i, url in enumerate(good, 1):
        try:
            info = fetch_playlist(url, quiet=True)
        except Exception:
            info = None
        pl_infos.append((url, info))
        if info:
            print(f"{i}) {info['title']} - {info['count']} videos")
        else:
            print(f"{i}) {url} - preview failed")
    _close()
    while True:
        batch_choice = ui.prompt(f"Download subtitles for these {len(good)} playlist(s)? (y/n) : ").upper()
        if batch_choice in ("Y", "N"):
            break
        print("Invalid Selection. Try again")
    if batch_choice == "N":
        print("Cancelled.")
        return
    if len(good) > 1:
        subs_scope = _ask_scope("Subtitles")
        range_scope = _ask_scope("Video range")
    else:
        subs_scope, range_scope = "all", "per"
    if subs_scope == "all":
        sub_mode, sub_args = plan_subs_only(good[0] if len(good) == 1 else None)
    else:
        sub_mode, sub_args = "none", []
    if sub_mode == "none" and subs_scope == "all":
        print("Continuing without subtitles.")
        return
    if range_scope == "all":
        from vidphen.downloadSelect.downloaderPlaylist import plan_scope
        scope = plan_scope()
    else:
        scope = None
    base_dir = ask_base_dir()
    titles = {url: (info["title"] if info else url) for url, info in pl_infos}
    ok, failed, skipped = 0, 0, 0
    for i, url in enumerate(good, 1):
        print(f"--- Playlist {i}/{len(good)}: {titles.get(url, url)} ---")
        cur_mode, cur_args = sub_mode, sub_args
        if subs_scope == "per":
            print(f"Subtitles for playlist {i}/{len(good)}:")
            cur_mode, cur_args = plan_subs_only(url)
        if cur_mode == "none":
            print("Skipped: no subtitles.")
            skipped += 1
            continue
        try:
            rc = downloaderPlaylist.downloader("best", url, sub_mode=cur_mode, sub_args=cur_args, base_dir=base_dir, scope=scope)
        except Exception as e:
            print(f"Playlist {i} failed: {e}")
            rc = 1
        if rc == 0:
            ok += 1
        else:
            failed += 1
    if skipped:
        print(f"Done: {ok} ok, {failed} failed, {skipped} skipped out of {len(good)}")
    else:
        print(f"Done: {ok} ok, {failed} failed out of {len(good)}")


def main():
    from vidphen import __version__
    from vidphen.contentSelect.ui import banner
    banner(__version__)
    from vidphen.doctor import run_doctor
    run_doctor()
    # Video or Playlist selection, loop until user quits
    while True:
        from vidphen.contentSelect.ui import close_section, open_section
        open_section()
        print("What do you want to do?")
        print("1) Download videos")
        print("2) Download playlists")
        print("3) Download subtitles only")
        print("4) Check settings")
        print("5) Quit")
        content = ui.prompt("Pick 1-5 : ").strip().upper()
        close_section()
        content = {"V": "1", "P": "2", "D": "3", "T": "3", "S": "4", "Q": "5"}.get(content, content)
        if content == "5":
            print("Bye!")
            return
        if content == "4":
            _settings_menu()
            continue
        if content == "3":
            while True:
                kind = ui.prompt("Subtitles for 1) Videos 2) Playlists : ").strip()
                if kind in ("1", "2"):
                    break
                print("Invalid Selection. Try again")
            if kind == "1":
                _handle_subtitles_videos()
            else:
                _handle_subtitles_playlists()
            continue
        if content == "1":
            if _ask_count("videos") == "one":
                good, bad = _prompt_single_url("Enter video URL : ")
            else:
                good, bad = _prompt_url_list("Enter video URLs : ")
            if bad:
                print(f"Skipped {len(bad)} invalid link(s):")
                for b in bad:
                    print(f"  - {b}")
            if not good:
                print("No valid video links. Try again")
                continue
            infos = _preview_batch(good)
            while True:
                batch_choice = ui.prompt(f"Download these {len(good)} video(s)? (y/n) : ").upper()
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
                # Dynamic menu already limits choices to what's available,
                # so the pick is valid by construction - no re-check needed.
                ID = video.video(good[0])
                from vidphen.contentSelect.quality import ask_fallback_policy, picked_height
                _picked_fmt = ID[0] if isinstance(ID, tuple) else ID
                if len(good) > 1 and picked_height(_picked_fmt) is not None:
                    fallback_policy = ask_fallback_policy()
                else:
                    fallback_policy = "auto"
            else:
                ID = None
                fallback_policy = "auto"
            if subs_scope == "all":
                sub_mode, sub_args = plan_subs(good[0] if len(good) == 1 else None, allow_only=False)
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
                    cur_mode, cur_args = plan_subs(url, allow_only=False)
                from vidphen.contentSelect.quality import get_available, picked_height
                _fmt = cur_ID[0] if isinstance(cur_ID, tuple) else cur_ID
                _picked = picked_height(_fmt)
                if _picked and fallback_policy in ("ask", "skip"):
                    print(f"Checking available quality ({i}/{len(good)})...")
                    _max = get_available(url).get("max_height")
                    if _max and _max < _picked:
                        if fallback_policy == "skip":
                            print(f"Skipped: best is {_max}p, picked {_picked}p")
                            skipped += 1
                            continue
                        elif fallback_policy == "ask":
                            from vidphen.contentSelect.ui import close_section, open_section
                            open_section()
                            print(f"Video {i}/{len(good)}: {titles.get(url, url)}")
                            print(f"Picked: {_picked}p | Best available: {_max}p")
                            print("1) Download lower for this video")
                            print("2) Skip this video")
                            print("3) Lower for this + all remaining")
                            while True:
                                fc = ui.prompt("Pick 1-3 : ").strip()
                                if fc in ("1", "2", "3"):
                                    break
                                print("Invalid Selection. Try again")
                            close_section()
                            if fc == "2":
                                skipped += 1
                                continue
                            if fc == "3":
                                fallback_policy = "auto"
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
        elif content == "2":
            if _ask_count("playlists") == "one":
                good, bad = _prompt_single_url("Enter playlist URL : ")
            else:
                good, bad = _prompt_url_list("Enter playlist URLs : ")
            if bad:
                print(f"Skipped {len(bad)} invalid link(s):")
                for b in bad:
                    print(f"  - {b}")
            if not good:
                print("No valid playlist links. Try again")
                continue
            from vidphen.contentSelect.ui import close_section as _close, open_section as _open
            from vidphen.metaDataSelect.metaData import fetch_playlist
            _open()
            print(f"{len(good)} playlist(s) found:")
            pl_infos = []
            for i, url in enumerate(good, 1):
                try:
                    info = fetch_playlist(url, quiet=True)
                except Exception:
                    info = None
                pl_infos.append((url, info))
                if info:
                    print(f"{i}) {info['title']} - {info['count']} videos")
                else:
                    print(f"{i}) {url} - preview failed")
            _close()
            while True:
                batch_choice = ui.prompt(f"Download these {len(good)} playlist(s)? (y/n) : ").upper()
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
                range_scope = _ask_scope("Video range")
            else:
                quality_scope, subs_scope, range_scope = "all", "all", "per"
            if quality_scope == "all":
                ID = playlist.playlist(good[0])
            else:
                ID = None
            if subs_scope == "all":
                sub_mode, sub_args = plan_subs(good[0] if len(good) == 1 else None, allow_only=False)
            else:
                sub_mode, sub_args = "none", []
            if range_scope == "all":
                from vidphen.downloadSelect.downloaderPlaylist import plan_scope
                scope = plan_scope()
            else:
                scope = None
            base_dir = ask_base_dir()
            titles = {url: (info["title"] if info else url) for url, info in pl_infos}
            ok, failed, skipped = 0, 0, 0
            for i, url in enumerate(good, 1):
                print(f"--- Playlist {i}/{len(good)}: {titles.get(url, url)} ---")
                cur_ID = ID
                if quality_scope == "per":
                    print(f"Quality for playlist {i}/{len(good)}:")
                    cur_ID = playlist.playlist(url)
                cur_mode, cur_args = sub_mode, sub_args
                if subs_scope == "per":
                    print(f"Subtitles for playlist {i}/{len(good)}:")
                    cur_mode, cur_args = plan_subs(url, allow_only=False)
                try:
                    rc = downloaderPlaylist.downloader(cur_ID, url, sub_mode=cur_mode, sub_args=cur_args, base_dir=base_dir, scope=scope)
                except Exception as e:
                    print(f"Playlist {i} failed: {e}")
                    rc = 1
                if rc == 0:
                    ok += 1
                else:
                    failed += 1
            if skipped:
                print(f"Done: {ok} ok, {failed} failed, {skipped} skipped out of {len(good)}")
            else:
                print(f"Done: {ok} ok, {failed} failed out of {len(good)}")
        else:
            print("Not a valid content selection. Try Again")
            continue
        if not _ask_another():
            return


if __name__ == "__main__":
    main()