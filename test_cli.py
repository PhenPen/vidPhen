import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from vidphen import cli
from vidphen.downloadSelect import downloaderPlaylist, downloaderVideo


class LinkIntentTests(unittest.TestCase):
    def test_watch_link_in_playlist_follows_selected_mode(self):
        url = "https://www.youtube.com/watch?v=video&list=playlist"
        with patch.object(downloaderVideo, "run_yt_dlp_capture") as video:
            downloaderVideo.downloader("best", url, base_dir="downloads")
        with patch.object(downloaderPlaylist, "run_yt_dlp_capture") as playlist:
            downloaderPlaylist.downloader("best", url, base_dir="downloads", scope=("E",))
        self.assertEqual(cli._filter_link_kind([url], "video"), [url])
        self.assertEqual(cli._filter_link_kind([url], "playlist"), [url])
        self.assertIn("--no-playlist", video.call_args.args[0])
        self.assertIn("--yes-playlist", playlist.call_args.args[0])

    def test_wrong_youtube_link_kind_is_skipped(self):
        playlist = "https://www.youtube.com/playlist?list=playlist"
        video = "https://youtu.be/video"
        with redirect_stdout(io.StringIO()):
            self.assertEqual(cli._filter_link_kind([playlist, video], "video"), [video])
            self.assertEqual(cli._filter_link_kind([video, playlist], "playlist"), [playlist])
