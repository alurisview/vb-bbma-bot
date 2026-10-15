import logging
import sys
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from flask import Flask

BOT_TOKEN = "YOUR_BOT_TOKEN"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# បង្កើត Flask App តូចមួយ ដើម្បីបំពេញលក្ខខណ្ឌ Web Service របស់ Render (Free)
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Bot is running!"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_name = update.effective_user.first_name
    welcome_message = (
        f"Hello {user_name}! 👋\n\n"
        "I am your official XAUUSD Signal Bot.\n"
        "Please type /signal to get the latest gold signal."
    )
    await update.message.reply_text(welcome_message)

async def send_signal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    signal_message = (
        "🟡 *GOLD (XAUUSD) VIP SIGNAL* 🟡\n\n"
        "📊 *Asset:* XAUUSD / GOLD\n"
        "⚡ *Signal Type:* SELL LIMIT / SHORT\n"
        "📉 *Entry Price:* 2,380.00 - 2,383.00\n\n"
        "🛑 *Stop Loss (SL):* 2,390.00\n"
        "🎯 *Take Profit 1 (TP1):* 2,375.00\n"
        "🎯 *Take Profit 2 (TP2):* 2,368.00\n"
        "🎯 *Take Profit 3 (TP3):* 2,355.00\n\n"
        "⚠️ *Risk Warning: Always use proper risk management.*"
    )
    try:
        await update.message.reply_text(signal_message, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        await update.message.reply_text("Sorry, an error occurred.")

def main() -> None:
    if BOT_TOKEN == "YOUR_BOT_TOKEN":
        print("⚠️ Please set your Bot Token first!")
        return

    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("signal", send_signal))

    # ចាប់ផ្តើម Bot តាមបែប Polling ក្នុង Background Thread ស្របពេលជាមួយ Flask
    application.run_polling()

if __name__ == "__main__":
    import threading
    # រត់ Telegram Bot ក្នុង Thread ដាច់ដោយឡែក
    bot_thread = threading.Thread(target=main)
    bot_thread.start()
    
    # យក Port ពី Render ឬប្រើប្រាស់ Port 10000 សម្រាប់ Local
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)
