"""Terminal rendering for VidPhen."""

from contextlib import contextmanager
from os import environ

from rich.cells import cell_len
from rich.console import Console
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn
from rich.table import Table
from rich.text import Text


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


def show_preview(title, label, value_label, rows):
    """Give numbers and durations fixed space and wrap only the title."""
    if not styled():
        show_table(title, ("#", label, value_label), rows)
        return
    index_width = max(cell_len(index) for index, _, _ in rows)
    value_width = max(cell_len(value) for value in [value_label, *(row[2] for row in rows)])
    if console.width < index_width + value_width + 16:
        console.print(title)
        for index, name, value in rows:
            console.print(Text(f"{index}. {name}"), overflow="fold")
            console.print(Text(f"   {value_label}: {value}"), overflow="fold")
        return

    table = Table(title=title, title_justify="left", header_style="bold cyan", box=None, padding=(0, 1))
    table.add_column("#", width=index_width, no_wrap=True)
    table.add_column(label, ratio=1, overflow="fold")
    table.add_column(value_label, width=value_width, no_wrap=True, justify="right")
    for row in rows:
        table.add_row(*(Text(value) for value in row))
    console.print(table, width=console.width)


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
