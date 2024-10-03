import logging
import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get the bot token and base URL for the API
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
BASE_URL = "https://telegram-seva-bot-16ec0e933bf1.herokuapp.com"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the bot starts."""
    await update.message.reply_text(
        "Welcome to the Seva Bot! Use /list_sevas to see available Seva slots."
    )

async def list_sevas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetch and display the list of Seva slots from the backend."""
    try:
        response = requests.get(f"{BASE_URL}/sevas")
        sevas = response.json()

        if not sevas:
            await update.message.reply_text("No Seva slots available at the moment.")
        else:
            seva_list = "\n".join([f"{seva[1]}: {seva[2]} ({seva[3]})" for seva in sevas])  # Adjust indices if needed
            await update.message.reply_text(f"Available Seva slots:\n{seva_list}")
    except Exception as e:
        logger.error(f"Error fetching Seva slots: {str(e)}")
        await update.message.reply_text(f"Error fetching Seva slots: {str(e)}")

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("list_sevas", list_sevas))

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()

