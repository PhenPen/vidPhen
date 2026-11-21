import json
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
    """Check conversion and explicit merge selectors."""
    if "--extract-audio" in args:
        return True
    if "-f" not in args:
        return False
    return "+" in args[args.index("-f") + 1]


def _without_merges(args):
    if "--extract-audio" in args or "-f" not in args:
        return None
    index = args.index("-f") + 1
    choices = [choice for choice in args[index].split("/") if "+" not in choice]
    if not choices:
        return None
    print("FFmpeg unavailable. Trying formats that already contain audio and video.")
    return [*args[:index], "/".join(choices), *args[index + 1:]]


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


def _collect_file_line(line):
    """Read explicitly reported paths and verify they exist."""
    source, _, payload = line.strip().partition(":")
    if source not in ("VIDPHEN_FILE", "VIDPHEN_SUBS"):
        return []
    try:
        value = json.loads(payload)
    except ValueError:
        return []
    if source == "VIDPHEN_FILE":
        paths = [value]
    elif isinstance(value, dict):
        paths = [track.get("filepath") for track in value.values() if isinstance(track, dict)]
    else:
        paths = []
    files = []
    for path in paths:
        if not isinstance(path, str):
            continue
        try:
            candidate = pathlib.Path(path)
            if candidate.is_file():
                files.append(str(candidate.resolve()))
        except OSError:
            continue
    return files


def _print_args(args):
    """Ask yt-dlp to report the files from this invocation."""
    prints = ["--no-simulate", "--progress", "--newline"]
    if "--skip-download" not in args:
        prints += ["--print", "after_move:VIDPHEN_FILE:%(filepath)j"]
    if "--write-subs" in args or "--write-automatic-subs" in args:
        prints += ["--print", "before_dl:VIDPHEN_SUBS:%(requested_subtitles)j"]
    return [*prints, *args]


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
    if rc != 0:
        print("Still failing after update - see causes above.")
    return (rc, files)


def _safe_print(line):
    """Print a yt-dlp output line without ever raising on exotic filenames."""
    try:
        print(line, end="")
    except UnicodeEncodeError:
        safe = _ANSI_RE.sub("", line).encode("ascii", "backslashreplace").decode("ascii")
        try:
            print(safe, end="")
        except Exception:
            pass


def _run_capture(args):
    """Popen tee: stream yt-dlp output live, collect printed filepaths.

    yt-dlp emits UTF-8: decode explicitly so a Windows locale never
    kills the run on exotic title characters (eg fullwidth bars).
    """
    proc = subprocess.Popen(['yt-dlp'] + args, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1,
                            encoding="utf-8", errors="replace")
    files = {}
    try:
        with proc.stdout:
            for line in proc.stdout:
                if line.startswith(("VIDPHEN_FILE:", "VIDPHEN_SUBS:")):
                    files.update(dict.fromkeys(_collect_file_line(line)))
                else:
                    _safe_print(line)
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        proc.wait()
        print("\nDownload interrupted. Partial files can be resumed.")
        return (130, list(files))
    return (proc.returncode, list(files))


def run_yt_dlp_capture(args):
    """Run yt-dlp, stream progress, return (returncode|None, files[])."""
    if not ensure_yt_dlp():
        return (None, [])
    if needs_ffmpeg(args) and shutil.which("ffmpeg") is None:
        fallback = _without_merges(args)
        if fallback is None:
            ensure_ffmpeg()
            return (None, [])
        args = fallback
    try:
        rc, files = _run_capture(_print_args(args))
    except FileNotFoundError:
        print("yt-dlp command not found. Install it with: pip install yt-dlp")
        return (None, [])
    if rc == 0 and not files:
        print("No output file was found.")
    elif rc not in (0, 130) and not files:
        print("Download failed. Check the downloader message above.")
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
