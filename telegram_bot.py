from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, RegexHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
import os
from dotenv import load_dotenv
from logging import getLogger, basicConfig, INFO
from logger_handler import BotHandler
from redis_work import RedisDB

logger = getLogger('app_logger')
QUIZ = range(1)


def start(bot, update):
    logger.debug('Пользователь начал работу с ботом')
    custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счёт']]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    bot.send_message(chat_id=update.message.chat.id, text="Игра началась", reply_markup=reply_markup)

    return QUIZ


def connect_redis():
    redis_port = int(os.environ['REDIS_PORT'])
    redis_host = os.environ['REDIS_HOST']
    redis_password = os.environ['REDIS_PASSWORD']
    return RedisDB(host=redis_host, port=redis_port, password=redis_password)


def handle_new_question_request(bot, update):
    logger.debug('Пользователь нажал кнопку новый вопрос')
    r = get_data_from_redis()
    id_question, question = r.get_random_question()
    logger.debug(f'Получили вопрос и ответ\n{id_question}\n{question}')
    r.update_user(f'tg_{update.message.chat.id}', id_question)
    logger.debug(f'Записали данные в БД')
    result = bot.send_message(chat_id=update.message.chat.id, text=question)
    logger.debug(f'Отправили сообщение в чат\n{result}')


def handle_surrender(bot, update):
    logger.debug('Пользователь нажал кнопку "Сдаться"')
    r = get_data_from_redis()
    user = r.get_user(f'tg_{update.message.chat.id}')
    if user:
        question_id = user['user_last_question_id']
        answer = r.get_answer(question_id)
        logger.debug(f'Получили сохранённый ответ из БД для этого пользователя:\n{answer}')
        text = f'Правильный ответ:\n{answer}'
        result = update.message.reply_text(text)
        logger.debug(f'Отправили сообщение в чат\n{result}')
        handle_new_question_request(bot, update)
    else:
        logger.warning(f'Не нашли такого пользователя в БД\n{update.message.chat.id}')
        handle_new_question_request(bot, update)


def handle_solution_attempt(bot, update):
    logger.debug(f'Пользователь пишет ответ {update.message.text}')
    r = get_data_from_redis()
    text = 'Неправильно… Попробуешь ещё раз?'
    user = r.get_user(f'tg_{update.message.chat.id}')
    if user:
        question_id = user['user_last_question_id']
        answer = r.get_answer(question_id)
        if update.message.text == answer:
            text = 'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»'
            logger.debug(f'Это правильный ответ {answer}')

        result = update.message.reply_text(text)
        logger.debug(f'Отправили сообщение в чат\n{result}')
        update.message.reply_text(text)
    else:
        logger.warning(f'Не нашли такого пользователя в БД\n{update.message.chat.id}')
        update.message.reply_text('Похоже ты ещё не начал с нами играть, вот тебе вопрос:')
        handle_new_question_request(bot, update)


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

    basicConfig(level=INFO, format='{asctime} - {levelname} - {name} - {message}', style='{')
    logger.addHandler(BotHandler(logger_token, logger_chat_id))

    logger.info('Начало работы телеграмм бота Викторина')

    updater = Updater(token_telegram)
    dp = updater.dispatcher

    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            QUIZ: [
                RegexHandler('^(Новый вопрос)$', handle_new_question_request),
                RegexHandler('^(Сдаться)$', handle_surrender),
                MessageHandler(Filters.text, handle_solution_attempt)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    ))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
