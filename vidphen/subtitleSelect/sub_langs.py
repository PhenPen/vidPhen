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


def plan_subs():
    """Before download: return (mode, lang_args). No downloading here."""
    from vidphen.contentSelect.ui import close_section, prompt
    show_subs_mode_menu()
    while True:
        choice = prompt("Pick 1-3 : ").strip()
        if choice == "1":
            close_section()
            return ("none", [])
        elif choice in ("2", "3"):
            mode = "with" if choice == "2" else "only"
            lang_args = _pick_language()
            lang_args = lang_args + _ask_auto_captions()
            return (mode, lang_args)
        print("Invalid Selection. Try again")
