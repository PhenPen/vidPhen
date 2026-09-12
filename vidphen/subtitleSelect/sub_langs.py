"""Numbered subtitle language menu. No raw code typing unless Advanced."""

OPTIONS = [
    ("1", "English", "en"),
    ("2", "French", "fr"),
    ("3", "Spanish", "es"),
    ("4", "German", "de"),
    ("5", "Default language (usually English)", None),
]

_LANGS = {c: (label, code) for c, label, code in OPTIONS}


def show_lang_menu():
    from vidphen.contentSelect.ui import open_section
    open_section()
    print("Which subtitles?")
    for choice, label, code in OPTIONS:
        suffix = "" if code is None else f" ({code})"
        print(f"{choice}) {label}{suffix}")
    print("6) Type code yourself (eg en,fr,es)")


def lang_args_for_choice(choice, manual_code=""):
    """Return --sub-langs args list. Empty list = default/auto."""
    choice = str(choice).strip()
    if choice == "5":
        return []
    if choice in _LANGS:
        _, code = _LANGS[choice]
        if code:
            return ["--sub-langs", code]
        return []
    if choice == "6" and manual_code.strip():
        return ["--sub-langs", manual_code.strip()]
    return None


def show_subs_mode_menu():
    from vidphen.contentSelect.ui import open_section
    open_section()
    print("Subtitles?")
    print("1) No subtitles - just video")
    print("2) Video + subtitles")
    print("3) Subtitles only - no video")


def _pick_language():
    """Ask 1-6 language, return lang_args list. Repeats until valid."""
    from vidphen.contentSelect.ui import close_section, prompt
    show_lang_menu()
    while True:
        sel = prompt("Pick 1-6 : ").strip()
        if sel == "6":
            lang = prompt("Enter language code eg en,fr,es : ").strip()
            args = lang_args_for_choice("6", lang)
        else:
            args = lang_args_for_choice(sel)
        if args is None:
            print("Invalid Selection. Try again")
            continue
        close_section()
        return args


def _ask_auto_captions():
    """Offer auto-generated captions as fallback. Default yes."""
    from vidphen.contentSelect.ui import prompt
    while True:
        choice = prompt("Also fetch auto-generated captions if manual ones don't exist? (y/n) : ").strip().upper()
        if choice in ("", "Y"):
            return ["--write-automatic-subs"]
        elif choice == "N":
            return []
        print("Invalid Selection. Try again")


def plan_subs(url=None):
    """Before download: return (mode, lang_args). No downloading here.

    With a url, the language menu is built from the video's actual
    subtitles (dynamic). Without one (batch same-for-all), the static
    menu is used.
    """
    from vidphen.contentSelect.ui import close_section, prompt
    show_subs_mode_menu()
    while True:
        choice = prompt("Pick 1-3 : ").strip()
        if choice == "1":
            close_section()
            return ("none", [])
        elif choice in ("2", "3"):
            mode = "with" if choice == "2" else "only"
            if url is not None:
                dyn = _pick_language_dynamic(url)
                if dyn is not None:
                    return (mode, dyn)
            lang_args = _pick_language()
            lang_args = lang_args + _ask_auto_captions()
            return (mode, lang_args)
        print("Invalid Selection. Try again")


_SUB_CACHE = {}

_PRIORITY = [("en", "English"), ("fr", "French"), ("es", "Spanish"), ("de", "German")]


def _base(code):
    return str(code).lower().replace("_", "-").split("-")[0]


def get_sub_langs(url):
    """One lookup: {manual:[codes], auto:[codes], unknown:bool}. Cached per URL."""
    import json as _json
    import subprocess
    if url in _SUB_CACHE:
        return _SUB_CACHE[url]
    try:
        result = subprocess.run(
            ['yt-dlp', '--skip-download', '--print', '%(subtitles)j',
             '--print', '%(automatic_captions)j', url],
            capture_output=True, text=True)
    except FileNotFoundError:
        print("yt-dlp command not found. Install it with: pip install yt-dlp")
        unknown = {"manual": [], "auto": [], "unknown": True}
        _SUB_CACHE[url] = unknown
        return unknown
    if result.returncode != 0:
        unknown = {"manual": [], "auto": [], "unknown": True}
        _SUB_CACHE[url] = unknown
        return unknown
    found = []
    for line in (result.stdout or "").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            found.append(_json.loads(line))
        except ValueError:
            pass
    manual = sorted({str(k) for d in found[:1] for k in d}) if found else []
    auto = sorted({str(k) for d in found[1:2] for k in d}) if len(found) > 1 else []
    subs = {"manual": manual, "auto": auto, "unknown": False}
    _SUB_CACHE[url] = subs
    return subs


def build_lang_options(subs):
    """Compact menu mapping. Returns (entries, note). Pure (testable).

    entries = [(label, kind)] with kind ("lang", code, is_manual),
    ("default",) or ("custom",).
    """
    manual = {_base(c): c for c in subs.get("manual", [])}
    auto = {_base(c): c for c in subs.get("auto", [])}
    entries, used = [], set()
    for code, name in _PRIORITY:
        if code in manual:
            entries.append((f"{name} ({manual[code]}) [manual]", ("lang", manual[code], True)))
            used.add(code)
        elif code in auto:
            entries.append((f"{name} ({auto[code]}) [auto-generated]", ("lang", auto[code], False)))
            used.add(code)
    rest = sorted((set(manual) | set(auto)) - used)
    others = [manual.get(c, auto.get(c)) for c in rest]
    if others:
        shown = ", ".join(others[:3])
        note = f"{len(others)} more ({shown}{'...' if len(others) > 3 else ''})"
    else:
        note = ""
    entries.append(("Default language", ("default",)))
    entries.append((f"Type code yourself{f' ({note})' if note else ''}", ("custom",)))
    return entries, note


def show_lang_options(entries, note=""):
    from vidphen.contentSelect.ui import open_section
    open_section()
    print("Which subtitles?" + (f" ({note})" if note else ""))
    mapping = {}
    for i, (label, kind) in enumerate(entries, 1):
        print(f"{i}) {label}")
        mapping[str(i)] = kind
    return mapping


def _pick_language_dynamic(url):
    """Dynamic pick. Returns lang_args, or None if lookup failed."""
    from vidphen.contentSelect.ui import close_section, prompt
    subs = get_sub_langs(url)
    if subs.get("unknown"):
        return None
    if not subs.get("manual") and not subs.get("auto"):
        print("This video has no subtitles in any language.")
        return []
    entries, note = build_lang_options(subs)
    mapping = show_lang_options(entries, note)
    top = str(len(mapping))
    while True:
        sel = prompt(f"Pick 1-{top} : ").strip()
        kind = mapping.get(sel)
        if kind is None:
            print("Invalid Selection. Try again")
            continue
        if kind[0] == "custom":
            lang = prompt("Enter language code eg en,fr,es : ").strip()
            if not lang:
                print("Invalid Selection. Try again")
                continue
            close_section()
            return ["--sub-langs", lang, "--write-automatic-subs"]
        close_section()
        if kind[0] == "default":
            return []
        _, code, is_manual = kind
        args = ["--sub-langs", code]
        if not is_manual:
            args.append("--write-automatic-subs")
        return args
