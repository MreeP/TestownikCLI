import os
import platform
import subprocess
from pathlib import Path
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
        return Question.parse_user_input(user_input) == set(self.correct_indices())

    @staticmethod
    def parse_user_input(user_input: str) -> set[int]:
        """
        Parses user input and returns a list of integers representing the selected answers.
        Accepts answers like '2 4 5', '245', or any mix of whitespace and digits.
        """
        return set([int(ch) for ch in user_input if ch.isdigit()])

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

        def is_img_tag(line: str) -> bool:
            line = line.strip()
            return line.lower().startswith("[img]") and line.lower().endswith("[/img]")

        with open(file, "r", encoding="utf-8", errors="replace") as f:  # protects against UnicodeDecodeError
            correct_answers = f.readline().strip("X\n")
            question = f.readline().rstrip(" ?\n")
            available_answers = [
                x.strip() for x in f.readlines()
                if x.strip() and not is_img_tag(x)
            ]

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
