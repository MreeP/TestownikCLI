import shutil
from pathlib import Path

import pytest


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
