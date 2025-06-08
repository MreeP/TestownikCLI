import json
import os
import subprocess
import platform
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union

import sys

if os.name == "nt":
    import msvcrt
else:
    import tty, termios


class Question:
    IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif')

    def __init__(
            self,
            file: Path,
            question: str,
            correct_answers: str,
            available_answers: list[str],
    ):
        self.file = file
        self.question = question
        self.correct_answers = correct_answers
        self.available_answers = available_answers

    def __str__(self):
        return f'Question [{self.file.name}]: {self.question}?\n' + '\n'.join(f'{i + 1}. {answer}' for i, answer in enumerate(self.available_answers))

    def correct_indices(self) -> list[int]:
        return [i + 1 for i, c in enumerate(self.correct_answers) if c == "1"]

    def answers_ok(self, user_input: str) -> bool:
        user_set = {int(tok) for tok in user_input.split() if tok.isdigit()}
        return user_set == set(self.correct_indices())

    def answers_as_str(self) -> str:
        return ", ".join(map(str, self.correct_indices()))

    def ask(self) -> str:
        print(self)
        return input("\nInsert correct answers: ")

    @classmethod
    def from_file(cls, file: Path) -> "Question":
        if not cls.should_process(file):
            raise ValueError(f"File {file} is not a valid question file")
        if not file.exists():
            raise FileNotFoundError(f"File {file} does not exist")

        with open(file, "r", encoding="utf-8", errors="replace") as f:  # protects against UnicodeDecodeError
            correct_answers = f.readline().strip("X\n")
            question = f.readline().rstrip(" ?\n")
            available_answers = [x.strip() for x in f.readlines()]

        return cls(file, question, correct_answers, available_answers)

    def image_path(self) -> Union[Path, None]:
        """Zwraca ścieżkę do pierwszego istniejącego pliku graficznego lub None."""
        for ext in self.IMAGE_EXTENSIONS:
            candidate = self.file.with_suffix(ext)
            if candidate.exists():
                return candidate

        return None

    def has_image(self) -> bool:
        return self.image_path() is not None

    def display_image(self):
        path = self.image_path()
        if not path:
            return

        system = platform.system()
        if system == "Darwin":
            subprocess.Popen(["open", str(path.absolute())])
        elif system == "Windows":
            os.startfile(str(path))
        else:
            subprocess.Popen(["xdg-open", str(path.absolute())])

    @staticmethod
    def should_process(file: Path) -> bool:
        return file.name.endswith('.txt')


class BaseInterface(ABC):
    """Abstrakcyjna warstwa prezentacji (CLI, GUI, itp.)."""

    def __init__(self, quiz: "Quiz"):
        self.quiz = quiz

    @abstractmethod
    def ask(self, question: Question, idx: int, total: int) -> str:
        """Wyświetla pytanie i zwraca odpowiedź użytkownika."""
        raise NotImplementedError

    @abstractmethod
    def notify_result(self, question: Question, correct: bool, idx: int, total: int) -> None:
        """Informuje o poprawności odpowiedzi."""
        raise NotImplementedError

    @abstractmethod
    def pause(self) -> None:
        """Krótka pauza po pytaniu (np. naciśnięcie Enter)."""
        raise NotImplementedError

    @abstractmethod
    def show_summary(self) -> None:
        """Wyświetla końcowe statystyki."""
        raise NotImplementedError


class CliInterface(BaseInterface):
    """Prosta implementacja linii komend."""

    WIDTH = 80  # szerokość ramki z '#'

    @staticmethod
    def _clear() -> None:
        os.system("cls" if os.name == "nt" else "clear")

    @classmethod
    def _line(cls, text: str = "") -> str:
        return f" {text}"

    def _global_stats_line(self) -> str:
        correct_cnt = self.quiz.total_unique_correct()
        incorrect_cnt = self.quiz.total_unique_incorrect()
        return self._line(f"✅ {correct_cnt} - ❌ {incorrect_cnt}")

    def ask(self, question: Question, idx: int, total: int) -> str:
        self._clear()
        question.display_image()

        border = "#" * self.WIDTH
        header = self._line(f"Question {idx} of {total}: {question.file.name}")
        stats_line = self._global_stats_line()

        print(border)
        print(header)
        print(stats_line)
        print(border)
        print()
        print(f"Q: {question.question}\n")
        for idx_ans, ans in enumerate(question.available_answers, start=1):
            print(f"{idx_ans}. {ans}")
        print()

        print(border)
        prompt_text = "Enter your answer: "
        prompt_line = self._line(prompt_text)
        print(prompt_line)
        print(border)

        print("\033[2A", end="")
        cursor_col = 2 + len(prompt_text)
        print(f"\033[{cursor_col}C", end="", flush=True)

        answer = input().strip()
        print()
        return answer

    def notify_result(self, question: Question, correct: bool, idx: int, total: int) -> None:
        self._clear()

        border = "#" * self.WIDTH
        symbol = "✅  " if correct else "❌  "
        header = self._line(f"Question {idx} of {total}: {question.file.name} {symbol} ")
        stats_line = self._global_stats_line()

        print(border)
        print(header)
        print(stats_line)
        print(border)
        print()

        print(f"Q: {question.question}\n")
        for idx_ans, ans in enumerate(question.available_answers, start=1):
            mark = "✅  " if idx_ans in question.correct_indices() else "❌  "
            print(f"{mark}{idx_ans}. {ans}")
        print()

        print(border)
        result_text = "Correct answer" if correct else "Wrong answer"
        prompt_line = self._line(f"{result_text}: {', '.join(map(str, question.correct_indices()))}")
        print(prompt_line)
        print(border)
        print()

    def pause(self) -> None:
        input("Press enter to continue")
        self._clear()

    def show_summary(self) -> None:
        border = "#" * self.WIDTH
        total_q = len(self.quiz.questions)
        correct_q = self.quiz.total_unique_correct()
        incorrect_q = self.quiz.total_unique_incorrect()

        self._clear()
        print(border)
        print(self._line("QUIZ SUMMARY"))
        print(border)
        print(self._line(f"✅  Correct:   {correct_q}/{total_q}"))
        print(self._line(f"❌  Incorrect: {incorrect_q}/{total_q}"))
        print(self._line(f"Success rate: {self.quiz.ratio():.0%}"))
        print(border)


