"""Section dividers so screen output isn't cluttered."""

DIVIDER = "-" * 70


def divider():
    print(DIVIDER)


def open_section():
    divider()


def close_section():
    divider()


def prompt(message=""):
    """input() that exits cleanly on Ctrl+C / Ctrl+D instead of traceback."""
    try:
        return input(message)
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        raise SystemExit(0)
