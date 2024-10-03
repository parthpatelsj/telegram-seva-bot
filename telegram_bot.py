import logging
import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

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
    """Fetch and display the list of Seva slots from the backend with sign-up buttons."""
    try:
        response = requests.get(f"{BASE_URL}/sevas")
        sevas = response.json()

        if not sevas:
            await update.message.reply_text("No Seva slots available at the moment.")
        else:
            keyboard = []
            for seva in sevas:
                # Create a button for each Seva with the seva_id passed as callback data
                keyboard.append([InlineKeyboardButton(f"{seva['seva_name']} - {seva['time_slot']} on {seva['date_slot']}", callback_data=str(seva['id']))])

            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text("Available Seva slots:", reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"Error fetching Seva slots: {str(e)}")
        await update.message.reply_text(f"Error fetching Seva slots: {str(e)}")

async def join_seva_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the callback when the user selects a Seva slot to join."""
    query = update.callback_query
    seva_id = query.data  # The seva_id is passed as callback data

    # Ask the user to confirm their name for signing up
    user_name = update.effective_user.first_name or "Anonymous"
    await query.answer()  # Acknowledge the button press

    # Send a POST request to the backend to join the seva
    try:
        response = requests.post(
            f"{BASE_URL}/join_seva",
            json={'name': user_name, 'seva_id': seva_id}
        )
        data = response.json()

        await query.edit_message_text(text=f"{data['message']}")

    except Exception as e:
        logger.error(f"Error joining Seva: {str(e)}")
        await query.edit_message_text(text="Error joining Seva. Please try again later.")



def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("list_sevas", list_sevas))
    application.add_handler(CallbackQueryHandler(join_seva_callback))
    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()

