from quiz import Quiz
from tests.dummy_classes.dummy_interface import DummyInterface


def test_quiz_end_to_end(workdir):
    print('workdir: ' + workdir.__str__())

    # odpowiadamy: Yes (dla q1) oraz Red (dla q2)
    quiz = Quiz.from_directory(
        workdir,
        interface=DummyInterface(None, ["1", "2"]),
        should_update_progress=False,
        skip_solved=False,
    )
    quiz.interface.quiz = quiz  # uzupełniamy referencję
    quiz.run()

    assert quiz.total_unique_correct() == 2
    assert quiz.total_unique_incorrect() == 0
    assert quiz.ratio() == 1.0
