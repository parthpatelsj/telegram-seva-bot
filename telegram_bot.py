import os
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import requests

# Use environment variable for security
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def start(update, context):
    update.message.reply_text("Welcome to Seva Bot! Type /seva to see available seva slots.")

def get_sevas(update, context):
    response = requests.get('https://telegram-seva-bot-16ec0e933bf1.herokuapp.com/sevas')
    if response.status_code == 200:
        sevas = response.json()
        message = "\n".join([f"{seva[1]} - {seva[2]}: {seva[3]}" for seva in sevas])
    else:
        message = "Error fetching sevas."
    update.message.reply_text(message)

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("seva", get_sevas))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

