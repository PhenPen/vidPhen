import subprocess


def table_short(url):
    """Run `yt-dlp -F` and return stdout. Returns None if yt-dlp is missing."""
    try:
        result = subprocess.run(['yt-dlp', '-F', url], capture_output=True, text=True)
    except FileNotFoundError:
        print("yt-dlp command not found. Install it with: pip install yt-dlp")
        return None
    if result.returncode != 0:
        print(result.stderr or "Failed to list formats")
        return None
    print(result.stdout)
    return result.stdout


def parse_formats(table_text):
    """Parse `yt-dlp -F` output into [{id, ext, resolution, note}]. Best-effort."""
    formats = []
    if not table_text:
        return formats
    for line in table_text.splitlines():
        line = line.strip()
        if not line or line.startswith("[") or line.startswith("ID") or line.startswith("-"):
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        formats.append({
            "id": parts[0],
            "ext": parts[1] if len(parts) > 1 else "",
            "resolution": parts[2] if len(parts) > 2 else "",
            "note": " ".join(parts[3:]),
        })
    return formats