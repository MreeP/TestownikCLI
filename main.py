from pathlib import Path

from quiz.quiz import Quiz
from quiz.selector import _collect_quiz_dirs, _select_directory


def main() -> None:
    base_directory = Path.cwd() / "zestawy"

    if not base_directory.exists():
        print(f"Brak katalogu bazowego: {base_directory}")
        return

    quiz_dirs = _collect_quiz_dirs(base_directory)

    if not quiz_dirs:
        print("Nie znaleziono żadnych zestawów pytań.")
        return

    directory = _select_directory(quiz_dirs, base_directory)

    try:
        quiz = Quiz.from_directory(directory)
    except FileNotFoundError:
        print("Wybrany katalog nie istnieje")
        return

    quiz.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        import sys
        import shutil

        # Move cursor to the bottom of the terminal, then print "Bye!" on a new line.
        rows, columns = shutil.get_terminal_size((80, 20))
        # Move cursor to bottom row, column 1
        print(f"\033[{rows};1H", end="")
        # Clear the line to avoid leftover prompt
        print("\033[2K", end="")
        print("Bye!")
