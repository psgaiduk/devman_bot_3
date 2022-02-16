import redis
import os
from dotenv import load_dotenv
import json
import random


class RedisDB:

    def __init__(self, host, port, password):
        self.r = redis.Redis(host=host, port=port, db=0, password=password, decode_responses=True)
        id_last_question = int(self.r.get('id_last_question'))
        if not id_last_question:
            self.r.set('id_last_question', 1)

    def get_user(self, chat_id):
        user_data = self.r.get(f'{chat_id}')
        if user_data:
            return_data = json.loads(user_data)
            if return_data.get('user_score_right') is None or return_data.get('user_score_wrong') is None:
                return {'user_last_question_id': 'question_1', 'user_score_right': 0, 'user_score_wrong': 0}
            return return_data
        return {'user_last_question_id': 'question_1', 'user_score_right': 0, 'user_score_wrong': 0}

    def update_user(self, chat_id, question_id, count_right, count_wrong):
        self.r.set(f'{chat_id}', json.dumps({
            'user_last_question_id': f'question_{question_id}',
            'user_score_right': count_right,
            'user_score_wrong': count_wrong,
        }))

    def add_question(self, question, answer):
        id_last_question = int(self.r.get('id_last_question'))
        question_answer = {'question': question, 'answer': answer}
        self.r.set(f'question_{id_last_question}', json.dumps(question_answer))
        self.r.set('id_last_question', id_last_question)
        print(f'Вопрос №{id_last_question} добавлен в базу данных:\n'
              f'Вопрос:\n{question}\n\n'
              f'Ответ: {answer}\n')

        self.r.set('id_last_question', id_last_question + 1)

    def get_question_and_answer(self, id_question):
        data = self.r.get(id_question)
        if data:
            question_answer = json.loads(data)
        else:
            return 'База данных пуста', 'Нужно добавить вопросов'
        question = question_answer.get('question')
        answer = question_answer.get('answer')
        return question, answer

    def get_random_question(self):
        id_last_question = int(self.r.get('id_last_question'))
        id_question = random.randint(1, id_last_question)
        return id_question, self.get_question_and_answer(f'question_{id_question}')[0]

    def get_answer(self, id_question):
        return self.get_question_and_answer(id_question)[1]


if __name__ == '__main__':
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
    redis_port = int(os.environ['REDIS_PORT'])
    redis_host = os.environ['REDIS_HOST']
    redis_password = os.environ['REDIS_PASSWORD']
    r = RedisDB(host=redis_host, port=redis_port, password=redis_password)

    r.update_user(123, 1234)
    user = r.get_user(123)
    # r.add_question('С одним советским туристом в Марселе произошел такой случай. Спустившись из своего номера '
    #                'на первый этаж, он вспомнил, что забыл закрутить кран в ванной. Когда он поднялся, вода уже '
    #                'затопила комнату. Он вызвал горничную, та попросила его обождать внизу. В страхе он ожидал'
    #                ' расплаты за свою оплошность. Но администрация его не ругала, а, напротив, извинилась сама'
    #                ' перед ним. За что?',
    #                'За то, что не объяснила ему правила пользования кранами.')
    print(user)
    print(r.get_random_question())
