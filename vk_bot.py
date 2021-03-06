from vk_api import VkApi, longpoll, exceptions
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import os
import time
from dotenv import load_dotenv
import random
from logging import getLogger, basicConfig, INFO
from logger_handler import BotHandler
from redis_work import RedisDB

logger = getLogger('app_logger')


def send_new_question(r, vk_api, event, keyboard):
    user = r.get_user(f'vk_{event.user_id}')
    right_answers = int(user['user_score_right'])
    wrong_answers = int(user['user_score_wrong'])
    logger.debug(f'Пользователь нажал кнопку новый вопрос')
    question_id, question = r.get_random_question()
    logger.debug(f'Получили вопрос и ответ\n{question_id}\n{question}')
    r.update_user(f'vk_{event.user_id}', question_id, right_answers, wrong_answers)
    logger.debug(f'Записали данные в БД')
    send_message(vk_api, event, keyboard, f'Вопрос:\n{question}')


def send_message(vk_api, event, keyboard, text):
    result = vk_api.messages.send(
        user_id=event.user_id,
        message=text,
        keyboard=keyboard.get_keyboard(),
        random_id=random.randint(1, 1000)
    )
    logger.debug(f'Отправил сообщение в ВК {result}')


def surrender(r, vk_api, event, keyboard):
    user = r.get_user(f'vk_{event.user_id}')
    right_answers = int(user['user_score_right'])
    wrong_answers = int(user['user_score_wrong']) + 1
    question_id = user['user_last_question_id']
    logger.debug(f'Пользователь нажал кнопку "Сдаться"')
    r.update_user(f'vk_{event.user_id}', question_id, right_answers, wrong_answers)
    _, answer = r.get_question_and_answer(question_id)
    logger.debug(f'Получили ответ для этого пользователя из БД {answer}')
    text = f'Правильный ответ:\n{answer}'
    send_message(vk_api, event, keyboard, text)
    send_new_question(r, vk_api, event, keyboard)


def check_answer(r, vk_api, event, keyboard):
    user = r.get_user(f'vk_{event.user_id}')
    logger.debug(f'Пользователь пишет ответ')
    question_id = user['user_last_question_id']
    _, answer = r.get_question_and_answer(question_id)
    logger.debug(f'Получили ответ для этого пользователя из БД {answer}')
    text = 'Неправильно… Попробуешь ещё раз?'
    if answer == event.message:
        right_answers = int(user['user_score_right']) + 1
        wrong_answers = int(user['user_score_wrong'])
        r.update_user(f'vk_{event.user_id}', question_id, right_answers, wrong_answers)
        text = 'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»'
        logger.debug(f'Это правильный ответ {event.message}')

    send_message(vk_api, event, keyboard, text)


def get_my_score(r, vk_api, event, keyboard):
    user = r.get_user(f'vk_{event.user_id}')
    logger.debug(f'Пользователь хочет узнать свой счёт')
    right_answers = int(user['user_score_right'])
    wrong_answers = int(user['user_score_wrong'])
    text = f'Вот твои результаты\nПравильных ответов: {right_answers}\nНеправильных ответов: {wrong_answers}'

    send_message(vk_api, event, keyboard, text)


def main():
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)

    token_vk = os.environ['VK_TOKEN']
    logger_token = os.environ['TOKEN_TELEGRAM_LOGGER']
    logger_chat_id = os.environ['CHAT_ID']
    redis_port = int(os.environ['REDIS_PORT'])
    redis_host = os.environ['REDIS_HOST']
    redis_password = os.environ['REDIS_PASSWORD']
    r = RedisDB(host=redis_host, port=redis_port, password=redis_password)

    basicConfig(level=INFO, format='{asctime} - {levelname} - {name} - {message}', style='{')
    logger.addHandler(BotHandler(logger_token, logger_chat_id))

    r.check_db()

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
                if event.message == 'Новый вопрос':
                    send_new_question(r, vk_api, event, keyboard)
                elif event.message == 'Сдаться':
                    surrender(r, vk_api, event, keyboard)
                elif event.message == 'Мой счёт':
                    get_my_score(r, vk_api, event, keyboard)
                else:
                    check_answer(r, vk_api, event, keyboard)
        except Exception as e:
            time.sleep(1)
            logger.exception(e)


if __name__ == "__main__":
    main()
