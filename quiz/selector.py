import os
import sys
from pathlib import Path

from .question import Question

if os.name == "nt":
    import msvcrt
else:
    import tty, termios

def _arrow_select(options: list[str]) -> int:
    """
    Zwraca indeks wskazanej opcji.
    – strzałki ↑/↓ przesuwają zaznaczenie
    – Enter potwierdza wybór
    Jeżeli stdin nie jest TTY, następuje powrót do wyboru „wpisz numer”.
    """
    if not sys.stdin.isatty():
        # fallback – użytkownik wpisuje numer
        for i, text in enumerate(options, 1):
            print(f"{i}. {text}")
        while True:
            ch = input("Wybierz numer: ")
            if ch.isdigit() and 1 <= int(ch) <= len(options):
                return int(ch) - 1
            print("Niepoprawny wybór – spróbuj ponownie.")

    sel = 0

    def _clear():
        os.system("cls" if os.name == "nt" else "clear")

    def _render() -> None:
        _clear()
        for i, text in enumerate(options):
            prefix = "👉 " if i == sel else "   "
            print(f"{prefix}{text}")

    if os.name == "nt":                       # Windows – msvcrt
        while True:
            _render()
            key = msvcrt.getch()
            if key == b'\r':                  # Enter
                return sel
            if key == b'\xe0':                # kod rozszerzony
                direction = msvcrt.getch()
                if direction == b'H':         # strzałka ↑
                    sel = (sel - 1) % len(options)
                elif direction == b'P':       # strzałka ↓
                    sel = (sel + 1) % len(options)
    else:                                     # Unix-like – termios/tty
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            while True:
                _render()
                ch = sys.stdin.read(1)
                if ch == '\n' or ch == '\r':  # Enter
                    return sel
                if ch == '\x1b':              # sekwencja ESC
                    seq = sys.stdin.read(2)
                    if seq == '[A':           # ↑
                        sel = (sel - 1) % len(options)
                    elif seq == '[B':         # ↓
                        sel = (sel + 1) % len(options)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

def _collect_quiz_dirs(base: Path) -> list[Path]:
    """Zwraca katalogi zawierające pliki .txt (pytania) lub progress.json.
       Te z plikiem progress.json są sortowane wyżej."""
    dirs: list[Path] = []
    for p in base.rglob("*"):
        if not p.is_dir():
            continue
        has_txt = any(Question.should_process(f) for f in p.iterdir())
        has_progress = (p / "progress.json").exists()
        if has_txt or has_progress:
            dirs.append(p)
    dirs.sort(key=lambda d: (0 if (d / "progress.json").exists() else 1, str(d).lower()))
    return dirs


def _select_directory(dirs: list[Path], base: Path) -> Path:
    labels = [
        f"{'[CONTINUE LEARNING] ' if (d / 'progress.json').exists() else ''}{d.relative_to(base)}"
        for d in dirs
    ]
    selected_index = _arrow_select(labels)
    return dirs[selected_index]
