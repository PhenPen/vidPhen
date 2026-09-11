"""Section dividers so screen output isn't cluttered."""

DIVIDER = "-" * 70


def divider():
    print(DIVIDER)


def open_section():
    divider()


def close_section():
    divider()


def prompt(message=""):
    """input() that confirms quit on Ctrl+C / Ctrl+D instead of traceback."""
    import builtins
    while True:
        try:
            return builtins.input(message)
        except (KeyboardInterrupt, EOFError):
            try:
                again = builtins.input("\nQuit app? (y/n) : ").strip().upper()
            except (KeyboardInterrupt, EOFError):
                print("\nBye!")
                raise SystemExit(0)
            if again == "Y":
                print("Bye!")
                raise SystemExit(0)
            print("Continuing...")
            continue
