from vk_api import VkApi, longpoll, exceptions
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import os
import time
from dotenv import load_dotenv
import random
import redis
from create_question_answer import get_questions_and_answers


def new_question(r, vk_api, event, keyboard):
    question, answer = get_questions_and_answers()
    r.set(event.user_id, answer)
    send_message(vk_api, event, keyboard, f'Вопрос:\n{question}')


def send_message(vk_api, event, keyboard, text):
    vk_api.messages.send(
        user_id=event.user_id,
        message=text,
        keyboard=keyboard.get_keyboard(),
        random_id=random.randint(1, 1000)
    )


def quiz_work(event, vk_api, keyboard):
    redis_password = os.environ['REDIS_PASSWORD']
    r = redis.Redis(host='redis-19360.c240.us-east-1-3.ec2.cloud.redislabs.com', port=19360, db=0,
                    password=redis_password, decode_responses=True)

    if event.message == 'Новый вопрос':
        new_question(r, vk_api, event, keyboard)

    elif event.message == 'Сдаться':
        answer = r.get(event.user_id)
        text = f'Правильный ответ:\n{answer}'
        send_message(vk_api, event, keyboard, text)
        new_question(r, vk_api, event, keyboard)

    else:
        answer = r.get(event.user_id)
        text = 'Неправильно… Попробуешь ещё раз?'
        if answer == event.message:
            text = 'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»'

        send_message(vk_api, event, keyboard, text)


def main():
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)

    token_vk = os.environ['VK_TOKEN']

    vk_session = VkApi(token=token_vk)
    vk_api = vk_session.get_api()
    long_poll = longpoll.VkLongPoll(vk_session)

    keyboard = VkKeyboard(one_time=True)

    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)

    keyboard.add_line()  # Переход на вторую строку
    keyboard.add_button('Мой счёт', color=VkKeyboardColor.PRIMARY)

    for event in long_poll.listen():
        try:
            if event.type == longpoll.VkEventType.MESSAGE_NEW and event.to_me:
                quiz_work(event, vk_api, keyboard)
        except exceptions.Captcha:
            time.sleep(1)
        except Exception as e:
            print(e)
            time.sleep(1)


if __name__ == "__main__":
    main()
