import json
from pathlib import Path
from typing import Union

from .question import Question
from .interface import BaseInterface, CliInterface

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
