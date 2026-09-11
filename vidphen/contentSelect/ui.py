"""Section dividers so screen output isn't cluttered."""

DIVIDER = "-" * 70
HEADER_LINE = "----- VIDPHEN " + "-" * 56

# Generated with figlet 'standard' font (never hand-drawn).
BANNER = r"""__     _____ ____  ____  _   _ _____ _   _
\ \   / /_ _|  _ \|  _ \| | | | ____| \ | |
 \ \ / / | || | | | |_) | |_| |  _| |  \| |
  \ V /  | || |_| |  __/|  _  | |___| |\  |
   \_/  |___|____/|_|   |_| |_|_____|_| \_|"""


def divider():
    print(DIVIDER)


def open_section():
    divider()
    print(HEADER_LINE)


def close_section():
    divider()


def banner(version=""):
    print("=" * 70)
    print(BANNER)
    if version:
        print(f"  v{version}")
    print("=" * 70)


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
