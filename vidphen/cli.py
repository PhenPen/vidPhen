from concurrent.futures import ThreadPoolExecutor, as_completed

from vidphen.contentSelect import ui, video,playlist
from vidphen.contentSelect.validators import is_valid_url, parse_url_list, youtube_link_kind
from vidphen.downloadSelect import downloaderVideo,downloaderPlaylist
from vidphen.downloadSelect.runner import ask_base_dir
from vidphen.metaDataSelect.metaData import fetch, fetch_playlist, format_duration
from vidphen.subtitleSelect.sub_langs import (
    get_sub_langs, plan_subs, plan_subs_only, subtitle_availability, subtitle_languages,
)



def _prompt_url_list(prompt_text, on_link=None):
    """Accept one or more links per line and queue each new valid link."""
    print(prompt_text)
    print("Press Enter on an empty line when done. Type :back to return to the main menu.")
    good, bad, seen = [], [], set()
    line_number = 1
    while True:
        line = ui.prompt(f"Link {line_number} (empty line to finish) : ")
        if not line.strip():
            return good, bad
        line_number += 1
        duplicates = []
        valid, invalid = parse_url_list(line, duplicates=duplicates)
        for url in valid:
            if url in seen:
                duplicates.append(url)
                continue
            seen.add(url)
            good.append(url)
            if on_link:
                on_link(url)
        for url in invalid:
            if url not in seen:
                bad.append(url)
                seen.add(url)
        for url in duplicates:
            print(f"Skipped duplicate link: {url}")


def _filter_link_kind(urls, mode):
    accepted = []
    for url in urls:
        kind = youtube_link_kind(url)
        if mode == "video" and kind == "playlist":
            print(f"Skipped playlist link in Videos mode: {url}")
        elif mode == "playlist" and kind == "video":
            print(f"Skipped video link without a playlist: {url}")
        else:
            accepted.append(url)
    return accepted


def _collect_previews(mode):
    inspect = fetch if mode == "video" else fetch_playlist
    executor = ThreadPoolExecutor(max_workers=3)
    pending = {}

    def queue(url):
        if _filter_link_kind([url], mode):
            pending[executor.submit(inspect, url, quiet=True)] = url

    try:
        _, bad = _prompt_url_list(f"Paste one or more {mode} links.", on_link=queue)
        for link in bad:
            print(f"Skipped invalid link: {link}")
        if not pending:
            print(f"No valid {mode} links. Try again")
            return []
        ready = {future for future in pending if future.done()}
        waiting = [future for future in pending if future not in ready]
        if waiting:
            print(f"Preview: {len(ready)} ready, {len(waiting)} still checking")
            for future, url in pending.items():
                if future in ready:
                    info = future.result()
                    print(f"  Ready: {info['title']}" if info else f"  Preview unavailable: {url}")
                else:
                    print(f"  Checking: {url}")
            for future in as_completed(waiting):
                info = future.result()
                print(f"  Ready: {info['title']}" if info else f"  Preview unavailable: {pending[future]}")
        previews = [(url, future.result()) for future, url in pending.items()]
    except KeyboardInterrupt:
        print("\nPreview cancelled.")
        raise ui.BackToMenu from None
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

    value_label = "Duration" if mode == "video" else "Entries"
    rows = []
    for index, (url, info) in enumerate(previews, 1):
        if info:
            value = format_duration(info["duration"]) if mode == "video" else str(info["count"])
            rows.append((str(index), info["title"], value))
        else:
            rows.append((str(index), url, "Preview unavailable"))
    ui.show_table(f"{mode.title()} preview", ("#", mode.title(), value_label), rows)
    return previews


def _customize_batch():
    while True:
        choice = ui.prompt("Enter: apply settings to all | C: customize per item : ").strip().upper()
        if choice in ("", "C"):
            return choice == "C"
        print("Press Enter or type C to customize.")


