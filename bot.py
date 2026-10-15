import os
import telebot
from PIL import Image
from openai import OpenAI

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(
        message,
        "Hello! I am your XAUUSD trading analysis bot powered by BBMA Oma Ally and GPT-4o. "
        "Please send a chart image to get professional trading signals (Entry, SL, TP)!"
    )

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        sent_msg = bot.reply_to(message, "Chart received! AI is performing advanced multi-timeframe BBMA Oma Ally analysis...")

        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        image_path = "chart.jpg"
        with open(image_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        import base64
        def encode_image(path):
            with open(path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')

        base64_image = encode_image(image_path)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Analyze this XAUUSD trading chart strictly based on the BBMA Oma Ally strategy. "
                                "Identify current setups (such as Extreme, MHV, Reentry, Market Hilang Volume, etc.) "
                                "across the timeframes shown. Provide a professional trading signal including: "
                                "1. Setup Type / Market Condition\n"
                                "2. Entry Price zone\n"
                                "3. Stop Loss (SL)\n"
                                "4. Take Profit (TP1 & TP2)\n"
                                "Respond clearly and concisely."
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1024
        )

        analysis_result = response.choices[0].message.content
        bot.edit_message_text(analysis_result, chat_id=message.chat.id, message_id=sent_msg.message_id)

    except Exception as e:
        error_msg = f"Error processing chart: {str(e)}"
        print(error_msg)
        bot.reply_to(message, error_msg)

if __name__ == "__main__":
    print("Bot is starting and running 24/7 with OpenAI...")
    bot.infinity_polling()
