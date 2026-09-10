from contentSelect.validators import parse_range
from downloadSelect.runner import ask_base_dir, build_playlist_template, run_yt_dlp

def _download_with_template(ID, url, extra_args):
    base_dir = ask_base_dir()
    download_template = build_playlist_template(base_dir)
    run_yt_dlp(['-f', ID, "-o", download_template] + extra_args + [url])


def downloader(ID,url) :

    # Selecting index of playlist
    print("Do you want to download everything in the playlist, a particular range of videos or only specific videos")
    print()
    playlistIndexConfirmation = input("Enter E for Everything, R for Range of videos and S for specific videos : ").upper()

    # Downloading based on index selection
    while True:
        if playlistIndexConfirmation == "E" :
            _download_with_template(ID, url, ["--ignore-errors", "--playlist-start", "1", "--playlist-end", "99999", "--no-overwrites", "--windows-filenames"])
            break

        elif playlistIndexConfirmation == "R" :
            print("Range format = Beginning Video Range - Ending Video Range")
            playlistRange = input("Enter the range of video index you want in the Range format eg 2-19 :  ")
            parsed = parse_range(playlistRange)
            if parsed is None:
                print("Invalid range. Use format eg 2-19")
                break
            playlistIndexBegin,playlistIndexEnd = parsed
            _download_with_template(ID, url, ["--ignore-errors", "--playlist-start", str(playlistIndexBegin), "--playlist-end", str(playlistIndexEnd), "--no-overwrites", "--windows-filenames"])
            break

        elif playlistIndexConfirmation == "S" :
            print("Specifics format = 1,4,6,7,9")
            print("If I want to download 5 videos with index 1,4,6,7,9, I would enter it as shown above")
            playlistIndexSpecifics = input("Enter all the index of all videos in the Specifics format eg 2,3,4,5,... :  ")
            _download_with_template(ID, url, ["--ignore-errors", "--playlist-items", playlistIndexSpecifics.strip(), "--no-overwrites", "--windows-filenames"])
            break
        else:
            print("Invalid selection. Try again")
            break