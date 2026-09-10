import subprocess,pathlib
from configSelect.config import default_location

def downloader(ID,url) :

    # Download Location Selection
    while True:
        download_location = input("Download to Default Location (y/n) : ").upper()
        if download_location == "Y" :
            downloadPath = default_location()
            download_template = f'{downloadPath}/%(title)s.%(ext)s'
            try:
                result = subprocess.run(['yt-dlp', '-f', ID, "-o", download_template, url], text=True, capture_output=True)
            except FileNotFoundError:
                print("yt-dlp command not found. Install it with: pip install yt-dlp")
                return
            break
        elif download_location == "N" :
            raw = input("Enter file location eg C:/Users/... : ").strip().strip('"')
            downloadPath = pathlib.Path(raw).expanduser()
            downloadPath.mkdir(parents=True, exist_ok=True)
            download_template = f'{downloadPath}/%(title)s.%(ext)s'
            try:
                result = subprocess.run(["yt-dlp", "-f", ID, "-o", download_template, url], text=True, capture_output=True)
            except FileNotFoundError:
                print("yt-dlp command not found. Install it with: pip install yt-dlp")
                return
            break
        else: print("Invalid Selection.Try again")

    # For checking if download was successful    
    if result.returncode == 0 :
        print("Download Completed")
    else:
        print("Download failed")
        print(result.stderr)
