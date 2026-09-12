import pathlib
import shutil
import subprocess

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


def _offer_update_and_retry(args):
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
        retried = subprocess.run(['yt-dlp'] + args, text=True)
    except FileNotFoundError:
        print("yt-dlp command not found after update.")
        return None
    if retried.returncode == 0:
        print("Download Completed")
    else:
        print("Still failing after update - see causes above.")
    return retried.returncode


def run_yt_dlp(args):
    """Run yt-dlp with streaming output so progress is visible. Returns returncode or None."""
    if not ensure_yt_dlp():
        return None
    if needs_ffmpeg(args) and not ensure_ffmpeg():
        print("Stopped before download so you don't get a broken file.")
        return None
    try:
        result = subprocess.run(['yt-dlp'] + args, text=True)
    except FileNotFoundError:
        print("yt-dlp command not found. Install it with: pip install yt-dlp")
        return None
    if result.returncode == 0:
        print("Download Completed")
    else:
        print("Download failed. Common causes:")
        print("- Private / age-restricted / login-required video")
        print("- No internet or the site blocked the request (try again)")
        print("- File already exists and --no-overwrites skipped it (check folder)")
        print("- Picked format not available (try 1) Best)")
        if not _UPDATE_OFFERED:
            retried = _offer_update_and_retry(args)
            if retried is not None:
                return retried
    return result.returncode
