# Automated checks - no network, no prompts. Run: python test.py
from contentSelect.quality import ask_fallback_policy  # noqa: F401 (import check)
from contentSelect.quality import get_format, picked_height
from contentSelect.validators import is_valid_format_id, is_valid_url, parse_items, parse_range, parse_url_list
from metaDataSelect.metaData import format_duration
from subtitleSelect.sub_langs import lang_args_for_choice

failures = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        failures.append(name)


# URLs
check("valid watch url", is_valid_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ"))
check("valid youtu.be url", is_valid_url("https://youtu.be/dQw4w9WgXcQ"))
check("valid playlist url", is_valid_url("https://www.youtube.com/playlist?list=PL123abc"))
check("reject notaurl", not is_valid_url("notaurl"))
check("reject empty", not is_valid_url(""))


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
import contentSelect.ui  # noqa: F401
import downloadSelect.runner  # noqa: F401
import subtitleSelect.subsPlaylist  # noqa: F401
import subtitleSelect.subsVideo  # noqa: F401
check("imports need no input", True)

print()
if failures:
    print(f"{len(failures)} FAILED")
    raise SystemExit(1)
print("All checks passed")
