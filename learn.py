import os.path
import subprocess
from pathlib import Path, PosixPath


class Question:
    def __init__(self, file: PosixPath):
        self.file = file
        self._init_question()

    def _init_question(self):
        if not Question.should_process(self.file):
            raise ValueError(f"File {self.file} is not a valid question file")

        if not self.file.exists():
            raise FileNotFoundError(f"File {self.file} does not exist")

        with open(self.file, 'r') as f:
            self.correct_answers = f.readline().strip('X\n')
            self.question = f.readline().rstrip(" ?\n")
            self.available_answers = [x.strip() for x in f.readlines()]

    @staticmethod
    def should_process(file: PosixPath) -> bool:
        return file.name.endswith('.txt')



def display_image(file: PosixPath):
    if file.exists():
        subprocess.Popen(['open', str(file)])


def handle_question(file: PosixPath):
    if file.name.split('.')[-1] != 'txt':
        return

    question_id = file.name.split('.')[0]

    display_image(file.parent / (question_id + '.png'))

    with open(file, 'r') as f:
        correct_answers = f.readline().strip('X\n')
        question = f.readline().rstrip(" ?\n")
        available_answers = [x.strip() for x in f.readlines()]

        print(f'[{question_id}] Question: {question}?\n')

        for i, answer in enumerate(available_answers):
            print(f'{i + 1}. {answer}')

        user_answers = input('\nInsert correct answers: ')

        for index, correct_answer in enumerate(correct_answers):
            if correct_answer == '1' and str(index + 1) not in user_answers:
                print(f'Correct answers: {", ".join([str(i + 1) for i, x in enumerate(correct_answers) if x == "1"])}')
                input('Press enter to continue')
                return

            if correct_answer == '0' and str(index + 1) in user_answers:
                print(f'Correct answers: {", ".join([str(i + 1) for i, x in enumerate(correct_answers) if x == "1"])}')
                input('Press enter to continue')
                return

    print('Correct answer')
    input('Press enter to continue')

def main():
    directory = Path.cwd() / 'zestawy' / 'sieci3'

    if not directory.exists():
        print('Directory does not exist')
        return

    for file in sorted(directory.iterdir()):
        os.system('clear')
        handle_question(file)


if __name__ == "__main__":
    main()
