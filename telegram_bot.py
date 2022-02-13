from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, RegexHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
import os
from dotenv import load_dotenv
from create_question_answer import get_questions_and_answers
import redis

QUIZ = range(1)


def start(bot, update):
    custom_keyboard = [['New question', 'Surrender'], ['My Score']]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    bot.send_message(chat_id=update.message.chat.id, text="Custom Keyboard Test", reply_markup=reply_markup)

    return QUIZ


def get_data_from_redis():
    redis_password = os.environ['REDIS_PASSWORD']
    return redis.Redis(host='redis-19360.c240.us-east-1-3.ec2.cloud.redislabs.com', port=19360, db=0,
                       password=redis_password, decode_responses=True)


def handle_new_question_request(bot, update):
    r = get_data_from_redis()
    question, answer = get_questions_and_answers()
    r.set(update.message.chat.id, answer)
    bot.send_message(chat_id=update.message.chat.id, text=question)


def handle_surrender(bot, update):
    r = get_data_from_redis()
    answer = r.get(update.message.chat.id)
    text = f'Правильный ответ:\n{answer}'
    update.message.reply_text(text)
    handle_new_question_request(bot, update)


def handle_solution_attempt(_, update):
    r = get_data_from_redis()
    text = 'Неправильно… Попробуешь ещё раз?'
    answer = r.get(update.message.chat.id)
    if update.message.text == answer:
        text = 'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»'

    update.message.reply_text(text)


def cancel(_, update):
    update.message.reply_text('Stop working', reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def main():

    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)

    token_telegram = os.environ['TELEGRAM_TOKEN']

    updater = Updater(token_telegram)
    dp = updater.dispatcher

    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            QUIZ: [
                RegexHandler('^(New question)$', handle_new_question_request),
                RegexHandler('^(Surrender)$', handle_surrender),
                MessageHandler(Filters.text, handle_solution_attempt)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    ))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
