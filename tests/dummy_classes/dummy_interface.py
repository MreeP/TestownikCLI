from quiz import BaseInterface


class DummyInterface(BaseInterface):
    """Replaces CLI – feeds predefined answers and does nothing else."""

    def __init__(self, quiz, answers):
        super().__init__(quiz)
        self._it = iter(answers)

    def ask(self, question, idx, total):  # noqa: D401
        return next(self._it)

    def notify_result(self, question, correct, idx, total):
        pass

    def pause(self):
        pass

    def show_summary(self):
        pass
