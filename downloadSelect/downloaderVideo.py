from downloadSelect.runner import ask_base_dir, build_video_template, run_yt_dlp

def downloader(ID,url) :
    base_dir = ask_base_dir()
    download_template = build_video_template(base_dir)
    run_yt_dlp(['-f', ID, "-o", download_template, url])
