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

# Static responses
STATIC_RESPONSES = {
    "wifi": "RKC Delegates\nSSID: mandir\nPassword: (open) no password",
    "transportation": "Today, shuttles to the hotel will begin after dinner at 8:30 PM till 9:30 PM.",
    "common_session_seating": "Common session seating will be updated shortly!",
    "block_schedule": "The block schedule is currently being finalized. Please check back later.",
    "today_food_menu": "Today's menu includes:\nBreakfast: Idli & Sambar\nLunch: Paneer Tikka\nDinner: Veg Biryani & Raita."
}

# Command: Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message with interactive buttons."""
    keyboard = [
        [InlineKeyboardButton("Wi-Fi Information", callback_data="wifi")],
        [InlineKeyboardButton("Transportation Details", callback_data="transportation")],
        [InlineKeyboardButton("Common Session Seating", callback_data="common_session_seating")],
        [InlineKeyboardButton("Event Schedule", callback_data="event_schedule")],
        [InlineKeyboardButton("Breakout Schedule", callback_data="breakout_schedule")],
        [InlineKeyboardButton("Today's Food Menu", callback_data="today_food_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Welcome to the RKC 2025 Assistant Bot!\nSelect an option below to get information:",
        reply_markup=reply_markup
    )

# Callback Handler for Static Responses
async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()  # Acknowledge the button click
    response = STATIC_RESPONSES.get(query.data, "Sorry, I couldn't find the information.")
    await query.edit_message_text(text=response)

# Command handlers for static responses
async def wifi_information(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(STATIC_RESPONSES["wifi"])

async def transportation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(STATIC_RESPONSES["transportation"])

async def common_session_seating(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(STATIC_RESPONSES["common_session_seating"])

async def block_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(STATIC_RESPONSES["block_schedule"])

async def today_food_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(STATIC_RESPONSES["today_food_menu"])

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

async def breakout_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetch and display the breakout schedule."""
    query = update.callback_query
    await query.answer()

    try:
        response = requests.get(f"{BASE_URL}/mandals")
        if response.status_code != 200:
            await query.edit_message_text("Failed to fetch breakout schedule. Please try again later.")
            return

        mandals = response.json()["mandals"]
        keyboard = [[InlineKeyboardButton(mandal, callback_data=f"mandal:{mandal}")] for mandal in mandals]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text("Select a Mandal:", reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error fetching breakout schedule: {str(e)}")
        await query.edit_message_text("Error fetching breakout schedule. Please try again later.")


# Command: Schedule
async def event_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetch and display the event schedule."""
    query = update.callback_query
    await query.answer()

    try:
        response = requests.get(f"{BASE_URL}/schedule")
        if response.status_code != 200:
            await query.edit_message_text("Failed to fetch the event schedule. Please try again later.")
            return

        schedule = response.json()
        message = "*Event Schedule*\n\n"
        for day in schedule:
            message += f"📅 *{day['day']}*\n"
            for session in day['sessions']:
                message += f"- {session['time']}: {session['title']} (Room: {session.get('room', 'TBD')})\n"
            message += "\n"

        await query.edit_message_text(message, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error fetching event schedule: {str(e)}")
        await query.edit_message_text("Error fetching the event schedule. Please try again later.")

# Command: Mandals
async def list_mandals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        response = requests.get(f"{BASE_URL}/mandals")
        if response.status_code != 200:
            await update.message.reply_text("Failed to fetch mandals. Please try again later.")
            return
        
        mandals = response.json()["mandals"]
        keyboard = [[InlineKeyboardButton(mandal, callback_data=f"mandal:{mandal}")] for mandal in mandals]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text("Select a Mandal:", reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error fetching mandals: {str(e)}")
        await update.message.reply_text("Error fetching mandals. Please try again later.")

# Callback Handler: Mandal Selection
async def handle_mandal_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    mandal_name = query.data.split(":")[1]

    try:
        response = requests.get(f"{BASE_URL}/mandals/{mandal_name}/tracks")
        if response.status_code != 200:
            await query.edit_message_text("Failed to fetch tracks. Please try again later.")
            return

        tracks = response.json()["tracks"]
        keyboard = [[InlineKeyboardButton(track, callback_data=f"track:{mandal_name}:{track}")] for track in tracks]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.answer()
        await query.edit_message_text(f"Tracks for {mandal_name}:", reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error fetching tracks: {str(e)}")
        await query.edit_message_text("Error fetching tracks. Please try again later.")

# Callback Handler: Track Selection
async def handle_track_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    mandal_name, track_name = query.data.split(":")[1:]

    try:
        response = requests.get(f"{BASE_URL}/mandals/{mandal_name}/tracks/{track_name}/sessions")
        if response.status_code != 200:
            await query.edit_message_text("Failed to fetch sessions. Please try again later.")
            return

        sessions = response.json()["sessions"]
        message = f"Sessions for {track_name}:\n"
        for session in sessions:
            message += f"- {session['name']} ({session['time']} in Room {session.get('room', 'TBD')})\n"

        await query.answer()
        await query.edit_message_text(message)
    except Exception as e:
        logger.error(f"Error fetching sessions: {str(e)}")
        await query.edit_message_text("Error fetching sessions. Please try again later.")


def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    # application.add_handler(CommandHandler("list_sevas", list_sevas))
    # application.add_handler(CallbackQueryHandler(join_seva_callback))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_button_click))
    application.add_handler(CallbackQueryHandler(event_schedule, pattern="^event_schedule$"))
    application.add_handler(CallbackQueryHandler(breakout_schedule, pattern="^breakout_schedule$"))
    application.add_handler(CallbackQueryHandler(handle_mandal_selection, pattern="^mandal:"))
    application.add_handler(CallbackQueryHandler(handle_track_selection, pattern="^track:"))



    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()

