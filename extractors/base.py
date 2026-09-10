from abc import ABC, abstractmethod


class Extractor(ABC):
    """Seam for swapping yt-dlp with a future custom Innertube extractor.

    UI layers (contentSelect/downloadSelect) should depend on this,
    never on `os.system` / raw `yt-dlp` CLI strings.
    """

    @abstractmethod
    def list_formats(self, url):
        """Return stdout of format listing, or None on failure."""
        raise NotImplementedError

    @abstractmethod
    def list_subs(self, url):
        """Return stdout of subtitle listing, or None on failure."""
        raise NotImplementedError

    @abstractmethod
    def download(self, url, format_id, output_template, extra_args=None):
        """Download url with format_id. Returns returncode or None."""
        raise NotImplementedError

    @abstractmethod
    def fetch_metadata(self, url):
        """Return dict with title/uploader/duration or None."""
        raise NotImplementedError
