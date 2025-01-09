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

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
BASE_URL = "https://telegram-seva-bot-16ec0e933bf1.herokuapp.com"

STATIC_RESPONSES = {
    "wifi": "RKC Delegates\nSSID: mandir\nPassword: (open) no password",
    "transportation": "Today, shuttles to the hotel will begin after dinner at 8:30 PM till 9:30 PM.",
    "common_session_seating": "Common session seating will be updated shortly!",
    "today_food_menu": "Today's menu includes:\nBreakfast: Idli & Sambar\nLunch: Paneer Tikka\nDinner: Veg Biryani & Raita."
}

# Command: Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
    await query.answer()
    response = STATIC_RESPONSES.get(query.data, "Sorry, I couldn't find the information.")
    await query.edit_message_text(text=response)

# Command: Event Schedule
async def event_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    try:
        response = requests.get(f"{BASE_URL}/schedule")
        if response.status_code != 200:
            await query.edit_message_text("Failed to fetch the event schedule.")
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
        logger.error(f"Error fetching schedule: {str(e)}")
        await query.edit_message_text("Error fetching the schedule.")

# Command: Breakout Schedule
async def breakout_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    try:
        response = requests.get(f"{BASE_URL}/mandals")
        if response.status_code != 200:
            await query.edit_message_text("Failed to fetch breakout schedule.")
            return
        mandals = response.json()["mandals"]
        keyboard = [[InlineKeyboardButton(mandal, callback_data=f"mandal:{mandal}")] for mandal in mandals]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Select a Mandal:", reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error fetching breakout schedule: {str(e)}")
        await query.edit_message_text("Error fetching breakout schedule.")

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

# Main
def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_button_click))
    application.add_handler(CallbackQueryHandler(event_schedule, pattern="^event_schedule$"))
    application.add_handler(CallbackQueryHandler(breakout_schedule, pattern="^breakout_schedule$"))
    application.add_handler(CallbackQueryHandler(handle_mandal_selection, pattern="^mandal:"))
    application.add_handler(CallbackQueryHandler(handle_track_selection, pattern="^track:"))

    application.run_polling()

if __name__ == "__main__":
    main()
