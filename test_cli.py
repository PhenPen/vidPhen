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

        metadata = CompletedProcess([], 0, '{"automatic_captions": {"es": []}}', '')
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
        inputs = ["3", "1", *urls, "", "", "y", "4"]
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


class InspectionTests(unittest.TestCase):
    def test_preview_formats_and_captions_share_one_process(self):
        import json
        from subprocess import CompletedProcess
        from vidphen.contentSelect import quality
        from vidphen.metaDataSelect.metaData import fetch, inspect_video
        from vidphen.subtitleSelect import sub_langs

        self.addCleanup(inspect_video.cache_clear)
        url = "https://example.com/structured"
        fixture = {
            "title": "A title | with a separator", "duration": 42, "language": "es",
            "formats": [{"height": 720, "vcodec": "avc1", "acodec": "aac"}],
            "subtitles": {"es": []},
        }
        with patch("subprocess.run", return_value=CompletedProcess([], 0, json.dumps(fixture), "")) as run:
            self.assertEqual(fetch(url, quiet=True)["title"], fixture["title"])
            self.assertEqual(quality.get_available(url)["heights"], [720])
            self.assertEqual(sub_langs.get_sub_langs(url)["manual"], ["es"])
            self.assertEqual(sub_langs.video_language(url), "es")
        self.assertEqual(run.call_count, 1)

    def test_playlist_title_and_entries_share_one_process(self):
        from subprocess import CompletedProcess
        from vidphen.metaDataSelect.metaData import fetch_playlist

        fixture = '{"title":"Course","entries":[{"url":"https://example.com/clip"},null]}'
        with patch("subprocess.run", return_value=CompletedProcess([], 0, fixture, "")) as run:
            playlist = fetch_playlist("https://example.com/course", quiet=True)
        self.assertEqual((playlist["title"], playlist["count"]), ("Course", 2))
        self.assertEqual(playlist["entries"][1]["index"], 2)
        self.assertIn("--flat-playlist", run.call_args.args[0])
        self.assertEqual(run.call_count, 1)


class BackgroundPreviewTests(unittest.TestCase):
    def test_lookup_starts_while_next_prompt_is_open(self):
        from threading import Event

        started = Event()
        release = Event()
        calls = iter(["https://example.com/one,https://example.com/two", "https://example.com/one", ""])

        def fetch(url, quiet):
            started.set()
            self.assertTrue(release.wait(2))
            return {"title": url, "duration": 1}

        def prompt(_):
            answer = next(calls)
            if answer == "https://example.com/one":
                self.assertTrue(started.wait(2))
                release.set()
            return answer

        with patch.object(cli.ui, "prompt", side_effect=prompt), patch.object(cli, "fetch", side_effect=fetch) as inspect, redirect_stdout(io.StringIO()):
            previews = cli._collect_previews("video")
        self.assertEqual([url for url, _ in previews], ["https://example.com/one", "https://example.com/two"])
        self.assertEqual(inspect.call_count, 2)


class SubtitleAvailabilityTests(unittest.TestCase):
    def test_known_missing_subtitles_do_not_ask_to_download(self):
        video = {"title": "Silent clip", "subtitles": [], "automatic_captions": []}
        with patch.object(cli, "_collect_previews", return_value=[("https://example.com/silent", video)]), \
                patch.object(cli.ui, "prompt") as prompt, redirect_stdout(io.StringIO()) as output:
            self.assertTrue(cli._handle_subtitles_videos())
        prompt.assert_not_called()
        self.assertIn("No subtitles available: Silent clip", output.getvalue())

    def test_playlist_checks_only_selected_entries_and_reports_unknowns(self):
        entries = [{"index": i, "url": str(i)} for i in range(1, 5)]
        subtitles = {
            "1": {"manual": [], "auto": [], "unknown": False},
            "2": {"manual": [], "auto": ["es"], "unknown": False},
            "3": {"manual": [], "auto": [], "unknown": True},
        }
        args = ["--sub-langs", "es", "--write-automatic-subs"]
        with patch.object(cli, "get_sub_langs", side_effect=subtitles.__getitem__) as lookup, redirect_stdout(io.StringIO()) as output:
            self.assertTrue(cli._check_playlist_subtitles({"entries": entries}, ("R", 1, 3), args))
        self.assertEqual({call.args[0] for call in lookup.call_args_list}, {"1", "2", "3"})
        self.assertIn("1 available, 1 unavailable, 1 unverified", output.getvalue())
