from vidphen.downloadSelect.runner import ask_base_dir, build_video_template, run_yt_dlp_capture

def _as_tuple(ID, extra_args=None):
    if isinstance(ID, tuple):
        return ID[0], list(ID[1] or [])
    return ID, list(extra_args or [])

def downloader(ID, url, extra_args=None, sub_mode="none", sub_args=None, base_dir=None):
    """Download one video. Returns (returncode|None, files[])."""
    ID, extra = _as_tuple(ID, extra_args)
    if ID == "bestaudio" and not extra:
        extra = ["--extract-audio", "--audio-format", "mp3"]
    sub_args = list(sub_args or [])
    if base_dir is None:
        base_dir = ask_base_dir()
    download_template = build_video_template(base_dir)
    common = ["--no-overwrites", "--continue", "--windows-filenames"]
    if sub_mode == "only":
        return run_yt_dlp_capture(['--write-subs', '--skip-download'] + sub_args + ["-o", download_template] + common + [url])
    sub_flags = (['--write-subs'] + sub_args) if sub_mode == "with" else []
    return run_yt_dlp_capture(['-f', ID, "-o", download_template] + common + extra + sub_flags + [url])
