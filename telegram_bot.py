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
    "wifi": "📶 *Wi-Fi Information*\nSSID: `mandir`\nPassword: `(open)` no password",
    "transportation": "🚌 *Transportation Details*\nToday, shuttles to the hotel will begin after dinner at *8:30 PM* till *9:30 PM*.",
    "common_session_seating": "📍 *Common Session Seating*\nSeating details will be updated shortly!",
    "today_food_menu": "🍴 *Today's Food Menu*\n- 🥞 *Breakfast*: Idli & Sambar\n- 🥗 *Lunch*: Paneer Tikka\n- 🍛 *Dinner*: Veg Biryani & Raita"
}

# Command: Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message with interactive buttons."""
    keyboard = [
        [InlineKeyboardButton("📶 Wi-Fi Information", callback_data="wifi")],
        [InlineKeyboardButton("🚌 Transportation Details", callback_data="transportation")],
        [InlineKeyboardButton("📍 Common Session Seating", callback_data="common_session_seating")],
        [InlineKeyboardButton("📅 Event Schedule", callback_data="event_schedule")],
        [InlineKeyboardButton("📘 Breakout Schedule", callback_data="breakout_schedule")],
        [InlineKeyboardButton("🍴 Food Menu", callback_data="food_menu")],
        [InlineKeyboardButton("Your Year In Review", web_app={"url": "https://telegram-seva.netlify.app"})]

    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 Welcome to the *RKC 2025 Assistant Bot*!\n\nSelect an option below to get information:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# Callback Handler for Static Responses
async def handle_static_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    response = {
        "wifi": "📶 *Wi-Fi Information*\nSSID: `mandir`\nPassword: `(open)` no password",
        "transportation": "🚌 *Transportation Details*\nToday, shuttles to the hotel will begin after dinner at *8:30 PM* till *9:30 PM*.",
        "common_session_seating": "📍 *Common Session Seating*\nSeating details will be updated shortly!"
    }.get(query.data, "Sorry, I couldn't find the information.")
    await query.edit_message_text(text=response, parse_mode="Markdown")


# Callback Handler: Event Schedule
async def event_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Prompt the user to select a specific day for the schedule."""
    query = update.callback_query
    await query.answer()  # Acknowledge the button click

    try:
        response = requests.get(f"{BASE_URL}/schedule")
        if response.status_code != 200:
            await query.edit_message_text("Failed to fetch the event schedule. Please try again later.")
            return

        schedule = response.json()

        # Create buttons for each available day
        keyboard = [[InlineKeyboardButton(day["day"], callback_data=f"event_schedule_day:{day['day']}")] for day in schedule]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text("📅 Select a day to view the schedule:", reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error fetching event schedule: {str(e)}")
        await query.edit_message_text("Error fetching the event schedule. Please try again later.")

# Callback Handler: Day-Specific Schedule
async def event_schedule_day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetch and display the schedule for a specific day."""
    query = update.callback_query
    _, selected_day = query.data.split(":")
    await query.answer()  # Acknowledge the button click

    try:
        response = requests.get(f"{BASE_URL}/schedule")
        if response.status_code != 200:
            await query.edit_message_text("Failed to fetch the event schedule. Please try again later.")
            return

        schedule = response.json()

        # Find the selected day's schedule
        selected_schedule = next((day for day in schedule if day["day"] == selected_day), None)
        if not selected_schedule:
            await query.edit_message_text(f"No schedule found for {selected_day}.")
            return

        # Format the schedule
        message = f"*📅 Schedule for {selected_day}*\n\n"
        for session in selected_schedule["sessions"]:
            message += f"⏰ {session['time']} - *{session['title']}*\n"
        await query.edit_message_text(message, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error fetching schedule for {selected_day}: {str(e)}")
        await query.edit_message_text(f"Error fetching the schedule for {selected_day}. Please try again later.")

# Callback Handler: Breakout Schedule
async def breakout_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()  # Acknowledge the button click
    try:
        response = requests.get(f"{BASE_URL}/mandals")
        if response.status_code != 200:
            await query.edit_message_text("Failed to fetch breakout schedule. Please try again later.")
            return
        mandals = response.json()["mandals"]
        keyboard = [[InlineKeyboardButton(f"📘 {mandal}", callback_data=f"mandal:{mandal}")] for mandal in mandals]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("👥 Select a Mandal for Breakout Sessions:", reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error fetching breakout schedule: {str(e)}")
        await query.edit_message_text("Error fetching breakout schedule. Please try again later.")

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
        keyboard = [[InlineKeyboardButton(f"🔹 {track}", callback_data=f"track:{mandal_name}:{track}")] for track in tracks]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"🔍 Tracks for {mandal_name}:", reply_markup=reply_markup)
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
        message = f"*📘 Sessions for {track_name}*\n\n"
        for session in sessions:
            message += f"🔸 *{session['name']}*\n  ⏰ {session['time']}\n  🏫 Room: {session.get('room', 'TBD')}\n\n"
        await query.edit_message_text(message, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error fetching sessions: {str(e)}")
        await query.edit_message_text("Error fetching sessions. Please try again later.")

# Callback Handler: Food Menu
async def food_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    try:
        # Fetch the full menu from the backend
        response = requests.get(f"{BASE_URL}/menu")
        if response.status_code != 200:
            await query.edit_message_text("Failed to fetch the food menu. Please try again later.")
            return

        menu = response.json()["menu"]

        # Create a date picker with InlineKeyboardButtons
        keyboard = [[InlineKeyboardButton(date, callback_data=f"food_menu_date:{date}")] for date in menu.keys()]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text("🍴 Select a date to view the food menu:", reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error fetching food menu: {str(e)}")
        await query.edit_message_text("Error fetching the food menu. Please try again later.")

# Callback Handler: Date-specific Food Menu
async def food_menu_by_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    _, selected_date = query.data.split(":")
    await query.answer()

    try:
        # Fetch menu for the selected date from the backend
        response = requests.get(f"{BASE_URL}/menu/{selected_date}")
        if response.status_code != 200:
            await query.edit_message_text("Menu for the selected date not found.")
            return

        menu = response.json().get(selected_date, {})
        message = f"*🍴 Food Menu for {selected_date}*\n\n"

        for meal, details in menu.items():
            message += f"🍽 *{meal.capitalize()}* (Timing: {details.get('timing', 'N/A')})\n"
            for item in details.get("items", []):
                message += f"- {item['name']} ({item['type']})\n"
            message += "\n"

        await query.edit_message_text(message, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error fetching menu for {selected_date}: {str(e)}")
        await query.edit_message_text("Error fetching the menu for the selected date. Please try again later.")

# Callback Handler: Year In Review
async def year_in_review(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()  # Acknowledge the button click

    await query.edit_message_text(
        "📊 Opening your Year In Review...\n[Click here to view it](https://telegram-seva.netlify.app)",
        parse_mode="Markdown"
    )

# Main
def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_static_response, pattern="^(wifi|transportation|common_session_seating|today_food_menu)$"))
    application.add_handler(CallbackQueryHandler(event_schedule, pattern="^event_schedule$"))
    application.add_handler(CallbackQueryHandler(event_schedule_day, pattern="^event_schedule_day:"))
    application.add_handler(CallbackQueryHandler(breakout_schedule, pattern="^breakout_schedule$"))
    application.add_handler(CallbackQueryHandler(handle_mandal_selection, pattern="^mandal:"))
    application.add_handler(CallbackQueryHandler(handle_track_selection, pattern="^track:"))
    application.add_handler(CallbackQueryHandler(food_menu, pattern="^food_menu$"))
    application.add_handler(CallbackQueryHandler(food_menu_by_date, pattern="^food_menu_date:"))
    application.add_handler(CallbackQueryHandler(year_in_review, pattern="^year_in_review$"))


    application.run_polling()

if __name__ == "__main__":
    main()
