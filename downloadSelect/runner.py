import pathlib
import shutil
import subprocess

from configSelect.config import default_location

PLAYLIST_SUBFOLDER = "%(playlist_title)s/%(playlist_index)s - %(title)s.%(ext)s"


def ensure_yt_dlp():
    """Return True if yt-dlp is available, else print help and return False."""
    if shutil.which("yt-dlp") is None:
        print("yt-dlp command not found. Install it with: pip install yt-dlp")
        return False
    return True


def ask_base_dir():
    """Prompt Default (y/n) and return a base directory path string."""
    while True:
        choice = input("Download to Default Location (y/n) : ").upper()
        if choice == "Y":
            return default_location()
        elif choice == "N":
            raw = input("Enter file location eg C:/Users/... : ").strip().strip('"')
            path = pathlib.Path(raw).expanduser()
            path.mkdir(parents=True, exist_ok=True)
            return str(path)
        else:
            print("Invalid Selection.Try again")


def build_video_template(base_dir):
    return f'{base_dir}/%(title)s.%(ext)s'


def build_playlist_template(base_dir):
    base = str(base_dir).rstrip("/\\")
    return f'{base}/{PLAYLIST_SUBFOLDER}'


def run_yt_dlp(args):
    """Run yt-dlp with streaming output so progress is visible. Returns returncode or None."""
    if not ensure_yt_dlp():
        return None
    try:
        result = subprocess.run(['yt-dlp'] + args, text=True)
    except FileNotFoundError:
        print("yt-dlp command not found. Install it with: pip install yt-dlp")
        return None
    if result.returncode == 0:
        print("Download Completed")
    else:
        print("Download failed")
    return result.returncode
