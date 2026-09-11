from contentSelect.ui import prompt
from contentSelect.validators import parse_items, parse_range
from downloadSelect.runner import ask_base_dir, build_playlist_template, run_yt_dlp

def _download_with_template(ID, url, extra_args, audio_extra=None, sub_mode="none", sub_args=None, base_dir=None):
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
        return run_yt_dlp(['--write-subs', '--skip-download', '--ignore-errors']
                     + sub_args + ["-o", download_template] + extra_args + [url])
    sub_flags = (['--write-subs'] + sub_args) if sub_mode == "with" else []
    return run_yt_dlp(['-f', ID, "-o", download_template] + audio_extra + sub_flags + extra_args + [url])


def _scope_to_args(scope):
    """Scope tuple -> yt-dlp playlist args. Scope: ('E',) | ('R', b, e) | ('S', items)."""
    if scope[0] == "E":
        return ["--ignore-errors", "--playlist-start", "1", "--playlist-end", "99999", "--no-overwrites", "--windows-filenames"]
    elif scope[0] == "R":
        return ["--ignore-errors", "--playlist-start", str(scope[1]), "--playlist-end", str(scope[2]), "--no-overwrites", "--windows-filenames"]
    else:
        return ["--ignore-errors", "--playlist-items", scope[1], "--no-overwrites", "--windows-filenames"]


def plan_scope():
    """Ask E/R/S once. Returns scope tuple. Repeats until valid."""
    from contentSelect.ui import close_section, open_section
    open_section()
    print("Which videos in each playlist?")
    print("E) Everything")
    print("R) Range (eg 2-19)")
    print("S) Specific videos (eg 1,4,6)")
    while True:
        choice = prompt("Pick E, R or S : ").upper()
        if choice == "E":
            close_section()
            return ("E",)
        elif choice == "R":
            raw = prompt("Enter range eg 2-19 : ")
            parsed = parse_range(raw)
            if parsed is None:
                print("Invalid range. Use format eg 2-19")
                continue
            close_section()
            return ("R", parsed[0], parsed[1])
        elif choice == "S":
            raw = prompt("Enter items eg 1,4,6 : ")
            items = parse_items(raw)
            if items is None:
                print("Invalid list. Use format eg 1,4,6 with numbers only")
                continue
            close_section()
            return ("S", items)
        print("Invalid Selection. Try again")


def downloader(ID, url, sub_mode="none", sub_args=None, base_dir=None, scope=None) :

    if scope is not None:
        return _download_with_template(ID, url, _scope_to_args(scope), sub_mode=sub_mode, sub_args=sub_args, base_dir=base_dir)

    # Selecting index of playlist
    print("Do you want to download everything in the playlist, a particular range of videos or only specific videos")
    print()
    playlistIndexConfirmation = prompt("Enter E for Everything, R for Range of videos and S for specific videos : ").upper()

    # Downloading based on index selection
    while True:
        if playlistIndexConfirmation == "E" :
            return _download_with_template(ID, url, ["--ignore-errors", "--playlist-start", "1", "--playlist-end", "99999", "--no-overwrites", "--windows-filenames"], sub_mode=sub_mode, sub_args=sub_args, base_dir=base_dir)

        elif playlistIndexConfirmation == "R" :
            print("Range format = Beginning Video Range - Ending Video Range")
            playlistRange = prompt("Enter the range of video index you want in the Range format eg 2-19 :  ")
            parsed = parse_range(playlistRange)
            if parsed is None:
                print("Invalid range. Use format eg 2-19")
                break
            playlistIndexBegin,playlistIndexEnd = parsed
            return _download_with_template(ID, url, ["--ignore-errors", "--playlist-start", str(playlistIndexBegin), "--playlist-end", str(playlistIndexEnd), "--no-overwrites", "--windows-filenames"], sub_mode=sub_mode, sub_args=sub_args, base_dir=base_dir)

        elif playlistIndexConfirmation == "S" :
            print("Specifics format = 1,4,6,7,9")
            print("If I want to download 5 videos with index 1,4,6,7,9, I would enter it as shown above")
            raw_items = prompt("Enter all the index of all videos in the Specifics format eg 2,3,4,5,... :  ")
            playlistIndexSpecifics = parse_items(raw_items)
            if playlistIndexSpecifics is None:
                print("Invalid list. Use format eg 1,4,6 with numbers only")
                break
            _download_with_template(ID, url, ["--ignore-errors", "--playlist-items", playlistIndexSpecifics, "--no-overwrites", "--windows-filenames"], sub_mode=sub_mode, sub_args=sub_args, base_dir=base_dir)
            return
        else:
            print("Invalid selection. Try again")
            break