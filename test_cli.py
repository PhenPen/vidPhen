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
        self.assertIn("--no-abort-on-error", args)
        self.assertNotIn("-f", args)


class FormatTests(unittest.TestCase):
    def test_ffmpeg_check_ignores_plus_in_url(self):
        from vidphen.downloadSelect import runner

        args = ["--skip-download", "https://example.com/watch?a+b"]
        self.assertFalse(runner.needs_ffmpeg(args))
        self.assertTrue(runner.needs_ffmpeg(["-f", "247+250", args[-1]]))
        self.assertTrue(runner.needs_ffmpeg(["--extract-audio", args[-1]]))

    def test_missing_ffmpeg_fallback_keeps_resolution_cap(self):
        from vidphen.contentSelect.quality import get_format
        from vidphen.downloadSelect import runner

        with redirect_stdout(io.StringIO()):
            args = runner._without_merges(["-f", get_format("4"), "https://example.com/video"])
        self.assertIsNotNone(args)
        self.assertTrue(all("height<=1080" in choice for choice in args[1].split("/")))
        self.assertIsNone(runner._without_merges(["-f", "247+250"]))


class ResultTests(unittest.TestCase):
    def test_partial_playlist_keeps_files_and_empty_success_is_visible(self):
        results = []
        cli._record_result(results, "Playlist", 1, ["first.mp4"])
        cli._record_result(results, "Missing captions", 0, [], subtitles_only=True)
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(cli._show_results(results), ["first.mp4"])
        self.assertIn("Partial download (1 file) | Playlist", output.getvalue())
        self.assertIn("No subtitle file found | Missing captions", output.getvalue())

    def test_only_explicit_paths_count_as_results(self):
        import json
        import tempfile
        from pathlib import Path
        from vidphen.downloadSelect import runner

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "video.es.vtt"
            path.touch()
            metadata = json.dumps({"es": {"filepath": str(path)}})
            self.assertEqual(runner._collect_file_line(f"VIDPHEN_SUBS:{metadata}"), [str(path.resolve())])
            self.assertEqual(runner._collect_file_line(str(path)), [])


class NavigationTests(unittest.TestCase):
    def test_one_paste_prompt_and_back_return_to_main_menu(self):
        output = io.StringIO()
        with patch("builtins.input", side_effect=["1", ":back", "5"]), redirect_stdout(output):
            cli.main()
        self.assertEqual(output.getvalue().count("What do you want to do?"), 2)
        self.assertNotIn("How many", output.getvalue())

    def test_batch_defaults_to_shared_settings(self):
        with patch.object(cli.ui, "prompt", return_value=""):
            self.assertFalse(cli._customize_batch())


class TerminalRenderingTests(unittest.TestCase):
    def test_narrow_styled_preview_renders_long_title(self):
        from rich.console import Console
        from vidphen.contentSelect import ui

        output = io.StringIO()
        console = Console(file=output, width=32, force_terminal=True, color_system=None, _environ={})
        with patch.object(ui, "console", console), patch.object(ui, "styled", return_value=True):
            ui.show_table("Video preview", ("#", "Video", "Duration"), [("1", "A long title " * 10, "1m")])
        self.assertIn("A long title", output.getvalue())
        self.assertLessEqual(max(map(len, output.getvalue().splitlines())), 32)

    def test_redirected_output_has_plain_text(self):
        from vidphen.contentSelect import ui

        with patch.object(ui, "styled", return_value=False), redirect_stdout(io.StringIO()) as output:
            ui.banner("1.0")
            ui.show_table("Results", ("Status", "Name"), [("Saved", "A video")])
        self.assertEqual(output.getvalue(), "VidPhen  v1.0\nResults\n  Saved | A video\n")


class BatchedMenuTests(unittest.TestCase):
    def test_mixed_video_batch_can_return_success_and_failure(self):
        first, second = "https://example.com/first", "https://example.com/second"
        inputs = ["1", first, first, "invalid", second, "", "y", "", "4"]
        output = io.StringIO()
        with patch("builtins.input", side_effect=inputs), redirect_stdout(output), \
                patch.object(cli, "fetch", return_value=None), \
                patch.object(cli.video, "video", return_value="best"), \
                patch.object(cli, "plan_subs", return_value=("none", [])), \
                patch.object(cli, "ask_base_dir", return_value="downloads"), \
                patch.object(downloaderVideo, "downloader", side_effect=[(0, ["first.mp4"]), (1, [])]) as run:
            cli.main()
        self.assertEqual([call.args[1] for call in run.call_args_list], [first, second])
        self.assertIn("Skipped duplicate link", output.getvalue())
        self.assertIn("1 file available", output.getvalue())
        self.assertIn(f"Failed | {second}", output.getvalue())

    def test_full_playlist_with_partial_results(self):
        url = "https://www.youtube.com/playlist?list=playlist"
        inputs = ["2", url, "", "y", " E ", "4"]
        output = io.StringIO()
        with patch("builtins.input", side_effect=inputs), redirect_stdout(output), \
                patch.object(cli, "fetch_playlist", return_value={"title": "Course", "count": 2}), \
                patch.object(cli.playlist, "playlist", return_value="best"), \
                patch.object(cli, "plan_subs", return_value=("none", [])), \
                patch.object(cli, "ask_base_dir", return_value="downloads"), \
                patch.object(downloaderPlaylist, "run_yt_dlp_capture", return_value=(1, ["first.mp4"])) as run:
            cli.main()
        self.assertNotIn("--playlist-end", run.call_args.args[0])
        self.assertIn("Partial download (1 file) | Course", output.getvalue())

    def test_subtitle_batch_reports_files_and_missing_language(self):
        urls = [f"https://example.com/{kind}" for kind in ("manual", "auto", "missing")]
        inputs = ["3", "1", *urls, "", "y", "", "4"]
        output = io.StringIO()
        with patch("builtins.input", side_effect=inputs), redirect_stdout(output), \
                patch.object(cli, "fetch", return_value=None), \
                patch.object(cli, "plan_subs_only", return_value=("only", ["--sub-langs", "es", "--write-automatic-subs"])), \
                patch.object(cli, "ask_base_dir", return_value="downloads"), \
                patch.object(downloaderVideo, "run_yt_dlp_capture", side_effect=[(0, ["manual.es.vtt"]), (0, ["auto.es.vtt"]), (0, [])]) as run:
            cli.main()
        self.assertEqual(run.call_count, 3)
        self.assertTrue(all("--skip-download" in call.args[0] for call in run.call_args_list))
        self.assertIn("2 files available", output.getvalue())
        self.assertIn(f"No subtitle file found | {urls[-1]}", output.getvalue())
