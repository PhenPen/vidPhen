"""Section dividers so screen output isn't cluttered."""

DIVIDER = "-" * 70


def divider():
    print(DIVIDER)


def open_section():
    divider()


def close_section():
    divider()
