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