def _ask_scope(what):
    """Same settings for all vs per video. Returns 'all' or 'per'."""
    while True:
        choice = ui.prompt(f"{what} for all videos? 1) Same for all 2) Pick per video : ").strip()
        if choice == "1":
            return "all"
        elif choice == "2":
            return "per"
        print("Invalid Selection. Try again")


def _pick_file(files):
    """Numbered file picker for playlists/batches. Returns path or None."""
    from pathlib import Path
    shown = files[:50]
    for i, f in enumerate(shown, 1):
        print(f"{i}) {Path(f).name}")
    if len(files) > len(shown):
        print(f"... +{len(files) - len(shown)} more - open the folder instead")
    print("0) Back")
    while True:
        raw = ui.prompt(f"Pick file 0-{len(shown)} : ").strip()
        if raw == "0":
            return None
        try:
            n = int(raw)
        except ValueError:
            print("Invalid Selection. Try again")
            continue
        if 1 <= n <= len(shown):
            return shown[n - 1]
        print("Invalid Selection. Try again")


def _ask_next(base_dir=None, files=None):
    """What-next menu. Return True to go again, False to exit."""
    from vidphen.downloadSelect.runner import open_folder, open_path
    seen, unique = set(), []
    for f in list(files or []):
        if f and f not in seen:
            seen.add(f)
            unique.append(f)
    files = unique
    has_folder = bool(base_dir)
    # Sequential numbers rebuild each loop so there is never a gap:
    # quit is 2/3/4 depending on what is offered.
    opts = [("1", "Main menu")]
    if has_folder:
        opts.append((str(len(opts) + 1), "Open download folder"))
    if files:
        opts.append((str(len(opts) + 1), "Open downloaded file"))
    quit_num = str(len(opts) + 1)
    folder_num = next((n for n, label in opts if label == "Open download folder"), None)
    file_num = next((n for n, label in opts if label == "Open downloaded file"), None)
    while True:
        print("What next?")
        for num, label in opts:
            print(f"{num}) {label}")
        print(f"{quit_num}) Quit")
        choice = ui.prompt(f"Pick 1-{quit_num} : ").strip().upper()
        if choice == "1" or choice == "Y":
            return True
        elif choice == folder_num and has_folder:
            open_folder(base_dir)
            continue
        elif choice == file_num and files:
            if len(files) == 1:
                open_path(files[0])
            else:
                picked = _pick_file(files)
                if picked:
                    open_path(picked)
            continue
        elif choice == quit_num or choice == "4" or choice == "N":
            print("Bye!")
            return False
        print("Invalid Selection. Try again")


def _record_result(results, title, rc, files, subtitles_only=False):
    if files and rc == 0:
        status = "Files found"
    elif files:
        status = "Partial download"
    elif rc == 0:
        status = "No subtitle file found" if subtitles_only else "No output file found"
    else:
        status = "Interrupted" if rc == 130 else "Failed"
    results.append((title, status, files))


def _show_results(results):
    all_files = list(dict.fromkeys(path for _, _, files in results for path in files))
    rows = []
    for title, status, files in results:
        count = f" ({len(files)} {'file' if len(files) == 1 else 'files'})" if files else ""
        rows.append((f"{status}{count}", title))
    file_label = "file" if len(all_files) == 1 else "files"
    ui.show_table(
        f"Results for {len(results)} links | {len(all_files)} {file_label} available",
        ("Result", "Item"), rows,
    )
    return all_files


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
        print("5) Check dependencies")
        choice = ui.prompt("Pick 1-5 : ").strip()
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
        elif choice == "5":
            from vidphen.doctor import run_doctor
            run_doctor()
        else:
            print("Invalid Selection. Try again")
            close_section()


def _confirm_subtitle_download(total):
    while True:
        choice = ui.prompt(f"Download subtitles for {total} item(s)? (y/n) : ").strip().upper()
        if choice in ("Y", "N"):
            return choice == "Y"
        print("Enter Y or N.")


