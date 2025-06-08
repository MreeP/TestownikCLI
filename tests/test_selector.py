from pathlib import Path

from quiz.selector import _collect_quiz_dirs


def test_collect_quiz_dirs_sorting(workdir: Path):
    dirs = _collect_quiz_dirs(workdir)
    # katalog z progress.json (set2) powinien być pierwszy
    names = [d.name for d in dirs]
    assert names[0] == "set2"
    assert set(names) == {"set1", "set2"}
