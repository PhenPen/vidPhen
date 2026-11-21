from vidphen.contentSelect.ui import prompt
from vidphen.contentSelect.validators import parse_items, parse_range
from vidphen.downloadSelect.runner import ask_base_dir, build_playlist_template, run_yt_dlp_capture

def _download_with_template(ID, url, extra_args, audio_extra=None, sub_mode="none", sub_args=None, base_dir=None):
    """Download playlist items. Returns (returncode|None, files[])."""
    if base_dir is None:
        base_dir = ask_base_dir()
    download_template = build_playlist_template(base_dir)
    if isinstance(ID, tuple):
        ID, audio_extra = ID[0], list(ID[1] or [])
    audio_extra = list(audio_extra or [])
    sub_args = list(sub_args or [])
    if ID == "bestaudio" and not audio_extra:
        audio_extra = ["--extract-audio", "--audio-format", "mp3"]
    if sub_mode == "only":
        return run_yt_dlp_capture(['--yes-playlist', '--write-subs', '--skip-download']
                     + sub_args + ["-o", download_template] + extra_args + [url])
    sub_flags = (['--write-subs'] + sub_args) if sub_mode == "with" else []
    return run_yt_dlp_capture(['--yes-playlist', '-f', ID, "-o", download_template] + audio_extra + sub_flags + extra_args + [url])


def _scope_to_args(scope):
    """Scope tuple -> yt-dlp playlist args. Scope: ('E',) | ('R', b, e) | ('S', items)."""
    if scope[0] == "E":
        return ["--ignore-errors", "--no-overwrites", "--windows-filenames"]
    elif scope[0] == "R":
        return ["--ignore-errors", "--playlist-start", str(scope[1]), "--playlist-end", str(scope[2]), "--no-overwrites", "--windows-filenames"]
    else:
        return ["--ignore-errors", "--playlist-items", scope[1], "--no-overwrites", "--windows-filenames"]


def plan_scope(count=None):
    """Ask E/R/S once. Returns scope tuple. Repeats until valid."""
    from vidphen.contentSelect.ui import close_section, open_section
    open_section()
    print("Which videos in each playlist?")
    total = f" ({count} entries)" if count else ""
    print(f"E) Everything{total}")
    print("R) Range (eg 2-19)")
    print("S) Specific videos (eg 1,4,6)")
    while True:
        choice = prompt("Pick E, R or S : ").strip().upper()
        if choice == "E":
            close_section()
            return ("E",)
        elif choice == "R":
            raw = prompt("Enter range eg 2-19 : ")
            parsed = parse_range(raw)
            while parsed is None or (count and parsed[1] > count):
                print(f"Enter a valid range within 1-{count}." if count else "Invalid range. Use a range like 2-19.")
                parsed = parse_range(prompt("Enter range eg 2-19 : "))
            close_section()
            print(f"Selected {parsed[1] - parsed[0] + 1} entries.")
            return ("R", parsed[0], parsed[1])
        elif choice == "S":
            raw = prompt("Enter items eg 1,4,6 : ")
            items = parse_items(raw)
            while items is None or (count and any(int(item) > count for item in items.split(","))):
                print(f"Choose entries within 1-{count}." if count else "Use a list like 1,4,6.")
                items = parse_items(prompt("Enter items eg 1,4,6 : "))
            close_section()
            selected = dict.fromkeys(items.split(","))
            print(f"Selected {len(selected)} entries.")
            return ("S", ",".join(selected))
        print("Invalid Selection. Try again")


def downloader(ID, url, sub_mode="none", sub_args=None, base_dir=None, scope=None):
    if scope is None:
        scope = plan_scope()
    return _download_with_template(
        ID, url, _scope_to_args(scope), sub_mode=sub_mode, sub_args=sub_args, base_dir=base_dir
    )