def _handle_subtitles_videos():
    previews = _collect_previews("video")
    eligible = []
    results = []
    for url, info in previews:
        title = info["title"] if info else url
        status = subtitle_availability(subtitle_languages(info))
        if status is False:
            print(f"No subtitles available: {title}")
            results.append((title, "Skipped: no subtitles available", []))
        else:
            if status is None:
                print(f"Couldn't check subtitles: {title}")
            eligible.append((url, title, info))
    if not eligible:
        return True

    customize = len(eligible) > 1 and _customize_batch()
    per_video = customize and _ask_scope("Subtitles") == "per"
    if not per_video:
        url = eligible[0][0] if len(eligible) == 1 else None
        shared_mode, shared_args = plan_subs_only(url)

    planned = []
    for url, title, info in eligible:
        mode, args = plan_subs_only(url) if per_video else (shared_mode, shared_args)
        status = subtitle_availability(subtitle_languages(info), args)
        if mode == "none":
            results.append((title, "Skipped: no subtitles selected", []))
        elif status is False:
            print(f"No subtitles in the selected language: {title}")
            results.append((title, "Skipped: selected subtitles unavailable", []))
        else:
            planned.append((url, title, mode, args))
    if not planned or not _confirm_subtitle_download(len(planned)):
        return True
    return _run_subtitle_downloads(planned, results)


def _selected_playlist_entries(info, scope):
    if info is None:
        return []
    entries = info.get("entries", [])
    if scope[0] == "R":
        start, end = scope[1:]
        return [entry for entry in entries if start <= entry["index"] <= end]
    if scope[0] == "S":
        selected = {int(position) for position in scope[1].split(",")}
        return [entry for entry in entries if entry["index"] in selected]
    return entries


def _check_playlist_subtitles(info, scope, args):
    entries = _selected_playlist_entries(info, scope)
    if not entries:
        print("Couldn't check subtitles for the selected playlist entries.")
        return None
    print(f"Checking subtitles for {len(entries)} selected entries…")
    executor = ThreadPoolExecutor(max_workers=3)
    try:
        urls = dict.fromkeys(entry["url"] for entry in entries if entry["url"])
        futures = {url: executor.submit(get_sub_langs, url) for url in urls}
        statuses = [
            subtitle_availability(futures[entry["url"]].result(), args) if entry["url"] else None
            for entry in entries
        ]
    except KeyboardInterrupt:
        print("\nSubtitle check cancelled.")
        raise ui.BackToMenu from None
    finally:
        executor.shutdown(wait=False, cancel_futures=True)
    available = statuses.count(True)
    unavailable = statuses.count(False)
    unknown = statuses.count(None)
    print(f"Selected subtitles: {available} available, {unavailable} unavailable, {unknown} unverified.")
    if available:
        return True
    if unknown:
        return None
    print("No subtitles available in the selected language.")
    return False


def _handle_subtitles_playlists():
    previews = _collect_previews("playlist")
    if not previews:
        return True
    customize = len(previews) > 1 and _customize_batch()
    per_playlist = customize and _ask_scope("Subtitles") == "per"
    per_range = _ask_scope("Video range") == "per" if customize else len(previews) == 1
    if not per_playlist:
        shared_mode, shared_args = plan_subs_only()
    shared_scope = None if per_range else downloaderPlaylist.plan_scope()
    planned, results = [], []
    for url, info in previews:
        title = info["title"] if info else url
        print(title)
        mode, args = plan_subs_only() if per_playlist else (shared_mode, shared_args)
        if mode == "none":
            results.append((title, "Skipped: no subtitles selected", []))
            continue
        scope = shared_scope or downloaderPlaylist.plan_scope(info["count"] if info else None)
        if _check_playlist_subtitles(info, scope, args) is False:
            results.append((title, "Skipped: selected subtitles unavailable", []))
            continue
        planned.append((url, title, mode, args, scope))
    if not planned or not _confirm_subtitle_download(len(planned)):
        return True
    return _run_subtitle_downloads(planned, results)


