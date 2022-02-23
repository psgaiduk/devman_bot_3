import os
from redis_work import RedisDB
from dotenv import load_dotenv


def add_question_and_answer_to_db():
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)

    redis_port = int(os.environ['REDIS_PORT'])
    redis_host = os.environ['REDIS_HOST']
    redis_password = os.environ['REDIS_PASSWORD']
    r = RedisDB(host=redis_host, port=redis_port, password=redis_password)

    questions_dir = os.path.join(os.path.dirname(__file__), 'questions')
    files = os.listdir(questions_dir)
    for file_name in files:
        file_path = os.path.join(questions_dir, file_name)
        with open(file_path, encoding='KOI8-R') as file_with_questions:
            questions = file_with_questions.read().split('Вопрос')[1:]

        for question_and_answer in questions:
            question, answer = question_and_answer.split('Ответ:')
            question = question.split(':')[1].strip()
            answer = answer.split('\n\n')[0].strip()

            r.add_question(question, answer)

        os.remove(file_path)


if __name__ == '__main__':
    add_question_and_answer_to_db()
