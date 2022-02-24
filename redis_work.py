import redis
import json
import random


class RedisDB:

    def __init__(self, host, port, password):
        self.r = redis.Redis(host=host, port=port, db=0, password=password, decode_responses=True)

    def check_db(self):
        last_question_id = len(self.r.keys(pattern='question_*'))
        if not last_question_id:
            raise Exception('База с вопросами пуста')

    def get_user(self, chat_id):
        user_data = self.r.get(chat_id)
        if user_data:
            user_data = json.loads(user_data)
            return {
                'user_last_question_id': user_data.get('user_last_question_id') or 'question_1',
                'user_score_right': user_data.get('user_score_right') or 0,
                'user_score_wrong': user_data.get('user_score_wrong') or 0
            }
        return {'user_last_question_id': 'question_1', 'user_score_right': 0, 'user_score_wrong': 0}

    def update_user(self, chat_id, question_id, count_right, count_wrong):
        self.r.set(chat_id, json.dumps({
            'user_last_question_id': f'question_{question_id}',
            'user_score_right': count_right,
            'user_score_wrong': count_wrong,
        }))

    def add_question(self, question, answer):
        last_question_id = len(self.r.keys(pattern='question_*')) + 1
        question_answer = {'question': question, 'answer': answer}
        self.r.set(f'question_{last_question_id}', json.dumps(question_answer))

    def get_question_and_answer(self, question_id):
        data = self.r.get(question_id)
        question_answer = json.loads(data)
        question = question_answer.get('question')
        answer = question_answer.get('answer')
        return question, answer

    def get_random_question(self):
        last_question_id = len(self.r.keys(pattern='question_*'))
        question_id = random.randint(1, last_question_id)
        return question_id, self.get_question_and_answer(f'question_{question_id}')[0]
