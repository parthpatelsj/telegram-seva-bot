import os
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Get your bot token from the environment variable
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
BASE_URL = "https://telegram-seva-bot-16ec0e933bf1.herokuapp.com"

# Command to list the Seva slots
def list_sevas(update: Update, context: CallbackContext):
    try:
        response = requests.get(f"{BASE_URL}/sevas")
        sevas = response.json()

        if not sevas:
            update.message.reply_text("No Seva slots available at the moment.")
        else:
            seva_list = "\n".join([f"{seva[1]}: {seva[2]} ({seva[3]})" for seva in sevas])  # Adjust indices based on your data
            update.message.reply_text(f"Available Seva slots:\n{seva_list}")
    except Exception as e:
        update.message.reply_text(f"Error fetching Seva slots: {str(e)}")

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome to the Seva Bot! Use /list_sevas to see available Seva slots.")

def main():
    updater = Updater(TELEGRAM_TOKEN, update_queue=False)

    dispatcher = updater.dispatcher

    # Command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("list_sevas", list_sevas))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

