import os
import telebot
import google.generativeai as genai

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

genai.configure(api_key=GEMINI_API_KEY)
# Using gemini-2.5-flash with rigorous technical instructions
model = genai.GenerativeModel('gemini-2.5-flash')

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Hello! Send an XAUUSD chart image to get an advanced BBMA Oma Ally multi-timeframe analysis signal.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        bot.reply_to(message, "📷 Chart received! AI is performing advanced multi-timeframe BBMA Oma Ally analysis...")
        
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        temp_image_path = "temp_chart.jpg"
        with open(temp_image_path, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        sample_file = genai.upload_file(path=temp_image_path, display_name="XAUUSD Advanced BBMA Chart")
        
        # Highly detailed and strict prompt for professional-grade BBMA analysis
        prompt = (
            "You are an expert institutional forex trader specializing strictly in the 'BBMA Oma Ally' strategy. "
            "Perform a rigorous, high-precision technical analysis of this XAUUSD chart across multiple timeframes (1D, 4H, 1H, 15M, and 5M if applicable).\n"
            "Evaluate strictly based on:\n"
            "1. Bollinger Bands (BB) setup: Expansion, Contraction, Standard deviation zones.\n"
            "2. Moving Averages: MA5/MA10 Low/High interactions, Middle Band (MB) validation.\n"
            "3. Market Phase identification: Look for Extreme (overextended price outside outer bands), "
            "MHV (Market Hilang Volume / failure to make new high/low with MA5/MA10 trapping), "
            "Reentry (continuation setup after MHV or Momentum), and Momentum candles (closing outside outer BB).\n"
            "4. Multi-timeframe confluence and market direction.\n\n"
            "You MUST format your final response strictly and only in the following template without any extra conversational text or markdown blocks outside the format:\n\n"
            "🛑 NEW SIGNAL FROM VB\n\n"
            "⭐️ XAUUSD (Timeframe)\n"
            "📊 (BUY/SELL) EntryPrice1 - EntryPrice2\n\n"
            "⛔️ SL : StopLossPrice\n\n"
            "✅ TP1 : TakeProfit1Price \n"
            "✅ TP2: TakeProfit2Price"
        )
        
        response = model.generate_content([sample_file, prompt])
        
        bot.send_message(message.chat.id, response.text)
        
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)
            
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Error processing chart: {str(e)}")

if __name__ == '__main__':
    print("Bot is running...")
    bot.infinity_polling()
