import os
import random


def get_random_question_and_answer():
    questions_dir = os.path.join(os.path.dirname(__file__), 'questions')
    files = os.listdir(questions_dir)
    random_questions_file = random.choice(files)

    file_path = os.path.join(questions_dir, random_questions_file)
    with open(file_path, encoding='KOI8-R') as file_with_questions:
        questions = file_with_questions.read()

    question_and_answer = ''
    while 'Ответ:' not in question_and_answer:
        list_questions = questions.split('Вопрос')[1:]
        question_and_answer = random.choice(list_questions)

    question_and_answer = question_and_answer.split('Ответ:')
    question = question_and_answer[0].split(':')[1].strip()
    answer = question_and_answer[1].split('\n\n')[0].strip()

    return question, answer
