import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
conn = sqlite3.connect('bot.db')
cursor = conn.cursor()

# Create tables
cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, points INTEGER DEFAULT 0, referred_by INTEGER)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS referrals (user_id INTEGER, referred_id INTEGER, PRIMARY KEY (user_id, referred_id))''')
conn.commit()

# Bot token and channel username
BOT_TOKEN = '7178545425:AAHUUxXbKXqDwSt_BYcq31HAUJkvx2qeL6U'
CHANNEL_USERNAME = '@dailynetflixcookiesfree'
ADMIN_CHANNEL_ID = '5577450357'

# Start command handler
def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not user:
        return
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user.id,))
    conn.commit()
    keyboard = [[InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_USERNAME}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(f"Welcome {user.first_name}! Please join our channel to use the bot.", reply_markup=reply_markup)

# Home command handler
def home(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("🆔 Account", callback_data='account')],
        [InlineKeyboardButton("🙌 Referrals", callback_data='referrals'), InlineKeyboardButton("🍪 Withdraw", callback_data='withdraw')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Welcome to the bot. Use the commands below:", reply_markup=reply_markup)

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    data = query.data

    if data == 'account':
        show_account(query, context)
    elif data == 'referrals':
        show_referrals(query, context)
    elif data == 'withdraw':
        handle_withdraw(query, context)

def show_account(query, context):
    user = query.from_user
    cursor.execute("SELECT points FROM users WHERE user_id = ?", (user.id,))
    points = cursor.fetchone()[0]
    query.edit_message_text(text=f"Your account details:\n\nUsername: {user.username}\nPoints: {points}")

def show_referrals(query, context):
    user = query.from_user
    referral_link = f"https://t.me/yourbot?start={user.id}"
    query.edit_message_text(text=f"Invite your friends with this link: {referral_link}")

def handle_withdraw(query, context):
    user = query.from_user
    cursor.execute("SELECT points FROM users WHERE user_id = ?", (user.id,))
    points = cursor.fetchone()[0]
    if points < 3:
        query.edit_message_text(text="You need at least 3 points to withdraw.")
    else:
        cursor.execute("UPDATE users SET points = points - 3 WHERE user_id = ?", (user.id,))
        conn.commit()
        context.bot.send_message(ADMIN_CHANNEL_ID, f"User {user.username} ({user.id}) has withdrawn Netflix Cookies.")
        query.edit_message_text(text="Your cookies will be sent to you [6AM-10PM IST].")

# Referral handling
def handle_referral(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    args = context.args
    if not user or not args:
        return
    referred_by = args[0]
    cursor.execute("INSERT OR IGNORE INTO users (user_id, referred_by) VALUES (?, ?)", (user.id, referred_by))
    cursor.execute("INSERT INTO referrals (user_id, referred_id) VALUES (?, ?)", (referred_by, user.id))
    cursor.execute("UPDATE users SET points = points + 1 WHERE user_id = ?", (referred_by,))
    conn.commit()

# Check if user joined the channel
def check_channel_membership(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not user:
        return
    member = context.bot.get_chat_member(CHANNEL_USERNAME, user.id)
    if member.status not in ['member', 'administrator', 'creator']:
        keyboard = [[InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_USERNAME}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("Please join the channel to use the bot.", reply_markup=reply_markup)
        return
    context.bot.send_message(user.id, "Thank you for joining the channel! You can now use the bot.")

def main() -> None:
    updater = Updater(BOT_TOKEN)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("home", home))
    dispatcher.add_handler(CommandHandler("start", handle_referral, pass_args=True))
    dispatcher.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
