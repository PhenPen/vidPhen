import subprocess
from configSelect.config import default_location


def _download_template():
    # Lazy-load so importing this module never prompts for input.
    return f'{default_location()}/%(title)s.%(ext)s'

def subs(url) :
    while True:
        subs_Select_input = input("Do you want subtitles (y/n) : ").upper()
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
    print()
    print("Do you want default subs or another language")
    while True :
        subs_selection = input("Enter D for default subs and A for another language : ").upper()
        if subs_selection == "D" :
            try:
                result = subprocess.run(['yt-dlp', '--write-subs', '--skip-download', '-o', _download_template(), url])
                if result.returncode != 0:
                    print("Subtitle download failed")
            except FileNotFoundError:
                print("yt-dlp command not found. Install it with: pip install yt-dlp")
            break
        elif subs_selection == "A" :
            try:
                subprocess.run(["yt-dlp", "--list-subs", url])
            except FileNotFoundError:
                print("yt-dlp command not found. Install it with: pip install yt-dlp")
                break
            lang = input("Enter language from options above in format eg en,fr,es,..")
            try:
                result = subprocess.run(["yt-dlp", "--write-subs", "--skip-download", "--sub-langs", lang, "-o", _download_template(), url])
                if result.returncode != 0:
                    print("Subtitle download failed")
            except FileNotFoundError:
                print("yt-dlp command not found. Install it with: pip install yt-dlp")
            break
        else :
            print("Invalid Selection.Try again")


