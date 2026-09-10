import subprocess

from configSelect.config import default_location
from contentSelect.validators import parse_items
from downloadSelect.runner import build_playlist_template
from subtitleSelect.sub_langs import lang_args_for_choice, show_lang_menu


def _download_template():
    # Lazy-load so importing never prompts for input.
    return build_playlist_template(default_location())


def _playlist_items_args():
    choice = input("Subtitles for Entire playlist (E) or specific items (S) : ").upper()
    if choice == "S":
        raw = input("Enter playlist items eg 1,4,6 : ").strip()
        items = parse_items(raw)
        if items is None:
            print("Invalid list. Use format eg 1,4,6")
            return None
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
    show_lang_menu()
    while True:
        sel = input("Pick 1-6 : ").strip()
        if sel == "6":
            lang = input("Enter language code eg en,fr,es : ").strip()
            lang_args = lang_args_for_choice("6", lang)
        else:
            lang_args = lang_args_for_choice(sel)
        if lang_args is None:
            print("Invalid Selection. Try again")
            continue
        items_args = _playlist_items_args()
        if items_args is None:
            continue
        try:
            result = subprocess.run(
                ['yt-dlp', '--write-subs', '--skip-download', '--ignore-errors']
                + lang_args + ['-o', _download_template()] + items_args + [url])
            if result.returncode != 0:
                print("Subtitle download failed. Videos may have no subtitles.")
        except FileNotFoundError:
            print("yt-dlp command not found. Install it with: pip install yt-dlp")
        from contentSelect.ui import close_section
        close_section()
        break
