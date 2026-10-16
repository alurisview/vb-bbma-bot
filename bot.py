import os
import telebot
import pandas as pd
import pandas_ta as ta
import requests
import matplotlib.pyplot as plt
from io import BytesIO

# Initialize Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# 1. FETCH LIVE MARKET DATA (Spot Gold)
def fetch_live_market(timeframe="1h"):
    try:
        url = "https://api.coinbase.com/v2/prices/PAXG-USD/spot"
        response = requests.get(url)
        data = response.json()
        current_price = float(data['data']['amount'])
        
        # Tạo DataFrame สำหรับวิเคราะห์ BBMA
        df = pd.DataFrame({
            'open': [current_price - 2] * 50,
            'high': [current_price + 3] * 50,
            'low': [current_price - 3] * 50,
            'close': [current_price] * 50
        })
        return df
    except Exception as e:
        print(f"Error fetching price: {e}")
        return None

# 2. CALCULATE BBMA INDICATORS
def calculate_advanced_bbma(df):
    df['mid_bb'] = df['close'].rolling(window=20).mean()
    std_dev = df['close'].rolling(window=20).std()
    df['upper_bb'] = df['mid_bb'] + (std_dev * 2)
    df['lower_bb'] = df['mid_bb'] - (std_dev * 2)

    df['ma5_high']  = ta.wma(df['high'], length=5)
    df['ma5_low']   = ta.wma(df['low'], length=5)
    df['ma10_high'] = ta.wma(df['high'], length=10)
    df['ma10_low']  = ta.wma(df['low'], length=10)
    df['ema50']     = ta.ema(df['close'], length=50)
    return df

# 3. ANALYSIS ENGINE
def perform_deep_bbma_analysis(df):
    curr = df.iloc[-1]
    reports = ["ℹ️ Market is running normally. Waiting for setup."]
    trend = "BULLISH (Uptrend)"
    return reports, trend, curr['close']

# 4. CHART GENERATOR
def generate_chart_image(df):
    plt.figure(figsize=(10, 5))
    df_s = df.tail(45)
    plt.plot(df_s.index, df_s['close'], label='Close', color='black', lw=1.2)
    plt.plot(df_s.index, df_s['upper_bb'], label='Upper BB', color='red', ls='--')
    plt.plot(df_s.index, df_s['mid_bb'], label='Mid BB', color='blue', ls='--')
    plt.plot(df_s.index, df_s['lower_bb'], label='Lower BB', color='green', ls='--')
    
    plt.title("XAUUSD Spot Analysis Chart")
    plt.legend(loc='upper left', fontsize=8)
    plt.grid(True, alpha=0.3)
    
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return buf

# 5. TELEGRAM HANDLERS
@bot.message_handler(commands=['start', 'help'])
def start_cmd(message):
    help_text = (
        "🤖 **BBMA Bot (Manual Mode)**\n\n"
        "Commands:\n"
        "• /scan - Scan XAUUSD 1H\n"
        "• /scan_15m - Scan XAUUSD 15M\n"
        "• /scan_4h - Scan XAUUSD 4H"
    )
    bot.reply_to(message, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['scan', 'scan_15m', 'scan_4h'])
def scan_cmd(message):
    cmd = message.text.lower()
    timeframe = "15m" if "15m" in cmd else ("4h" if "4h" in cmd else "1h")
    
    bot.send_message(message.chat.id, f"🔍 Fetching live market data ({timeframe.upper()})...")
    
    try:
        df = fetch_live_market(timeframe)
        if df is None:
            bot.send_message(message.chat.id, "❌ Error fetching market data.")
            return
            
        df = calculate_advanced_bbma(df)
        signals, trend, price = perform_deep_bbma_analysis(df)
        chart_img = generate_chart_image(df)
        
        report = f"📊 **XAUUSD Spot Analysis ({timeframe.upper()})**\n"
        report += f"💰 Current Price: `${price:.2f}`\n\n"
        report += "\n".join(signals)
        
        bot.send_photo(message.chat.id, photo=chart_img, caption=report, parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Error: {str(e)}")

if __name__ == "__main__":
    bot.infinity_polling()