class Quiz:
    def __init__(
            self,
            questions: list[Question],
            progress_path: Path,
            should_update_progress: bool = True,
            interface: Union["BaseInterface", None] = None,
            skip_solved: bool = True
    ):
        self.questions = questions
        self.progress_path = progress_path
        self.should_update_progress = should_update_progress
        self.correct_questions: list[str] = []
        self.incorrect_questions: list[str] = []
        self.stats: dict[str, dict[str, int]] = {}
        self._load_progress()
        self.interface = interface or CliInterface(self)
        self.skip_solved = skip_solved

    def _load_progress(self):
        if not self.progress_path.exists():
            return

        try:
            with open(self.progress_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            return

        if isinstance(data.get("stats"), dict):
            self.stats = {
                k: {"correct": v.get("correct", 0), "incorrect": v.get("incorrect", 0)}
                for k, v in data["stats"].items()
            }
            return

        self.correct_questions = data.get("correct", [])
        self.incorrect_questions = data.get("incorrect", [])
        for name in self.correct_questions:
            self.stats.setdefault(name, {"correct": 0, "incorrect": 0})["correct"] += 1
        for name in self.incorrect_questions:
            self.stats.setdefault(name, {"correct": 0, "incorrect": 0})["incorrect"] += 1

    def _save_progress(self):
        self.progress_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.progress_path, "w", encoding="utf-8") as f:
            data = {
                "stats": self.stats,
                "correct": self.correct_questions,
                "incorrect": self.incorrect_questions,
            }
            json.dump(data, f, indent=2)

    @classmethod
    def from_directory(
            cls,
            directory: Path,
            *,
            progress_path: Union[Path, None] = None,
            should_update_progress: bool = True,
            interface: Union["BaseInterface", None] = None,
            skip_solved: bool = True
    ) -> "Quiz":
        if not directory.exists():
            raise FileNotFoundError(directory)

        questions = [
            Question.from_file(file)
            for file in sorted(directory.iterdir())
            if Question.should_process(file)
        ]
        progress_path = progress_path or directory / "progress.json"
        return cls(questions, progress_path, should_update_progress, interface, skip_solved=skip_solved)

    def _should_skip(self, question: Question) -> bool:
        return (
                self.skip_solved
                and self.stats.get(question.file.name, {}).get("correct", 0) > 0
        )

    def _record_result(self, name: str, correct: bool) -> None:
        self.stats.setdefault(name, {"correct": 0, "incorrect": 0})
        key_add, key_remove = ("correct", "incorrect") if correct else ("incorrect", "correct")
        self.stats[name][key_add] += 1

        add_list = self.correct_questions if correct else self.incorrect_questions
        rem_list = self.incorrect_questions if correct else self.correct_questions

        if name not in add_list:
            add_list.append(name)
        rem_list[:] = [q for q in rem_list if q != name]

    def _maybe_save_progress(self) -> None:
        if self.should_update_progress:
            self._save_progress()

    def _get_question_stats(self, q: Question) -> dict[str, int]:
        return self.stats.get(q.file.name, {"correct": 0, "incorrect": 0})

    def _process_single(self, question: Question, idx: int, total: int):
        user_ans = self.interface.ask(question, idx, total)
        correct = question.answers_ok(user_ans)
        self._record_result(question.file.name, correct)
        self.interface.notify_result(question, correct, idx, total)
        self._maybe_save_progress()
        self.interface.pause()

    def run(self):
        total = len(self.questions)
        for idx, q in enumerate(self.questions, start=1):
            if self._should_skip(q):
                continue
            self._process_single(q, idx, total)
        self.interface.show_summary()

    def total_unique_correct(self) -> int:
        return sum(1 for v in self.stats.values() if v["correct"] > 0)

    def total_unique_incorrect(self) -> int:
        return sum(1 for v in self.stats.values() if v["correct"] == 0 and v["incorrect"] > 0)

    def ratio(self) -> float:
        total = len(self.questions)
        return self.total_unique_correct() / total if total else 0.0


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


def main():
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
    main()
