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


def test_img_tag_is_not_counted_as_answer(tmp_path):
    file = tmp_path / "q_img.txt"
    file.write_text("1\nWhat?\nA\n[img]07.png[/img]\nB", encoding="utf-8")
    q = Question.from_file(file)
    # Only "A" and "B" should be available answers, not the image tag
    assert q.available_answers == ["A", "B"]
    assert q.correct_indices() == [1]
    assert q.answers_ok("1")
    assert not q.answers_ok("2")
