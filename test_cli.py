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


class BatchLinkTests(unittest.TestCase):
    def test_pasted_links_preserve_url_punctuation_and_report_duplicates(self):
        url = "https://example.com/watch?tags=a,b;c"
        lines = [f"{url},https://example.org/video", f"{url}, invalid", ""]
        output = io.StringIO()
        with patch.object(cli.ui, "prompt", side_effect=lines), redirect_stdout(output):
            good, bad = cli._prompt_url_list("Paste links")
        self.assertEqual(good, [url, "https://example.org/video"])
        self.assertEqual(bad, ["invalid"])
        self.assertIn("Skipped duplicate link:", output.getvalue())


class PlaylistScopeTests(unittest.TestCase):
    def test_invalid_range_can_be_corrected_without_restart(self):
        with patch.object(downloaderPlaylist, "prompt", side_effect=[" R ", "9-2", "1-12", "2-4"]), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(downloaderPlaylist.plan_scope(count=10), ("R", 2, 4))
        self.assertIn("Selected 3 entries", output.getvalue())

    def test_everything_has_no_artificial_item_limit(self):
        with patch.object(downloaderPlaylist, "prompt", return_value=" E "), redirect_stdout(io.StringIO()):
            scope = downloaderPlaylist.plan_scope()
        self.assertEqual(scope, ("E",))
        self.assertNotIn("--playlist-end", downloaderPlaylist._scope_to_args(scope))


class SubtitleTests(unittest.TestCase):
    def test_auto_track_is_detected_when_manual_tracks_are_missing(self):
        from subprocess import CompletedProcess
        from vidphen.subtitleSelect import sub_langs

        metadata = CompletedProcess([], 0, 'manual:NA\nauto:{"es": []}\n', '')
        with patch("subprocess.run", return_value=metadata):
            subs = sub_langs.get_sub_langs("https://example.com/auto-only")
        self.assertEqual(subs, {"manual": [], "auto": ["es"], "unknown": False})
        self.assertEqual(sub_langs.resolve_lang("es", subs), (["es"], True))

    def test_subtitle_playlist_keeps_language_choice_for_all_items(self):
        url = "https://www.youtube.com/playlist?list=playlist"
        with patch.object(downloaderPlaylist, "run_yt_dlp_capture") as download:
            downloaderPlaylist.downloader(
                "best", url, sub_mode="only",
                sub_args=["--sub-langs", "es", "--write-automatic-subs"],
                base_dir="downloads", scope=("E",),
            )
        args = download.call_args.args[0]
        self.assertIn("--skip-download", args)
        self.assertIn("--write-automatic-subs", args)
        self.assertIn("--ignore-errors", args)
        self.assertNotIn("-f", args)
