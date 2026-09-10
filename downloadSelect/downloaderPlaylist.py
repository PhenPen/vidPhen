import subprocess,pathlib
from configSelect.config import default_location

def downloader(ID,url) :

    # Sub folder to store playlist videos
    playlistSubFolder = "%(playlist_title)s/%(playlist_index)s - %(title)s.%(ext)s" # Playlist title is used as the folder name, with the index of the video in the playlist coming first and the video title and extension

    # Selecting index of playlist
    print("Do you want to download everything in the playlist, a particular range of videos or only specific videos")
    print()
    playlistIndexConfirmation = input("Enter E for Everything, R for Range of videos and S for specific videos : ").upper()

    # Downloading based on index selection
    while True:
        if playlistIndexConfirmation == "E" :

            # Download Location Selection
            while True:
                download_location = input("Download to Default Location (y/n) : ").upper()
                if download_location == "Y" :
                    downloadPath = default_location()
                    download_template = f'{downloadPath}{playlistSubFolder}'
                    result = subprocess.run(['yt-dlp' ,'-f', ID, "-o", download_template, "--ignore-errors", "--playlist-start", "1", "--playlist-end", "99999", "--no-overwrites", "--windows-filenames", url] ,text=True, capture_output=True)
                    break
                elif download_location == "N" : 
                    downloadPath = pathlib.Path(input("Enter file location eg C:/Users/... : ").strip().strip('"')).expanduser()
                    downloadPath.mkdir(parents=True, exist_ok=True)
                    download_template = f'{downloadPath}/{playlistSubFolder}'
                    result = subprocess.run(["yt-dlp", "-f", ID, "-o", download_template, "--ignore-errors", "--playlist-start", "1", "--playlist-end", "99999", "--no-overwrites", "--windows-filenames", url],text=True, capture_output=True)
                    break 
                else: print("Invalid Selection.Try again")

            # For checking if download was successful    
            if result.returncode == 0 :
                print("Download Completed")
            else:
                print("Download failed")
                print(result.stderr)
            break

        elif playlistIndexConfirmation == "R" :
            print("Range format = Beginning Video Range - Ending Video Range")
            playlistRange = input("Enter the range of video index you want in the Range format eg 2-19 :  ")
            playlistIndexBegin,playlistIndexEnd = playlistRange.split("-")

            # Download Location Selection
            while True:
                download_location = input("Download to Default Location (y/n) : ").upper()
                if download_location == "Y" :
                    downloadPath = default_location()
                    download_template = f'{downloadPath}{playlistSubFolder}'
                    
                    result = subprocess.run(['yt-dlp' ,'-f', ID, "-o", download_template, "--ignore-errors", "--playlist-start", playlistIndexBegin, "--playlist-end", playlistIndexEnd, "--no-overwrites", "--windows-filenames", url] ,text=True, capture_output=True)
                    break
                elif download_location == "N" : 
                    downloadPath = pathlib.Path(input("Enter file location eg C:/Users/... : ").strip().strip('"')).expanduser()
                    downloadPath.mkdir(parents=True, exist_ok=True)
                    download_template = f'{downloadPath}/{playlistSubFolder}'
                    result = subprocess.run(["yt-dlp", "-f", ID, "-o", download_template, "--ignore-errors", "--playlist-start", playlistIndexBegin, "--playlist-end", playlistIndexEnd, "--no-overwrites", "--windows-filenames", url],text=True, capture_output=True)
                    break 
                else: print("Invalid Selection.Try again")

            # For checking if download was successful    
            if result.returncode == 0 :
                print("Download Completed")
            else:
                print("Download failed")
                print(result.stderr)
            break

        elif playlistIndexConfirmation == "S" :
            print("Specifics format = 1,4,6,7,9")
            print("If I want to download 5 videos with index 1,4,6,7,9, I would enter it as shown above")
            playlistIndexSpecifics = input("Enter all the index of all videos in the Specifics format eg 2,3,4,5,... :  ")

            # Download Location Selection
            while True:
                download_location = input("Download to Default Location (y/n) : ").upper()
                if download_location == "Y" :
                    downloadPath = default_location()
                    download_template = f'{downloadPath}{playlistSubFolder}'
                    
                    result = subprocess.run(['yt-dlp' ,'-f', ID, "-o", download_template, "--ignore-errors", "--playlist-items", playlistIndexSpecifics, "--no-overwrites", "--windows-filenames", url] ,text=True, capture_output=True)
                    break
                elif download_location == "N" : 
                    downloadPath = pathlib.Path(input("Enter file location eg C:/Users/... : ").strip().strip('"')).expanduser()
                    downloadPath.mkdir(parents=True, exist_ok=True)
                    download_template = f'{downloadPath}/{playlistSubFolder}'
                    result = subprocess.run(["yt-dlp", "-f", ID, "-o", download_template, "--ignore-errors", "--playlist-items", playlistIndexSpecifics, "--no-overwrites", "--windows-filenames", url],text=True, capture_output=True)
                    break 
                else: print("Invalid Selection.Try again")

            # For checking if download was successful    
            if result.returncode == 0 :
                print("Download Completed")
            else:
                print("Download failed")
                print(result.stderr)
            break
        else:
            print("Invalid selection. Try again")
            break