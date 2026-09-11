# Automated checks - no network, no prompts. Run: python test.py
from vidphen.contentSelect.quality import ask_fallback_policy  # noqa: F401 (import check)
from vidphen.contentSelect.quality import get_format, picked_height
from vidphen.contentSelect.validators import is_valid_format_id, is_valid_url, parse_items, parse_range, parse_url_list
from vidphen.metaDataSelect.metaData import format_duration
from vidphen.subtitleSelect.sub_langs import lang_args_for_choice
from vidphen.doctor import _parse_version, check_python, instructions_for

failures = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        failures.append(name)


# URLs
check("valid watch url", is_valid_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ"))
check("valid youtu.be url", is_valid_url("https://youtu.be/dQw4w9WgXcQ"))
check("valid playlist url", is_valid_url("https://www.youtube.com/playlist?list=PL123abc"))
check("valid other-site url", is_valid_url("https://vimeo.com/123456789"))
check("valid bare domain url", is_valid_url("vimeo.com/123456789"))
check("reject notaurl", not is_valid_url("notaurl"))
check("reject empty", not is_valid_url(""))
check("reject spaces", not is_valid_url("not a link"))


def _choices():
    g, b = parse_url_list("https://youtu.be/abc123XYZ12, notaurl\nhttps://www.youtube.com/watch?v=dQw4w9WgXcQ")
    return g, b


g, b = _choices()
check("url list splits good/bad", len(g) == 2 and len(b) == 1)
g2, _ = parse_url_list("https://youtu.be/abc123XYZ12, https://youtu.be/abc123XYZ12")
check("url list dedupes", len(g2) == 1)

# Formats / quality presets
check("preset 1 ends with fallback", get_format("1").endswith("/best"))
check("preset 4 targets 1080", "height<=1080" in get_format("4"))
check("preset 9 asks audio", get_format("9") == "AUDIO_ASK")
check("preset 10 original", get_format("10") == "bestaudio/best")
check("preset 11 8K targets 4320", "height<=4320" in get_format("11"))
check("unknown preset None", get_format("99") is None)
check("picked height 1080", picked_height(get_format("4")) == 1080)
check("picked height audio None", picked_height("bestaudio") is None)
check("format id 247+250 valid", is_valid_format_id("247+250"))

# Ranges / items
check("range 2-19", parse_range("2-19") == (2, 19))
check("range bad None", parse_range("bad") is None)
check("items 1,4,6", parse_items("1,4,6") == "1,4,6")
check("items bad None", parse_items("1,,x") is None)

# Duration
check("658s -> 10m 58s", format_duration("658") == "10m 58s")
check("45s", format_duration("45") == "45s")
check("3930 -> 1h 5m 30s", format_duration("3930") == "1h 5m 30s")
check("NA unknown", format_duration("NA") == "unknown")

# Subtitle langs
check("lang 1 en", lang_args_for_choice("1") == ["--sub-langs", "en"])
check("lang 5 auto", lang_args_for_choice("5") == [])
check("lang bad None", lang_args_for_choice("9") is None)

# Imports with no prompt on import (would hang waiting for input if broken)
import vidphen.contentSelect.ui  # noqa: F401
import vidphen.doctor  # noqa: F401
import vidphen.downloadSelect.runner  # noqa: F401
check("imports need no input", True)

# Doctor helpers (pure, no system changes)
check("parse version 2026.8.19", _parse_version("yt-dlp 2026.8.19") == (2026, 8, 19))
check("parse version bad None", _parse_version("no version here") is None)
py_ok, py_cur, py_req = check_python()
check("python check runs", isinstance(py_ok, bool) and py_cur and py_req == "3.9")
check("yt-dlp instructions exist", len(instructions_for("yt-dlp")) > 0)
check("ffmpeg instructions exist", len(instructions_for("ffmpeg")) > 0)

# Packaging: installed dist matches source tree
import vidphen
from importlib import metadata as _md
check("dist version matches source", _md.version("vidphen") == vidphen.__version__)
_eps = _md.entry_points()
if hasattr(_eps, "select"):
    _eps = _eps.select(group="console_scripts")
else:
    _eps = _eps.get("console_scripts", [])
check("vidphen console script installed", "vidphen" in [e.name for e in _eps])
from vidphen.contentSelect.ui import BANNER, HEADER_LINE
_banner_lines = [l for l in BANNER.splitlines() if l.strip()]
check("banner is multi-line figlet art", len(_banner_lines) >= 5 and "___" in BANNER)
check("header line tagged", "VIDPHEN" in HEADER_LINE)

print()
if failures:
    print(f"{len(failures)} FAILED")
    raise SystemExit(1)
print("All checks passed")
