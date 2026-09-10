"""Numbered subtitle language menu. No raw code typing unless Advanced."""

OPTIONS = [
    ("1", "English", "en"),
    ("2", "French", "fr"),
    ("3", "Spanish", "es"),
    ("4", "German", "de"),
    ("5", "All / auto (default)", None),
]

_LANGS = {c: (label, code) for c, label, code in OPTIONS}


def show_lang_menu():
    from contentSelect.ui import open_section
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
    from contentSelect.ui import open_section
    open_section()
    print("Subtitles?")
    print("1) No subtitles - just video")
    print("2) Video + subtitles")
    print("3) Subtitles only - no video")


def _pick_language():
    """Ask 1-6 language, return lang_args list. Repeats until valid."""
    from contentSelect.ui import close_section
    show_lang_menu()
    while True:
        sel = input("Pick 1-6 : ").strip()
        if sel == "6":
            lang = input("Enter language code eg en,fr,es : ").strip()
            args = lang_args_for_choice("6", lang)
        else:
            args = lang_args_for_choice(sel)
        if args is None:
            print("Invalid Selection. Try again")
            continue
        close_section()
        return args


def plan_subs():
    """Before download: return (mode, lang_args). No downloading here."""
    from contentSelect.ui import close_section
    show_subs_mode_menu()
    while True:
        choice = input("Pick 1-3 : ").strip()
        if choice == "1":
            close_section()
            return ("none", [])
        elif choice in ("2", "3"):
            mode = "with" if choice == "2" else "only"
            lang_args = _pick_language()
            return (mode, lang_args)
        print("Invalid Selection. Try again")
