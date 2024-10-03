import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler

# Get your bot token from the environment variable
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
BASE_URL = "https://telegram-seva-bot-16ec0e933bf1.herokuapp.com"

# Command to list the Seva slots
async def list_sevas(update: Update, context):
    try:
        response = requests.get(f"{BASE_URL}/sevas")
        sevas = response.json()

        if not sevas:
            await update.message.reply_text("No Seva slots available at the moment.")
        else:
            seva_list = "\n".join([f"{seva[1]}: {seva[2]} ({seva[3]})" for seva in sevas])  # Adjust indices based on your data
            await update.message.reply_text(f"Available Seva slots:\n{seva_list}")
    except Exception as e:
        await update.message.reply_text(f"Error fetching Seva slots: {str(e)}")

# Command to start the bot and send welcome message
async def start(update: Update, context):
    await update.message.reply_text("Welcome to the Seva Bot! Use /list_sevas to see available Seva slots.")

def main():
    # Create the Application and pass the bot's token
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add command handlers to the application
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("list_sevas", list_sevas))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()

