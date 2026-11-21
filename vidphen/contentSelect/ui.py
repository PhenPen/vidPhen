"""Terminal rendering for VidPhen."""

from contextlib import contextmanager
from os import environ

from rich.console import Console
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn
from rich.table import Table


console = Console(markup=False, highlight=False)


def styled():
    return console.is_terminal and "NO_COLOR" not in environ and environ.get("TERM") != "dumb"


def divider():
    print()


def open_section():
    print()


def close_section():
    print()


def banner(version=""):
    label = f"VidPhen  v{version}" if version else "VidPhen"
    if styled():
        console.rule(label, style="bold cyan", align="left")
    else:
        print(label)


def show_table(title, headers, rows):
    if styled():
        table = Table(title=title, title_justify="left", header_style="bold cyan", box=None)
        for header in headers:
            table.add_column(header, overflow="fold")
        for row in rows:
            table.add_row(*row)
        console.print(table, width=console.width)
    else:
        print(title)
        for row in rows:
            print("  " + " | ".join(row))


@contextmanager
def download_progress():
    if not styled():
        yield None
        return
    with Progress(
        TextColumn("Downloading", style="cyan"), BarColumn(bar_width=None),
        TaskProgressColumn(), console=console, transient=True,
    ) as progress:
        task = progress.add_task("Downloading", total=100, visible=False)

        def update(value):
            try:
                percent = float(value.strip().rstrip("%"))
            except ValueError:
                return False
            progress.update(task, completed=percent, visible=True)
            return True

        yield update


class BackToMenu(Exception):
    """Return from the current workflow to the main menu."""


def prompt(message="", allow_back=True):
    """input() that confirms quit on Ctrl+C / Ctrl+D instead of traceback."""
    import builtins
    while True:
        try:
            answer = builtins.input(message)
            if allow_back and answer.strip().lower() == ":back":
                raise BackToMenu
            return answer
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
