import os
import random
from redis_work import RedisDB
from dotenv import load_dotenv


def add_question_and_answer_to_db(file_name):
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)

    redis_port = int(os.environ['REDIS_PORT'])
    redis_host = os.environ['REDIS_HOST']
    redis_password = os.environ['REDIS_PASSWORD']
    r = RedisDB(host=redis_host, port=redis_port, password=redis_password)

    questions_dir = os.path.join(os.path.dirname(__file__), 'questions')

    file_path = os.path.join(questions_dir, file_name)
    with open(file_path, encoding='KOI8-R') as file_with_questions:
        questions = file_with_questions.read()

    question_and_answer = ''
    while 'Ответ:' not in question_and_answer:
        list_questions = questions.split('Вопрос')[1:]
        question_and_answer = random.choice(list_questions)

    question_and_answer = question_and_answer.split('Ответ:')
    question = question_and_answer[0].split(':')[1].strip()
    answer = question_and_answer[1].split('\n\n')[0].strip()

    r.add_question(question, answer)
