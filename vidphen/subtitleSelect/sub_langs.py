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
                action, dyn = _pick_language_dynamic(url)
                if action == "ok":
                    return (mode, dyn)
                elif action == "skip":
                    return ("none", [])
            lang_args = _pick_language()
            lang_args = lang_args + _ask_auto_captions()
            return (mode, lang_args)
        print("Invalid Selection. Try again")


_SUB_CACHE = {}
_LANG_CACHE = {}

_PRIORITY = [("en", "English"), ("fr", "French"), ("es", "Spanish"), ("de", "German")]


def _base(code):
    return str(code).lower().replace("_", "-").split("-")[0]


def resolve_lang(requested, subs):
    """Map a requested code to exact available keys. Pure (testable).

    Returns (keys, needs_auto). keys empty = not available anywhere.
    Exact base match wins; otherwise first variant. Manual preferred.
    """
    want = _base(requested)
    manual = [c for c in subs.get("manual", []) if _base(c) == want]
    if manual:
        exact = [c for c in manual if c.lower() == want]
        return (exact or sorted(manual)[:1], False)
    auto = [c for c in subs.get("auto", []) if _base(c) == want]
    if auto:
        exact = [c for c in auto if c.lower() == want]
        return (exact or sorted(auto)[:1], True)
    return ([], False)


def video_language(url):
    """Video's own language code, or None. Cached per URL."""
    import subprocess
    if url in _LANG_CACHE:
        return _LANG_CACHE[url]
    try:
        result = subprocess.run(
            ['yt-dlp', '--skip-download', '--print', '%(language)s', url],
            capture_output=True, text=True)
    except FileNotFoundError:
        _LANG_CACHE[url] = None
        return None
    if result.returncode != 0:
        _LANG_CACHE[url] = None
        return None
    for line in (result.stdout or "").splitlines():
        line = line.strip()
        if line and not line.startswith("[") and line.lower() not in ("na", "none"):
            _LANG_CACHE[url] = line
            return line
    _LANG_CACHE[url] = None
    return None


def resolve_default(subs, url):
    """Default language: video's own language, else English. Pure-ish (cached lookup)."""
    lang = video_language(url) if url else None
    for candidate in ([lang] if lang else []) + ["en"]:
        keys, needs_auto = resolve_lang(candidate, subs)
        if keys:
            return (keys, needs_auto, candidate)
    return ([], False, None)


def _none_here(requested, subs):
    """Tell the user nothing exists. Returns 'retry' or 'skip'."""
    from vidphen.contentSelect.ui import close_section, open_section, prompt
    have = sorted({_base(c).upper() for c in subs.get("manual", []) + subs.get("auto", [])})
    open_section()
    print(f"No {requested} subtitles exist for this video" + (f" (has: {', '.join(have)})" if have else ""))
    print("1) Pick another language")
    print("2) Continue without subtitles")
    while True:
        choice = prompt("Pick 1-2 : ").strip()
        if choice == "1":
            close_section()
            return "retry"
        elif choice == "2":
            close_section()
            return "skip"
        print("Invalid Selection. Try again")


def _flags_for(keys, needs_auto):
    args = []
    if keys:
        args += ["--sub-langs", ",".join(keys)]
    if needs_auto:
        args.append("--write-automatic-subs")
    return args


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
    """Dynamic pick. Returns (action, lang_args).

    action: 'ok' (use args), 'skip' (continue without subtitles),
    'static' (lookup failed - use old static path).
    """
    from vidphen.contentSelect.ui import close_section, prompt
    subs = get_sub_langs(url)
    if subs.get("unknown"):
        return ("static", [])
    if not subs.get("manual") and not subs.get("auto"):
        print("This video has no subtitles in any language. Continuing without.")
        return ("skip", [])
    while True:
        entries, note = build_lang_options(subs)
        mapping = show_lang_options(entries, note)
        top = str(len(mapping))
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
            keys, needs_auto = resolve_lang(lang, subs)
            if not keys:
                if _none_here(lang, subs) == "retry":
                    close_section()
                    continue
                close_section()
                return ("skip", [])
            close_section()
            return ("ok", _flags_for(keys, needs_auto))
        close_section()
        if kind[0] == "default":
            keys, needs_auto, _ = resolve_default(subs, url)
            if not keys:
                if _none_here("default", subs) == "retry":
                    continue
                return ("skip", [])
            return ("ok", _flags_for(keys, needs_auto))
        _, code, is_manual = kind
        keys, needs_auto = resolve_lang(code, subs)
        if not keys:
            if _none_here(code, subs) == "retry":
                continue
            return ("skip", [])
        return ("ok", _flags_for(keys, needs_auto))
