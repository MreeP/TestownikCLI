import json
import subprocess
import os
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Union


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

        with open(file, "r") as f:
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
        if path:
            subprocess.Popen(['open', path.absolute()])

    @staticmethod
    def should_process(file: Path) -> bool:
        return file.name.endswith('.txt')


class BaseInterface(ABC):
    """Abstrakcyjna warstwa prezentacji (CLI, GUI, itp.)."""

    def __init__(self, quiz: "Quiz"):
        self.quiz = quiz

    @abstractmethod
    def ask(self, question: Question) -> str:
        """Wyświetla pytanie i zwraca odpowiedź użytkownika."""
        raise NotImplementedError

    @abstractmethod
    def notify_result(self, question: Question, correct: bool) -> None:
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

    WIDTH = 55  # szerokość ramki z '#'

    @staticmethod
    def _clear() -> None:
        os.system("cls" if os.name == "nt" else "clear")

    @classmethod
    def _line(cls, text: str = "") -> str:
        return f"# {text.ljust(cls.WIDTH - 4)} #"

    def ask(self, question: Question) -> str:
        self._clear()
        question.display_image()

        border = "#" * self.WIDTH
        header = self._line(f"Question: {question.file.name}")

        print(border)
        print(header)
        print(border)
        print()
        print(f"Q: {question.question}\n")

        for idx, ans in enumerate(question.available_answers, start=1):
            print(f"{idx}. {ans}")

        print()
        print(border)
        prompt_line = self._line("Enter your answer: ")
        print(prompt_line)
        print(border)

        return input().strip()

    def notify_result(self, question: Question, correct: bool) -> None:
        self._clear()

        border = "#" * self.WIDTH
        symbol = "✅" if correct else "❌"
        correct_ids = ", ".join(map(str, question.correct_indices()))
        header = self._line(f"{symbol} Correct answer: {correct_ids}")

        print(border)
        print(header)
        print(border)
        print()

        for idx, ans in enumerate(question.available_answers, start=1):
            mark = "✅" if idx in question.correct_indices() else "❌"
            print(f"{idx}. {ans}   {mark}")

        print()

    def pause(self) -> None:
        input("Press enter to continue")
        self._clear()

    def show_summary(self) -> None:
        print(
            f"\nResult: {len(self.quiz.correct_questions)}/{len(self.quiz.questions)} "
            f"({self.quiz.ratio():.0%} correct)"
        )

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
        except (OSError, json.JSONDecodeError):
            return  # zostaw puste statystyki

        # format z licznikami
        if isinstance(data.get("stats"), dict):
            self.stats = {
                k: {"correct": v.get("correct", 0), "incorrect": v.get("incorrect", 0)}
                for k, v in data["stats"].items()
            }
            return

        # stary format list -> konwersja
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
                "stats": self.stats,  # nowy format
                "correct": self.correct_questions,  # zachowujemy na zgodność z wcześniejszym kodem
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
        """Decyduje czy pytanie należy pominąć (już rozwiązane)."""
        return (
            self.skip_solved
            and self.stats.get(question.file.name, {}).get("correct", 0) > 0
        )

    def _record_result(self, name: str, correct: bool) -> None:
        """Aktualizuje statystyki oraz listy correct/incorrect."""
        self.stats.setdefault(name, {"correct": 0, "incorrect": 0})
        key_add, key_remove = ("correct", "incorrect") if correct else ("incorrect", "correct")
        self.stats[name][key_add] += 1

        add_list = self.correct_questions if correct else self.incorrect_questions
        rem_list = self.incorrect_questions if correct else self.correct_questions

        if name not in add_list:
            add_list.append(name)
        rem_list[:] = [q for q in rem_list if q != name]

    def _maybe_save_progress(self) -> None:
        """Zapisuje postęp, jeżeli opcja jest włączona."""
        if self.should_update_progress:
            self._save_progress()

    def _ask_question(self, question: Question):
        user_answers = self.interface.ask(question)
        correct = question.answers_ok(user_answers)

        self._record_result(question.file.name, correct)
        self.interface.notify_result(question, correct)
        self._maybe_save_progress()
        self.interface.pause()

    def run(self):
        for question in self.questions:
            if self._should_skip(question):
                continue
            self._ask_question(question)
        self.interface.show_summary()

    def ratio(self) -> float:
        total = len(self.questions)
        return len(self.correct_questions) / total if total else 0.0


def main():
    directory = Path.cwd() / 'zestawy' / 'sieci3'

    try:
        quiz = Quiz.from_directory(directory)
    except FileNotFoundError:
        print('Directory does not exist')
        return

    quiz.run()


if __name__ == "__main__":
    main()
