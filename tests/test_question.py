from quiz import Question


def test_question_parsing_and_validation(tmp_path):
    file = tmp_path / "q.txt"
    file.write_text("101\nWhat?\nA\nB\nC", encoding="utf-8")

    q = Question.from_file(file)
    assert q.correct_indices() == [1, 3]
    assert q.answers_ok("1 3")
    assert q.answers_ok("13")
    assert q.answers_ok(" 1   3 ")
    assert not q.answers_ok("2")
    assert not q.answers_ok("12")
    assert not q.answers_ok("3")
