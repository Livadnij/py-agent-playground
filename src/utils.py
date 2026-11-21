RESET = '\033[0m'
COLORS = {
    'red': 31,
    'green': 32,
    'yellow': 33,
    'blue': 34,
    'magenta': 35,
    'cyan': 36,
    'gray': 90,
}


def paint(text: str, color: str, background: bool = False) -> str:
    code = COLORS[color] + (10 if background else 0)
    return f'\033[{code}m{text}{RESET}'