def _run_subtitle_downloads(planned, results):
    base_dir = ask_base_dir()
    for url, title, mode, args, *scope in planned:
        print(f"--- Subtitles: {title} ---")
        try:
            if scope:
                rc, files = downloaderPlaylist.downloader(
                    "best", url, sub_mode=mode, sub_args=args, base_dir=base_dir, scope=scope[0],
                )
            else:
                rc, files = downloaderVideo.downloader(
                    "best", url, sub_mode=mode, sub_args=args, base_dir=base_dir,
                )
        except ui.BackToMenu:
            raise
        except Exception as error:
            print(f"Subtitle download failed: {error}")
            rc, files = 1, []
        _record_result(results, title, rc, files, subtitles_only=True)
        if rc == 130:
            break
    return _ask_next(base_dir, _show_results(results))


def main():
    from vidphen import __version__
    from vidphen.contentSelect.ui import banner
    banner(__version__)
    # Keep workflow cancellation at the menu boundary.
    while True:
        ui.show_table(
            "What do you want to do?", ("Key", "Action"),
            [("1", "Download videos"), ("2", "Download playlists"),
             ("3", "Download subtitles"), ("4", "Settings"), ("5", "Quit")],
        )
        content = ui.prompt("Choose 1-5: ", allow_back=False).strip().upper()
        content = {"V": "1", "P": "2", "D": "3", "T": "3", "S": "4", "Q": "5"}.get(content, content)
        if content == "5":
            print("Bye!")
            return
        try:
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
                    keep = _handle_subtitles_videos()
                else:
                    keep = _handle_subtitles_playlists()
                if not keep:
                    return
                continue
            if content == "1":
                infos = _collect_previews("video")
                if not infos:
                    continue
                good = [url for url, _ in infos]
                while True:
                    batch_choice = ui.prompt(f"Download these {len(good)} video(s)? (y/n) : ").upper()
                    if batch_choice in ("Y", "N"):
                        break
                    print("Invalid Selection. Try again")
                if batch_choice == "N":
                    print("Cancelled.")
                    continue
                if len(good) > 1 and _customize_batch():
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
                    availability = [subtitle_availability(subtitle_languages(info)) for _, info in infos]
                    if all(status is False for status in availability):
                        print("No subtitles available.")
                        sub_mode, sub_args = "none", []
                    else:
                        sub_mode, sub_args = plan_subs(good[0] if len(good) == 1 else None, allow_only=False)
                else:
                    sub_mode, sub_args = "none", []
                base_dir = ask_base_dir()
                titles = {url: (info["title"] if info else url) for url, info in infos}
                results = []
                for i, (url, info) in enumerate(infos, 1):
                    print(f"--- Video {i}/{len(good)}: {titles.get(url, url)} ---")
                    cur_ID = ID
                    if quality_scope == "per":
                        print(f"Quality for video {i}/{len(good)}:")
                        cur_ID = video.video(url)
                    cur_mode, cur_args = sub_mode, sub_args
                    if subs_scope == "per":
                        print(f"Subtitles for video {i}/{len(good)}:")
                        cur_mode, cur_args = plan_subs(url, allow_only=False)
                    if cur_mode == "with" and subtitle_availability(subtitle_languages(info), cur_args) is False:
                        print("Selected subtitles unavailable. Downloading the video only.")
                        cur_mode, cur_args = "none", []
                    from vidphen.contentSelect.quality import get_available, picked_height
                    _fmt = cur_ID[0] if isinstance(cur_ID, tuple) else cur_ID
                    _picked = picked_height(_fmt)
                    if _picked and fallback_policy in ("ask", "skip"):
                        print(f"Checking available quality ({i}/{len(good)})...")
                        available = get_available(url)
                        heights = available.get("heights", [])
                        if heights and _picked not in heights:
                            lower = max((height for height in heights if height < _picked), default=None)
                            if fallback_policy == "skip" or lower is None:
                                print(f"Skipped: {_picked}p unavailable"
                                      + (f" (best below it: {lower}p)." if lower else "."))
                                results.append((titles.get(url, url), "Skipped: quality unavailable or declined", []))
                                continue
                            print(f"Picked: {_picked}p | Best below it: {lower}p")
                            print("1) Download lower for this video")
                            print("2) Skip this video")
                            print("3) Allow lower for remaining videos too")
                            while True:
                                choice = ui.prompt("Pick 1-3 : ").strip()
                                if choice in ("1", "2", "3"):
                                    break
                                print("Invalid selection. Try again")
                            if choice == "2":
                                results.append((titles.get(url, url), "Skipped: quality unavailable or declined", []))
                                continue
                            if choice == "3":
                                fallback_policy = "auto"
                    try:
                        rc, files = downloaderVideo.downloader(cur_ID, url, sub_mode=cur_mode, sub_args=cur_args, base_dir=base_dir)
                    except ui.BackToMenu:
                        raise
                    except Exception as e:
                        print(f"Video {i} failed: {e}")
                        rc, files = 1, []
                    _record_result(results, titles.get(url, url), rc, files)
                    if rc == 130:
                        break
                last_base_dir, last_files = base_dir, _show_results(results)
            elif content == "2":
                pl_infos = _collect_previews("playlist")
                if not pl_infos:
                    continue
                good = [url for url, _ in pl_infos]
                while True:
                    batch_choice = ui.prompt(f"Download these {len(good)} playlist(s)? (y/n) : ").upper()
                    if batch_choice in ("Y", "N"):
                        break
                    print("Invalid Selection. Try again")
                if batch_choice == "N":
                    print("Cancelled.")
                    continue
                if len(good) > 1 and _customize_batch():
                    quality_scope = _ask_scope("Quality")
                    subs_scope = _ask_scope("Subtitles")
                    range_scope = _ask_scope("Video range")
                else:
                    quality_scope, subs_scope = "all", "all"
                    range_scope = "per" if len(good) == 1 else "all"
                if quality_scope == "all":
                    ID = playlist.playlist(good[0])
                else:
                    ID = None
                if subs_scope == "all":
                    sub_mode, sub_args = plan_subs(allow_only=False)
                else:
                    sub_mode, sub_args = "none", []
                if range_scope == "all":
                    from vidphen.downloadSelect.downloaderPlaylist import plan_scope
                    scope = plan_scope()
                else:
                    scope = None
                base_dir = ask_base_dir()
                titles = {url: (info["title"] if info else url) for url, info in pl_infos}
                results = []
                for i, (url, info) in enumerate(pl_infos, 1):
                    print(f"--- Playlist {i}/{len(good)}: {titles.get(url, url)} ---")
                    cur_ID = ID
                    if quality_scope == "per":
                        print(f"Quality for playlist {i}/{len(good)}:")
                        cur_ID = playlist.playlist(url)
                    cur_mode, cur_args = sub_mode, sub_args
                    if subs_scope == "per":
                        print(f"Subtitles for playlist {i}/{len(good)}:")
                        cur_mode, cur_args = plan_subs(allow_only=False)
                    selection = scope or downloaderPlaylist.plan_scope(info["count"] if info else None)
                    if cur_mode == "with" and _check_playlist_subtitles(info, selection, cur_args) is False:
                        print("Downloading the playlist without subtitles.")
                        cur_mode, cur_args = "none", []
                    try:
                        rc, files = downloaderPlaylist.downloader(cur_ID, url, sub_mode=cur_mode, sub_args=cur_args, base_dir=base_dir, scope=selection)
                    except ui.BackToMenu:
                        raise
                    except Exception as e:
                        print(f"Playlist {i} failed: {e}")
                        rc, files = 1, []
                    _record_result(results, titles.get(url, url), rc, files)
                    if rc == 130:
                        break
                last_base_dir, last_files = base_dir, _show_results(results)
            else:
                print("Not a valid content selection. Try Again")
                continue
            if not _ask_next(last_base_dir, last_files):
                return
        except ui.BackToMenu:
            continue


if __name__ == "__main__":
    main()