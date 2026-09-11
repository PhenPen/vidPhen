import subprocess
from vidphen.configSelect.config import default_location
from vidphen.contentSelect.ui import prompt
from vidphen.subtitleSelect.sub_langs import lang_args_for_choice, show_lang_menu


def _download_template():
    # Lazy-load so importing this module never prompts for input.
    return f'{default_location()}/%(title)s.%(ext)s'

def subs(url) :
    while True:
        subs_Select_input = prompt("Do you want subtitles (y/n) : ").upper()
        if subs_Select_input == "Y" :
            print("Selected Subtitles")
            subs_Lang_Select(url)
            break
        elif subs_Select_input == "N" :
            print("Selected no Subtitles")
            break
        else:
            print("Invalid selection.Try again")


def subs_Lang_Select(url) :
    show_lang_menu()
    while True :
        subs_selection = prompt("Pick 1-6 : ").strip()
        if subs_selection == "6":
            lang = prompt("Enter language code eg en,fr,es : ").strip()
            args = lang_args_for_choice("6", lang)
            if args is None:
                print("Invalid Selection. Try again")
                continue
        else:
            args = lang_args_for_choice(subs_selection)
            if args is None:
                print("Invalid Selection. Try again")
                continue
        try:
            result = subprocess.run(['yt-dlp', '--write-subs', '--skip-download'] + args + ['-o', _download_template(), url])
            if result.returncode != 0:
                print("Subtitle download failed. Video may have no subtitles.")
        except FileNotFoundError:
            print("yt-dlp command not found. Install it with: pip install yt-dlp")
        from contentSelect.ui import close_section
        close_section()
        break


