import subprocess

from configSelect.config import default_location
from downloadSelect.runner import build_playlist_template


def _download_template():
    # Lazy-load so importing never prompts for input.
    return build_playlist_template(default_location())


def _playlist_items_args():
    choice = input("Subtitles for Entire playlist (E) or specific items (S) : ").upper()
    if choice == "S":
        items = input("Enter playlist items eg 1,4,6 : ").strip()
        if items:
            return ["--playlist-items", items]
    return []


def subs(url):
    while True:
        subs_select = input("Do you want subtitles (y/n) : ").upper()
        if subs_select == "Y":
            print("Selected Subtitles")
            subs_lang_select(url)
            break
        elif subs_select == "N":
            print("Selected no Subtitles")
            break
        else:
            print("Invalid selection.Try again")


def subs_lang_select(url):
    print()
    print("Do you want default subs or another language")
    while True:
        sel = input("Enter D for default subs and A for another language : ").upper()
        if sel == "D":
            try:
                result = subprocess.run(
                    ['yt-dlp', '--write-subs', '--skip-download', '--ignore-errors',
                     '-o', _download_template()] + _playlist_items_args() + [url])
                if result.returncode != 0:
                    print("Subtitle download failed")
            except FileNotFoundError:
                print("yt-dlp command not found. Install it with: pip install yt-dlp")
            break
        elif sel == "A":
            try:
                subprocess.run(["yt-dlp", "--list-subs", url])
            except FileNotFoundError:
                print("yt-dlp command not found. Install it with: pip install yt-dlp")
                break
            lang = input("Enter language from options above in format eg en,fr,es,..").strip()
            try:
                result = subprocess.run(
                    ["yt-dlp", "--write-subs", "--skip-download", "--sub-langs", lang,
                     '--ignore-errors', "-o", _download_template()] + _playlist_items_args() + [url])
                if result.returncode != 0:
                    print("Subtitle download failed")
            except FileNotFoundError:
                print("yt-dlp command not found. Install it with: pip install yt-dlp")
            break
        else:
            print("Invalid Selection.Try again")
