import shutil
from pathlib import Path

import pytest

from quiz.interface import BaseInterface


@pytest.fixture()
def workdir(tmp_path: Path) -> Path:
    """
    Kopiuje statyczne dummy-zestawy do tymczasowego katalogu
    i zwraca ścieżkę do kopii.
    """
    src = Path(__file__).parent / "dummy_sets"
    dst = tmp_path / "sets"
    shutil.copytree(src, dst)
    return dst


class DummyInterface(BaseInterface):
    """
    Minimalna implementacja interfejsu – podaje z góry ustalone odpowiedzi,
    pomija wszelkie wydruki.
    """

    def __init__(self, quiz, answers):
        super().__init__(quiz)
        self._it = iter(answers)

    def ask(self, question, idx, total):
        return next(self._it)

    def notify_result(self, question, correct, idx, total):
        pass

    def pause(self):
        pass

    def show_summary(self):
        pass
