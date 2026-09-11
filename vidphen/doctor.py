"""Startup dependency check: Python, yt-dlp, ffmpeg.

Explains what's missing and what breaks, then offers install
instructions or automatic install. Never crashes on missing tools.
"""

import shutil
import subprocess
import sys

MIN_PYTHON = (3, 9)
MIN_YTDLP = (2023, 0, 0)


def _parse_version(text):
    """'2026.8.19' -> (2026, 8, 19). None if unparseable."""
    import re as _re
    m = _re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", str(text))
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)), int(m.group(3) or 0))


def check_python():
    """Returns (ok, current_str, required_str)."""
    current = sys.version_info[:3]
    current_s = ".".join(str(p) for p in current)
    required_s = ".".join(str(p) for p in MIN_PYTHON)
    return (current >= MIN_PYTHON, current_s, required_s)


def check_tool(name, version_flag="--version"):
    """Returns (found, version_str_or_None)."""
    if shutil.which(name) is None:
        return (False, None)
    try:
        result = subprocess.run([name, version_flag], capture_output=True, text=True)
        first = (result.stdout or result.stderr or "").strip().splitlines()
        return (True, first[0].strip() if first else "unknown version")
    except OSError:
        return (False, None)


def instructions_for(tool):
    """Install instructions for this OS. Pure (testable)."""
    if tool == "yt-dlp":
        return ["pip install -U yt-dlp", "then restart vidphen"]
    if tool == "ffmpeg":
        if sys.platform == "win32":
            return ["winget install Gyan.FFmpeg", "then open a NEW terminal and restart vidphen"]
        elif sys.platform == "darwin":
            return ["brew install ffmpeg", "then restart vidphen"]
        else:
            return ["sudo apt install ffmpeg", "then restart vidphen"]
    if tool == "python":
        return ["Download from https://www.python.org/downloads/",
                "then restart vidphen"]
    return []


def auto_install(tool):
    """Try installing. Returns True on success. Always called after asking."""
    try:
        if tool == "yt-dlp":
            result = subprocess.run([sys.executable, "-m", "pip", "install", "-U", "yt-dlp"])
            return result.returncode == 0
        if tool == "ffmpeg":
            if sys.platform == "win32":
                result = subprocess.run(["winget", "install", "Gyan.FFmpeg"])
            elif sys.platform == "darwin":
                result = subprocess.run(["brew", "install", "ffmpeg"])
            else:
                result = subprocess.run(["sudo", "apt", "install", "-y", "ffmpeg"])
            return result.returncode == 0
    except FileNotFoundError:
        return False
    return False


def _status_line(name, ok, detail):
    mark = "\u2713" if ok else "\u2717"
    return f"{name} {detail} {mark}" if detail else f"{name} {mark}"


def run_doctor():
    """Startup gate. Returns True to continue (exits only on user quit)."""
    from vidphen.contentSelect.ui import close_section, open_section, prompt
    py_ok, py_cur, py_req = check_python()
    yt_ok, yt_ver = check_tool("yt-dlp")
    ff_ok, ff_ver = check_tool("ffmpeg")
    yt_new_enough = yt_ok and (_parse_version(yt_ver) or (0,)) >= MIN_YTDLP

    open_section()
    print(f"Python {py_cur} {'ok' if py_ok else 'TOO OLD (need ' + py_req + '+)'}")
    if yt_ok:
        print(f"yt-dlp {yt_ver or ''} {'ok' if yt_new_enough else 'TOO OLD (need 2023.0.0+)'}")
    else:
        print("yt-dlp NOT FOUND - nothing can download without it")
    if ff_ok:
        print(f"ffmpeg {ff_ver or ''} ok")
    else:
        print("ffmpeg NOT FOUND - MP3 convert and video+audio merge won't work")
    close_section()

    if not py_ok:
        print("Your Python is too old for vidphen.")
        for line in instructions_for("python"):
            print(f"  {line}")
        raise SystemExit(1)

    if not yt_ok or not yt_new_enough:
        _resolve("yt-dlp", blocking=True)
    if not ff_ok:
        _resolve("ffmpeg", blocking=False)
    return True


def _resolve(tool, blocking):
    from vidphen.contentSelect.ui import prompt
    if tool == "yt-dlp":
        print("Without yt-dlp, no video, playlist, audio or subtitle can download.")
    else:
        print("Without ffmpeg: MP3/M4A/OPUS/WAV/FLAC convert and 1080p+ merging fail.")
        print("Best single-file and original-audio still work.")
    while True:
        print("1) Show me how to install it")
        print("2) Install it automatically for me")
        print("3) Quit" if blocking else "3) Continue anyway (limited)")
        choice = prompt("Pick 1-3 : ").strip()
        if choice == "1":
            for line in instructions_for(tool):
                print(f"  {line}")
            continue
        elif choice == "2":
            print(f"Installing {tool}...")
            if auto_install(tool):
                print(f"{tool} installed. Re-checking...")
                return
            print(f"Auto-install failed. Try option 1 instead.")
            continue
        elif choice == "3":
            if blocking:
                print("Bye!")
                raise SystemExit(0)
            print("Continuing with limits.")
            return
        print("Invalid Selection. Try again")
