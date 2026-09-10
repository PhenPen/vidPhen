# Coming soon - now basic implementation via yt-dlp --print
import subprocess


def fetch(url):
    """Return {title, uploader, duration, url} or None. No download."""
    try:
        result = subprocess.run(
            ['yt-dlp', '--skip-download', '--print',
             '%(title)s|%(uploader)s|%(duration)s|%(webpage_url)s', url],
            capture_output=True, text=True)
    except FileNotFoundError:
        print("yt-dlp command not found. Install it with: pip install yt-dlp")
        return None
    if result.returncode != 0:
        print(result.stderr or "Failed to fetch metadata")
        return None
    lines = (result.stdout or "").strip().splitlines()
    if not lines:
        return None
    parts = lines[0].split("|")
    info = {
        "title": parts[0] if len(parts) > 0 else "",
        "uploader": parts[1] if len(parts) > 1 else "",
        "duration": parts[2] if len(parts) > 2 else "",
        "url": parts[3] if len(parts) > 3 else url,
    }
    print(f"Title: {info['title']}")
    print(f"Uploader: {info['uploader']}")
    print(f"Duration: {info['duration']}s")
    return info


def fetch_playlist(url):
    """Return {title, count, url} for playlists. No download. None on failure."""
    try:
        title_res = subprocess.run(
            ['yt-dlp', '--skip-download', '--flat-playlist', '--print',
             '%(playlist_title)s', '--playlist-items', '1', url],
            capture_output=True, text=True)
        list_res = subprocess.run(
            ['yt-dlp', '--skip-download', '--flat-playlist', '--print',
             '%(title)s', url],
            capture_output=True, text=True)
    except FileNotFoundError:
        print("yt-dlp command not found. Install it with: pip install yt-dlp")
        return None
    if list_res.returncode != 0:
        return None
    videos = [l for l in (list_res.stdout or "").splitlines()
              if l.strip() and not l.strip().startswith("[")]
    title_lines = [l for l in (title_res.stdout or "").splitlines()
                   if l.strip() and not l.strip().startswith("[")]
    title = title_lines[0].strip() if title_lines else "Playlist"
    info = {"title": title, "count": len(videos), "url": url}
    print(f"Playlist: {info['title']}")
    print(f"Videos: {info['count']}")
    return info