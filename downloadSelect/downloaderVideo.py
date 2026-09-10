from downloadSelect.runner import ask_base_dir, build_video_template, run_yt_dlp

def _as_tuple(ID, extra_args=None):
    if isinstance(ID, tuple):
        return ID[0], list(ID[1] or [])
    return ID, list(extra_args or [])

def downloader(ID, url, extra_args=None) :
    ID, extra = _as_tuple(ID, extra_args)
    if ID == "bestaudio" and not extra:
        extra = ["--extract-audio", "--audio-format", "mp3"]
    base_dir = ask_base_dir()
    download_template = build_video_template(base_dir)
    common = ["--no-overwrites", "--continue", "--windows-filenames"]
    run_yt_dlp(['-f', ID, "-o", download_template] + common + extra + [url])
