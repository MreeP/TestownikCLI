from __future__ import annotations

import os
import textwrap
from abc import ABC, abstractmethod

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .quiz import Quiz
from .question import Question

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

    def _print_wrapped(self, prefix: str, text: str) -> None:
        """Print text wrapped to WIDTH, keeping the prefix on the first line."""
        lines = textwrap.wrap(text, width=self.WIDTH - len(prefix))
        if not lines:
            print(prefix.rstrip())
            return
        print(prefix + lines[0])
        indent = " " * len(prefix)
        for l in lines[1:]:
            print(indent + l)

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
        self._print_wrapped("Q: ", question.question)
        print()
        for idx_ans, ans in enumerate(question.available_answers, start=1):
            self._print_wrapped(f"{idx_ans}. ", ans)
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

        self._print_wrapped("Q: ", question.question)
        print()
        for idx_ans, ans in enumerate(question.available_answers, start=1):
            mark = "✅  " if idx_ans in question.correct_indices() else "❌  "
            self._print_wrapped(f"{mark}{idx_ans}. ", ans)
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
