from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, RegexHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
import os
from dotenv import load_dotenv
from logging import getLogger, basicConfig, INFO
from logger_handler import BotHandler
from redis_work import RedisDB
from functools import partial

logger = getLogger('app_logger')
QUIZ = range(1)


def start(bot, update):
    logger.debug('Пользователь начал работу с ботом')
    custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счёт']]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    bot.send_message(chat_id=update.message.chat.id, text="Игра началась", reply_markup=reply_markup)

    return QUIZ


def handle_new_question_request(bot, update, r):
    logger.debug('Пользователь нажал кнопку новый вопрос')
    user = r.get_user(f'tg_{update.message.chat.id}')
    question_id, question = r.get_random_question()
    logger.debug(f'Получили вопрос и ответ\n{question_id}\n{question}')
    r.update_user(f'tg_{update.message.chat.id}', question_id, user['user_score_right'], user['user_score_wrong'])
    logger.debug(f'Записали данные в БД')
    result = bot.send_message(chat_id=update.message.chat.id, text=question)
    logger.debug(f'Отправили сообщение в чат\n{result}')


def handle_surrender(bot, update, r):
    logger.debug('Пользователь нажал кнопку "Сдаться"')
    user = r.get_user(f'tg_{update.message.chat.id}')
    if user:
        question_id = user['user_last_question_id']
        right_answers = int(user['user_score_right'])
        wrong_answers = int(user['user_score_wrong']) + 1
        r.update_user(f'tg_{update.message.chat.id}', question_id, right_answers, wrong_answers)
        _, answer = r.get_question_and_answer(question_id)
        logger.debug(f'Получили сохранённый ответ из БД для этого пользователя:\n{answer}')
        text = f'Правильный ответ:\n{answer}'
        result = update.message.reply_text(text)
        logger.debug(f'Отправили сообщение в чат\n{result}')
        handle_new_question_request(bot, update, r)
    else:
        logger.warning(f'Не нашли такого пользователя в БД\n{update.message.chat.id}')
        handle_new_question_request(bot, update, r)


def handle_solution_attempt(bot, update, r):
    logger.debug(f'Пользователь пишет ответ {update.message.text}')
    text = 'Неправильно… Попробуешь ещё раз?'
    user = r.get_user(f'tg_{update.message.chat.id}')
    if user:
        question_id = user['user_last_question_id']
        _, answer = r.get_question_and_answer(question_id)
        if update.message.text == answer:
            right_answers = int(user['user_score_right']) + 1
            wrong_answers = int(user['user_score_wrong'])
            r.update_user(f'tg_{update.message.chat.id}', question_id, right_answers, wrong_answers)
            text = 'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»'
            logger.debug(f'Это правильный ответ {answer}')

        result = update.message.reply_text(text)
        logger.debug(f'Отправили сообщение в чат\n{result}')
    else:
        logger.warning(f'Не нашли такого пользователя в БД\n{update.message.chat.id}')
        update.message.reply_text('Похоже ты ещё не начал с нами играть, вот тебе вопрос:')
        handle_new_question_request(bot, update, r)


def handle_get_my_score(bot, update, r):
    logger.debug(f'Пользователь просит сказать его счёт {update.message.text}')
    user = r.get_user(f'tg_{update.message.chat.id}')

    right_answers = int(user['user_score_right'])
    wrong_answers = int(user['user_score_wrong'])
    text = f'Вот твои результаты\nПравильных ответов: {right_answers}\nНеправильных ответов: {wrong_answers}'
    logger.debug(f'Подготовили сообщение {text}')
    result = update.message.reply_text(text)
    logger.debug(f'Отправили сообщение в чат\n{result}')


def cancel(_, update):
    update.message.reply_text('Stop working', reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def main():

    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)

    token_telegram = os.environ['TELEGRAM_TOKEN']
    logger_token = os.environ['TOKEN_TELEGRAM_LOGGER']
    logger_chat_id = os.environ['CHAT_ID']
    redis_port = int(os.environ['REDIS_PORT'])
    redis_host = os.environ['REDIS_HOST']
    redis_password = os.environ['REDIS_PASSWORD']
    r = RedisDB(host=redis_host, port=redis_port, password=redis_password)
    r.check_db()

    basicConfig(level=INFO, format='{asctime} - {levelname} - {name} - {message}', style='{')
    logger.addHandler(BotHandler(logger_token, logger_chat_id))

    logger.info('Начало работы телеграмм бота Викторина')

    updater = Updater(token_telegram)
    dp = updater.dispatcher

    new_question = partial(handle_new_question_request, r=r)
    surrender = partial(handle_surrender, r=r)
    solution_attempt = partial(handle_solution_attempt, r=r)
    get_my_score = partial(handle_get_my_score, r=r)

    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            QUIZ: [
                RegexHandler('^(Новый вопрос)$', new_question),
                RegexHandler('^(Сдаться)$', surrender),
                RegexHandler('^(Мой счёт)$', get_my_score),
                MessageHandler(Filters.text, solution_attempt)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    ))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
