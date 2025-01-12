import logging
import os
import requests
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from datetime import datetime

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
BASE_URL = "https://telegram-seva-bot-16ec0e933bf1.herokuapp.com"

STATIC_RESPONSES = {
    "wifi": "📶 *Wi-Fi Information*\nSSID: `mandir`\nPassword: `(open)` no password",
    # "common_session_seating": "📍 *Common Session Seating*\nSeating details will be updated shortly!",
    "today_food_menu": "🍴 *Today's Food Menu*\n- 🥞 *Breakfast*: Idli & Sambar\n- 🥗 *Lunch*: Paneer Tikka\n- 🍛 *Dinner*: Veg Biryani & Raita"
}

# Command: Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message with interactive buttons."""
    keyboard = [
        [InlineKeyboardButton("📶 Wi-Fi Information", callback_data="wifi")],
        # [InlineKeyboardButton("📍 Common Session Seating", callback_data="common_session_seating")],
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
        # "common_session_seating": "📍 *Common Session Seating*\nSeating details will be updated shortly!"
    }.get(query.data, "Sorry, I couldn't find the information.")
    await query.edit_message_text(text=response, parse_mode="Markdown")


async def event_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetch and send the schedule image from the server."""
    query = update.callback_query
    await query.answer()  # Acknowledge the button click

    try:
        # Fetch the image from the server
        response = requests.get(f"{BASE_URL}/schedule_image")
        if response.status_code != 200:
            logger.error(f"Failed to fetch schedule image. Status code: {response.status_code}")
            await query.edit_message_text("Failed to retrieve the schedule. Please try again later.")
            return

        # Convert the image content to a file-like object
        image_data = BytesIO(response.content)
        image_data.seek(0)

        # Send the image to the user
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=InputFile(image_data, filename="schedule.jpg"),
            caption="📅 *Event Schedule*\nHere is the schedule for the event.",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error retrieving and sending schedule image: {str(e)}")
        await query.edit_message_text("Error retrieving the schedule. Please try again later.")
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

        # Hardcode buttons with exact strings from JSON
        keyboard = [
            [InlineKeyboardButton("Friday 1/17", callback_data="food_menu_date:Friday 1/17")],
            [InlineKeyboardButton("Saturday 1/18", callback_data="food_menu_date:Saturday 1/18")],
            [InlineKeyboardButton("Sunday 1/19", callback_data="food_menu_date:Sunday 1/19")],
        ]
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
        # Use the hardcoded date as-is to query the backend
        response = requests.get(f"{BASE_URL}/menu/{selected_date}")
        if response.status_code != 200:
            await query.edit_message_text("Menu for the selected date not found.")
            return

        # Fetch and display the menu
        menu = response.json().get(selected_date, {})
        message = f"*🍴 Food Menu for {selected_date}*\n\n"

        # Sort meals in breakfast, lunch, dinner order
        for meal in ["breakfast", "lunch", "dinner"]:
            details = menu.get(meal)
            if details:
                message += f"🍽 *{meal.capitalize()}* (Timing: {details.get('timing', 'N/A')})\n"
                for item in details.get("items", []):
                    message += f"- {item['name']} ({item['type']})\n"
                message += "\n"

        await query.edit_message_text(message.strip(), parse_mode="Markdown")
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

# Message Handler: Process Full Name Input
async def search_by_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.user_data.get("awaiting_full_name"):
        # Ignore messages not related to full name search
        return

    # Reset state
    context.user_data["awaiting_full_name"] = False

    # Extract full name
    full_name = update.message.text.strip()
    if " " not in full_name:
        await update.message.reply_text("Please provide both First Name and Last Name, separated by a space.")
        return

    first_name, last_name = full_name.split(" ", 1)

    # Send request to search_by_full_name API
    try:
        response = requests.post(f"{BASE_URL}/search_by_full_name", json={"First Name": first_name, "Last Name": last_name})

        if response.status_code != 200:
            await update.message.reply_text("Error fetching breakout details. Please try again later.")
            return

        data = response.json()
        if "options" in data:
            # Multiple matches found; ask for confirmation
            keyboard = [
                [InlineKeyboardButton(f"{opt['First Name']} {opt['Last Name']} ({opt['Center']}, {opt['Primary Seva']})",
                                      callback_data=f"confirm_breakout:{opt['First Name']}:{opt['Last Name']}:{opt['Center']}:{opt['Primary Seva']}")]
                for opt in data["options"]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(data["message"], reply_markup=reply_markup)
        else:
            await update.message.reply_text("No breakout sessions found for the provided name.")
    except Exception as e:
        logger.error(f"Error searching breakout by full name: {str(e)}")
        await update.message.reply_text("Error searching breakout by full name. Please try again later.")


# Callback Handler: Breakout Schedule
async def breakout_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()  # Acknowledge the button click

    try:
        # Extract Telegram user's first name
        user_first_name = update.effective_user.first_name

        # Fetch breakout matches using the first name
        response = requests.post(f"{BASE_URL}/search_breakouts", json={"first_name": user_first_name})

        if response.status_code != 200:
            await query.edit_message_text("Error fetching breakout schedule. Please try again later.")
            return

        data = response.json()

        # Check if the response requires user input (e.g., full name needed)
        if "prompt" in data:
            context.user_data["awaiting_full_name"] = True  # Set state for expecting full name
            await query.edit_message_text(
                f"{data['message']}\n\n{data['prompt']}",
                parse_mode="Markdown"
            )
        elif "options" in data:
            # Multiple or single match found; confirm identity
            keyboard = [
                [InlineKeyboardButton(f"{opt['First Name']} {opt['Last Name']} ({opt['Center']}, {opt['Primary Seva']})",
                                      callback_data=f"confirm_breakout:{opt['First Name']}:{opt['Last Name']}:{opt['Center']}:{opt['Primary Seva']}")]
                for opt in data["options"]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(data["message"], reply_markup=reply_markup)
        else:
            await query.edit_message_text("No breakout sessions found for you.")
    except Exception as e:
        logger.error(f"Error fetching breakout schedule: {str(e)}")
        await query.edit_message_text("Error fetching breakout schedule. Please try again later.")


# Callback Handler: Confirm Breakout
async def confirm_breakout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    try:
        # Extract confirmation details from callback data
        _, first_name, last_name, center, primary_seva = query.data.split(":")

        # Confirm and fetch breakout details
        response = requests.post(
            f"{BASE_URL}/confirm_breakout",
            json={
                "First Name": first_name,
                "Last Name": last_name,
                "Center": center,
                "Primary Seva": primary_seva
            }
        )

        if response.status_code != 200:
            await query.edit_message_text("Error confirming breakout details. Please try again later.")
            return

        data = response.json()
        details = data.get("details", {})
        message = (
            f"*Breakout Details Confirmed!*\n\n"
            f"👤 *Name:* {details.get('First Name')} {details.get('Last Name')}\n"
            f"🏠 *Center:* {details.get('Center')}\n"
            f"🛠 *Primary Seva:* {details.get('Primary Seva')}\n\n"
            f"📘 *Breakout Sessions:*\n"
            f"🔹 *Breakout #1:* {details.get('Breakout #1')}\n"
            f"🔹 *Breakout #2:* {details.get('Breakout #2')}\n"
            f"🔹 *Breakout #3:* {details.get('Breakout #3')}\n"
            f"🔹 *Goshthi:* {details.get('Goshthi')}"
        )
        await query.edit_message_text(message, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error confirming breakout details: {str(e)}")
        await query.edit_message_text("Error confirming breakout details. Please try again later.")

# Message Handler: Process Full Name Input
async def handle_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Check if the bot is awaiting a full name input
    if not context.user_data.get("awaiting_full_name"):
        return  # Ignore unrelated messages

    # Reset state
    context.user_data["awaiting_full_name"] = False

    # Extract full name from user input
    full_name = update.message.text.strip()
    if " " not in full_name:
        await update.message.reply_text("Please provide both First Name and Last Name, separated by a space.")
        return

    first_name, last_name = full_name.split(" ", 1)

    # Send request to search_by_full_name API
    try:
        response = requests.post(f"{BASE_URL}/search_by_full_name", json={"First Name": first_name, "Last Name": last_name})

        if response.status_code != 200:
            await update.message.reply_text("Error fetching breakout details. Please try again later.")
            return

        data = response.json()
        if "options" in data:
            # Multiple matches found; ask for confirmation
            keyboard = [
                [InlineKeyboardButton(f"{opt['First Name']} {opt['Last Name']} ({opt['Center']}, {opt['Primary Seva']})",
                                      callback_data=f"confirm_breakout:{opt['First Name']}:{opt['Last Name']}:{opt['Center']}:{opt['Primary Seva']}")]
                for opt in data["options"]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(data["message"], reply_markup=reply_markup)
        else:
            await update.message.reply_text("No breakout sessions found for the provided name.")
    except Exception as e:
        logger.error(f"Error searching breakout by full name: {str(e)}")
        await update.message.reply_text("Error searching breakout by full name. Please try again later.")


def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_static_response, pattern="^(wifi|today_food_menu)$"))
    application.add_handler(CallbackQueryHandler(event_schedule, pattern="^event_schedule$"))
    application.add_handler(CallbackQueryHandler(handle_mandal_selection, pattern="^mandal:"))
    application.add_handler(CallbackQueryHandler(handle_track_selection, pattern="^track:"))
    application.add_handler(CallbackQueryHandler(food_menu, pattern="^food_menu$"))
    application.add_handler(CallbackQueryHandler(food_menu_by_date, pattern="^food_menu_date:"))
    application.add_handler(CallbackQueryHandler(year_in_review, pattern="^year_in_review$"))
    application.add_handler(CallbackQueryHandler(breakout_schedule, pattern="^breakout_schedule$"))
    application.add_handler(CallbackQueryHandler(confirm_breakout, pattern="^confirm_breakout:"))

    # Add MessageHandler for full name input
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_full_name))

    # Start the bot
    application.run_polling()


if __name__ == "__main__":
    main()
