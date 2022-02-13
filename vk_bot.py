from vk_api import VkApi, longpoll, exceptions
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import os
import time
from dotenv import load_dotenv
import random
import redis
from create_question_answer import get_questions_and_answers
from logging import getLogger, basicConfig, INFO
from logger_handler import BotHandler

logger = getLogger('app_logger')


def new_question(r, vk_api, event, keyboard):
    logger.debug(f'Пользователь нажал кнопку новый вопрос')
    question, answer = get_questions_and_answers()
    logger.debug(f'Получили вопрос и ответ\n{question}\n{answer}')
    insert_to_bd = r.set(event.user_id, answer)
    logger.debug(f'Записали данные в БД {insert_to_bd}')
    send_message(vk_api, event, keyboard, f'Вопрос:\n{question}')


def send_message(vk_api, event, keyboard, text):
    result = vk_api.messages.send(
        user_id=event.user_id,
        message=text,
        keyboard=keyboard.get_keyboard(),
        random_id=random.randint(1, 1000)
    )
    logger.debug(f'Отправил сообщение в ВК {result}')


def quiz_work(event, vk_api, keyboard):
    redis_host = os.environ['REDIS_HOST']
    redis_port = int(os.environ['REDIS_PORT'])
    redis_password = os.environ['REDIS_PASSWORD']
    r = redis.Redis(host=redis_host, port=redis_port, db=0, password=redis_password, decode_responses=True)

    if event.message == 'Новый вопрос':
        new_question(r, vk_api, event, keyboard)

    elif event.message == 'Сдаться':
        logger.debug(f'Пользователь нажал кнопку "Сдаться"')
        answer = r.get(event.user_id)
        logger.debug(f'Получили ответ для этого пользователя из БД {answer}')
        text = f'Правильный ответ:\n{answer}'
        send_message(vk_api, event, keyboard, text)
        new_question(r, vk_api, event, keyboard)

    else:
        logger.debug(f'Пользователь пишет ответ')
        answer = r.get(event.user_id)
        logger.debug(f'Получили ответ для этого пользователя из БД {answer}')
        text = 'Неправильно… Попробуешь ещё раз?'
        if answer == event.message:
            text = 'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»'
            logger.debug(f'Это правильный ответ {event.message}')

        send_message(vk_api, event, keyboard, text)


def main():
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)

    token_vk = os.environ['VK_TOKEN']
    logger_token = os.environ['TOKEN_TELEGRAM_LOGGER']
    logger_chat_id = os.environ['CHAT_ID']

    basicConfig(level=INFO, format='{asctime} - {levelname} - {name} - {message}', style='{')
    logger.addHandler(BotHandler(logger_token, logger_chat_id))

    logger.info('Начало работы ВК бота Викторина')

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
