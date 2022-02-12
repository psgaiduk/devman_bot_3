from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ReplyKeyboardMarkup
import os
from dotenv import load_dotenv
from create_question_answer import get_questions_and_answers
import redis


def start(bot, update):
    custom_keyboard = [['New question', 'Surrender'], ['My Score']]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    bot.send_message(chat_id=update.message.chat.id, text="Custom Keyboard Test", reply_markup=reply_markup)


def help(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def quiz(bot, update):
    redis_password = os.environ['REDIS_PASSWORD']
    r = redis.Redis(host='redis-19360.c240.us-east-1-3.ec2.cloud.redislabs.com', port=19360, db=0,
                    password=redis_password, decode_responses=True)

    if update.message.text == 'New question':
        question, answer = get_questions_and_answers()
        r.set(update.message.chat.id, answer)
        bot.send_message(chat_id=update.message.chat.id, text=question)
    else:
        text = 'Неправильно… Попробуешь ещё раз?'
        answer = r.get(update.message.chat.id)
        if update.message.text == answer:
            text = 'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»'

        update.message.reply_text(text)


# def error(bot, update, error):
#     """Log Errors caused by Updates."""
#     logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)

    token_telegram = os.environ['TELEGRAM_TOKEN']

    updater = Updater(token_telegram)
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, quiz))

    # log all errors
    # dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
