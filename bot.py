import os
import time
import threading
import telebot
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import matplotlib.pyplot as plt
from io import BytesIO

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

last_signal_state = {"1h": "", "15m": ""}

def fetch_live_market(timeframe="1h"):
    tf_map = {
        "15m": ("15m", "7d"),
        "1h": ("1h", "1mo"),
        "4h": ("1h", "3mo")
    }
    interval, period = tf_map.get(timeframe, ("1h", "1mo"))
    try:
        # ប្រើ XAU=X (Spot Gold) ដើម្បីឱ្យតម្លៃជិតស្និទ្ធនឹង MetaTrader
        ticker = yf.Ticker("XAU=X")
        df = ticker.history(period=period, interval=interval)
        
        if df.empty:
            return None
            
        df.reset_index(inplace=True)
        df.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'}, inplace=True)
        return df
    except Exception as e:
        print(f"Data fetch error: {e}")
        return None

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

def perform_deep_bbma_analysis(df):
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    prev2 = df.iloc[-3]
    reports = []
    
    trend = "BULLISH (Uptrend)" if curr['close'] > curr['ema50'] else "BEARISH (Downtrend)"

    if prev['ma5_high'] > prev['upper_bb'] and curr['close'] < curr['open']:
        reports.append("🔴 EXTREME SELL: Buying exhaustion detected.")
    elif prev['ma5_low'] < prev['lower_bb'] and curr['close'] > curr['open']:
        reports.append("🟢 EXTREME BUY: Selling exhaustion detected.")

    if prev2['ma5_high'] > prev2['upper_bb'] and prev['high'] < prev2['high'] and curr['close'] < curr['mid_bb']:
        reports.append("⚠️ MHV SELL DETECTED: Price rejection at top.")
    elif prev2['ma5_low'] < prev2['lower_bb'] and prev['low'] > prev2['low'] and curr['close'] > curr['mid_bb']:
        reports.append("⚠️ MHV BUY DETECTED: Price rejection at bottom.")

    if curr['close'] < curr['mid_bb'] and curr['close'] < curr['ma5_low'] and prev['close'] >= prev['mid_bb']:
        reports.append("🔻 CSAK SELL: Strong momentum downwards.")
    elif curr['close'] > curr['mid_bb'] and curr['close'] > curr['ma5_high'] and prev['close'] <= prev['mid_bb']:
        reports.append("🔺 CSAK BUY: Strong momentum upwards.")

    if curr['high'] >= curr['ma5_high'] and curr['close'] < curr['mid_bb']:
        reports.append("🎯 REENTRY SELL ZONE: Testing MA5/10 High.")
    elif curr['low'] <= curr['ma5_low'] and curr['close'] > curr['mid_bb']:
        reports.append("🎯 REENTRY BUY ZONE: Testing MA5/10 Low.")

    return reports, trend, curr['close']

def generate_chart_image(df):
    plt.figure(figsize=(10, 5))
    df_s = df.tail(45)
    plt.plot(df_s.index, df_s['close'], label='Close', color='black', lw=1.2)
    plt.plot(df_s.index, df_s['upper_bb'], label='Upper BB', color='red', ls='--')
    plt.plot(df_s.index, df_s['mid_bb'], label='Mid BB', color='blue', ls='--')
    plt.plot(df_s.index, df_s['lower_bb'], label='Lower BB', color='green', ls='--')
    plt.plot(df_s.index, df_s['ema50'], label='EMA 50', color='purple', lw=1.5)
    
    plt.title("XAUUSD BBMA Advanced Analysis Chart")
    plt.legend(loc='upper left', fontsize=8)
    plt.grid(True, alpha=0.3)
    
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return buf

@bot.message_handler(commands=['start', 'help'])
def start_cmd(message):
    help_text = (
        "🤖 **BBMA Bot Active**\n\n"
        "Commands:\n"
        "• /scan - Scan 1H\n"
        "• /scan_15m - Scan 15M\n"
        "• /scan_4h - Scan 4H"
    )
    bot.reply_to(message, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['scan', 'scan_15m', 'scan_4h'])
def scan_cmd(message):
    cmd = message.text.lower()
    timeframe = "15m" if "15m" in cmd else ("4h" if "4h" in cmd else "1h")
    
    bot.send_message(message.chat.id, f"🔍 Analyzing BBMA ({timeframe.upper()})...")
    
    try:
        df = fetch_live_market(timeframe)
        if df is None or len(df) < 60:
            bot.send_message(message.chat.id, "❌ Failed to fetch market data. Try again later.")
            return
            
        df = calculate_advanced_bbma(df)
        signals, trend, price = perform_deep_bbma_analysis(df)
        chart_img = generate_chart_image(df)
        
        report = f"📊 **BBMA Market Analysis ({timeframe.upper()})**\n"
        report += f"💰 Current Price: `${price:.2f}`\n"
        report += f"🌐 Major Trend (EMA 50): {trend}\n\n"
        
        if signals:
            report += "🚨 **Signals:**\n" + "\n".join(signals)
        else:
            report += "ℹ️ Market is running normally. Waiting for setup."
            
        bot.send_photo(message.chat.id, photo=chart_img, caption=report, parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Error: {str(e)}")

if __name__ == "__main__":
    bot.infinity_polling()
