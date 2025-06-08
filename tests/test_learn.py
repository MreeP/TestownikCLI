import json
from pathlib import Path

import pytest

from quiz import (
    Question,
    Quiz,
    _collect_quiz_dirs,
)
from tests.dummy_classes.dummy_interface import DummyInterface


def _make_qfile(dir_: Path, name: str, mask: str = "10", q="What?", answers=None):
    answers = answers or ["A", "B"]
    content = "\n".join([mask, q, *answers])
    file = dir_ / f"{name}.txt"
    file.write_text(content, encoding="utf-8")
    return file


def test_question_parsing_and_validation(tmp_path):
    f = _make_qfile(tmp_path, "q1", mask="101", q="Select", answers=["X", "Y", "Z"])
    q = Question.from_file(f)

    assert q.correct_indices() == [1, 3]
    assert q.answers_ok("1 3")
    assert not q.answers_ok("1")
    assert not q.answers_ok("2 3")


def test_collect_quiz_dirs_sorting(tmp_path):
    # dir with progress.json
    d1 = tmp_path / "set1"
    d1.mkdir()
    (d1 / "progress.json").write_text("{}", encoding="utf-8")

    # dir with txt file
    d2 = tmp_path / "set2"
    d2.mkdir()
    _make_qfile(d2, "q")

    # nested dir with txt file
    nested = tmp_path / "nested" / "inner"
    nested.mkdir(parents=True)
    _make_qfile(nested, "q")

    result = _collect_quiz_dirs(tmp_path)
    # d1 first because it contains progress.json
    assert result[0] == d1
    assert set(result) == {d1, d2, nested}


def test_quiz_flow_and_stats(tmp_path):
    _make_qfile(tmp_path, "q1", mask="10")
    _make_qfile(tmp_path, "q2", mask="01")

    # correct answers are "1" and "2"
    qi = Quiz.from_directory(
        tmp_path,
        interface=DummyInterface(None, ["1", "2"]),
        should_update_progress=False,
        skip_solved=False,
    )
    # patch interface.quiz now that quiz is created
    qi.interface.quiz = qi
    qi.run()

    assert qi.total_unique_correct() == 2
    assert qi.total_unique_incorrect() == 0
    assert pytest.approx(qi.ratio()) == 1.0

    # recorded stats should be persisted when saved
    qi._save_progress()
    data = json.loads((tmp_path / "progress.json").read_text(encoding="utf-8"))
    assert set(data["stats"].keys()) == {"q1.txt", "q2.txt"}
