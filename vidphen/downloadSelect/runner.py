import pathlib
import re
import shutil
import subprocess

_ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")

from vidphen.configSelect.config import default_location
from vidphen.contentSelect.ui import prompt

PLAYLIST_SUBFOLDER = "%(playlist_title)s/%(playlist_index)s - %(title)s.%(ext)s"

# Offered once per app run so batches don't nag per video.
_UPDATE_OFFERED = False


def ensure_yt_dlp():
    """Return True if yt-dlp is available, else print help and return False."""
    if shutil.which("yt-dlp") is None:
        print("yt-dlp command not found. Install it with: pip install yt-dlp")
        return False
    return True


def ensure_ffmpeg():
    """Return True if ffmpeg is available, else print help and return False."""
    if shutil.which("ffmpeg") is None:
        print("ffmpeg not found. MP3 convert and video+audio merge need it.")
        print("Install: winget install ffmpeg  OR  https://ffmpeg.org/download.html")
        print("Tip: pick 1) Best or 10) Audio original which often work without convert.")
        return False
    return True


def needs_ffmpeg(args):
    """Detect merge (247+250 / bv*+ba) or --extract-audio in yt-dlp args."""
    text = " ".join(args)
    return ("--extract-audio" in args) or ("+" in text)


def ask_base_dir():
    """Prompt Default once or Custom folder. Change-default lives in Settings."""
    try:
        from vidphen.configSelect.config import _load_config
        current = _load_config()
    except Exception:
        current = None
    if current:
        print(f"Saved folder: {current}")
    while True:
        choice = prompt("Save to Default (D) or Custom once (C)? : ").upper()
        if choice in ("D", "Y"):
            return default_location()
        elif choice in ("C", "N"):
            raw = prompt("Enter file location eg C:/Users/... : ").strip().strip('"')
            path = pathlib.Path(raw).expanduser()
            path.mkdir(parents=True, exist_ok=True)
            return str(path)
        else:
            print("Invalid Selection. Try again")


def build_video_template(base_dir):
    return f'{base_dir}/%(title)s.%(ext)s'


def build_playlist_template(base_dir):
    base = str(base_dir).rstrip("/\\")
    return f'{base}/{PLAYLIST_SUBFOLDER}'


def _collect_file_line(line, base_dir=None):
    """yt-dlp --print filepath line -> absolute path or None. Pure.

    Tolerates ANSI colours, surrounding quotes, and `\\\\?\\`-prefixed
    Windows paths. Relative prints resolve against base_dir/cwd.
    """
    text = _ANSI_RE.sub("", line or "").strip().strip('"').strip("'").strip()
    if text.startswith("\\\\?\\"):
        text = text[4:]
    if not text or text.startswith("["):
        return None
    try:
        p = pathlib.Path(text).expanduser()
    except Exception:
        return None
    try:
        if not p.is_absolute() and base_dir:
            cand = pathlib.Path(str(base_dir)).expanduser() / p
            if cand.is_file():
                return str(cand.resolve())
        if p.is_file():
            return str(p.resolve())
    except OSError:
        return None
    return None


def _looks_like_url(s):
    s = str(s)
    return bool(s) and not s.startswith("-") and ("." in s)


def _print_args(args):
    """Insert filepath prints BEFORE the trailing URL so yt-dlp emits them.

    Appending `--print` after the URL applies to "the next URL" (none)
    on some versions, yielding rc 0 with zero captured paths. Both
    `after_move:filepath` (media) and `filepath` (subs-only
    `--skip-download`) are requested.
    """
    full = list(args)
    if "--print" in full:
        return full
    prints = ["--print", "after_move:filepath", "--print", "filepath"]
    if full and _looks_like_url(full[-1]):
        return full[:-1] + prints + full[-1:]
    return full + prints


def _offer_update_and_retry(args, _run):
    """Stale yt-dlp is the top cause of sudden failures. Offer update + one retry."""
    import sys
    global _UPDATE_OFFERED
    _UPDATE_OFFERED = True
    print("This can also mean an outdated yt-dlp (sites change often).")
    while True:
        choice = prompt("Update yt-dlp now and retry this download? (y/n) : ").strip().upper()
        if choice == "N":
            return None
        elif choice == "Y":
            break
        print("Invalid Selection. Try again")
    print("Updating yt-dlp...")
    try:
        updated = subprocess.run([sys.executable, "-m", "pip", "install", "-U", "yt-dlp"])
    except FileNotFoundError:
        print("Update failed. Try: pip install -U yt-dlp")
        return None
    if updated.returncode != 0:
        print("Update failed. Try: pip install -U yt-dlp")
        return None
    print("Updated. Retrying once...")
    try:
        rc, files = _run(_print_args(args))
    except FileNotFoundError:
        print("yt-dlp command not found after update.")
        return None
    if rc == 0:
        print("Download Completed")
    else:
        print("Still failing after update - see causes above.")
    return (rc, files)


def _run_capture(args):
    """Popen tee: stream yt-dlp output live, collect after_move filepaths."""
    proc = subprocess.Popen(['yt-dlp'] + args, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1)
    files, seen = [], set()
    for line in proc.stdout:
        print(line, end="")
        found = _collect_file_line(line)
        if found and found not in seen:
            seen.add(found)
            files.append(found)
    proc.wait()
    return (proc.returncode, files)


def run_yt_dlp_capture(args):
    """Run yt-dlp, stream progress, return (returncode|None, files[])."""
    if not ensure_yt_dlp():
        return (None, [])
    if needs_ffmpeg(args) and not ensure_ffmpeg():
        print("Stopped before download so you don't get a broken file.")
        return (None, [])
    try:
        rc, files = _run_capture(_print_args(args))
    except FileNotFoundError:
        print("yt-dlp command not found. Install it with: pip install yt-dlp")
        return (None, [])
    if rc == 0:
        print("Download Completed")
    else:
        print("Download failed. Common causes:")
        print("- Private / age-restricted / login-required video")
        print("- No internet or the site blocked the request (try again)")
        print("- File already exists and --no-overwrites skipped it (check folder)")
        print("- Picked format not available (try 1) Best)")
        if not _UPDATE_OFFERED:
            retried = _offer_update_and_retry(args, _run_capture)
            if retried is not None:
                return retried
    return (rc, files)


def run_yt_dlp(args):
    """Run yt-dlp with streaming output so progress is visible. Returns returncode or None."""
    rc, _ = run_yt_dlp_capture(args)
    return rc


def open_path(path):
    """Open a file/folder with the OS default app. Never raises. Returns True if launched."""
    import os
    import sys
    try:
        p = pathlib.Path(str(path)).expanduser()
    except Exception:
        print(f"Couldn't open: {path}")
        return False
    if not p.exists():
        print(f"Not found: {p}")
        return False
    try:
        if sys.platform == "win32":
            os.startfile(str(p))
        elif sys.platform == "darwin":
            subprocess.run(["open", str(p)])
        else:
            subprocess.run(["xdg-open", str(p)])
        return True
    except OSError as e:
        print(f"Couldn't open {p}: {e}")
        print(f"Find it at: {p}")
        return False


def open_folder(folder):
    """Open a download folder. Never raises."""
    try:
        p = pathlib.Path(str(folder)).expanduser()
    except Exception:
        print(f"Couldn't open folder: {folder}")
        return False
    if not p.is_dir():
        print(f"Folder not found: {p}")
        return False
    return open_path(p)
