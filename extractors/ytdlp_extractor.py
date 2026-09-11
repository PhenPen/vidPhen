import subprocess

from contentSelect.tableShort import table_short
from downloadSelect.runner import run_yt_dlp
from extractors.base import Extractor


class YtDlpExtractor(Extractor):
    """Current engine: thin wrapper over yt-dlp CLI.

    Later: add `InnentubeExtractor(Extractor)` with pure requests,
    UI code stays unchanged.
    """

    def list_formats(self, url):
        return table_short(url)

    def list_subs(self, url):
        try:
            result = subprocess.run(['yt-dlp', '--list-subs', url], capture_output=True, text=True)
        except FileNotFoundError:
            print("yt-dlp command not found. Install it with: pip install yt-dlp")
            return None
        print(result.stdout)
        return result.stdout

    def download(self, url, format_id, output_template, extra_args=None):
        args = ['-f', format_id, "-o", output_template] + list(extra_args or []) + [url]
        return run_yt_dlp(args)

    def fetch_metadata(self, url):
        try:
            result = subprocess.run(
                ['yt-dlp', '--skip-download', '--print', '%(title)s|%(uploader)s|%(duration)s|%(webpage_url)s', url],
                capture_output=True, text=True)
        except FileNotFoundError:
            print("yt-dlp command not found. Install it with: pip install yt-dlp")
            return None
        if result.returncode != 0:
            return None
        line = (result.stdout or "").strip().splitlines()
        if not line:
            return None
        parts = line[0].split("|")
        return {
            "title": parts[0] if len(parts) > 0 else "",
            "uploader": parts[1] if len(parts) > 1 else "",
            "duration": parts[2] if len(parts) > 2 else "",
            "url": parts[3] if len(parts) > 3 else url,
        }


def get_extractor(name="ytdlp"):
    if name == "ytdlp":
        return YtDlpExtractor()
    raise ValueError(f"Unknown extractor: {name}")
