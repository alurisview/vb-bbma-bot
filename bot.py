import os
import time
import threading
import telebot
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import matplotlib.pyplot as plt
from io import BytesIO

# Initialize Telegram Bot Token & Chat ID
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") # Optional: Your chat ID for auto signals

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Store last sent signals to avoid duplicate spamming
last_signal_state = {"1h": "", "15m": ""}

# 1. FETCH LIVE MARKET DATA (XAUUSD)
def fetch_live_market(timeframe="1h"):
    tf_map = {
        "15m": ("15m", "7d"),
        "1h": ("1h", "1mo"),
        "4h": ("1h", "3mo")
    }
    interval, period = tf_map.get(timeframe, ("1h", "1mo"))
    ticker = yf.Ticker("GC=F")
    df = ticker.history(period=period, interval=interval)
    
    if df.empty:
        return None
        
    df.reset_index(inplace=True)
    df.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'}, inplace=True)
    return df

# 2. CALCULATE BBMA INDICATORS (PURE PANDAS SAFE METHOD)
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

# 3. DEEP RULE-BASED BBMA ANALYSIS ENGINE
def perform_deep_bbma_analysis(df):
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    prev2 = df.iloc[-3]
    reports = []
    
    trend = "BULLISH (Uptrend)" if curr['close'] > curr['ema50'] else "BEARISH (Downtrend)"

    if prev['ma5_high'] > prev['upper_bb'] and curr['close'] < curr['open']:
        reports.append("🔴 EXTREME SELL: Buying exhaustion detected, preparing for MHV Sell.")
    elif prev['ma5_low'] < prev['lower_bb'] and curr['close'] > curr['open']:
        reports.append("🟢 EXTREME BUY: Selling exhaustion detected, preparing for MHV Buy.")

    if prev2['ma5_high'] > prev2['upper_bb'] and prev['high'] < prev2['high'] and curr['close'] < curr['mid_bb']:
        reports.append("⚠️ MHV SELL DETECTED: Price rejection at top, looking for Reentry Sell.")
    elif prev2['ma5_low'] < prev2['lower_bb'] and prev['low'] > prev2['low'] and curr['close'] > curr['mid_bb']:
        reports.append("⚠️ MHV BUY DETECTED: Price rejection at bottom, looking for Reentry Buy.")

    if curr['close'] < curr['mid_bb'] and curr['close'] < curr['ma5_low'] and prev['close'] >= prev['mid_bb']:
        reports.append("🔻 CSAK SELL: Strong momentum candle breaking Mid BB downwards.")
    elif curr['close'] > curr['mid_bb'] and curr['close'] > curr['ma5_high'] and prev['close'] <= prev['mid_bb']:
        reports.append("🔺 CSAK BUY: Strong momentum candle breaking Mid BB upwards.")

    if curr['high'] >= curr['ma5_high'] and curr['close'] < curr['mid_bb']:
        reports.append("🎯 REENTRY SELL ZONE: Price testing MA5/10 High, safe zone to Sell.")
    elif curr['low'] <= curr['ma5_low'] and curr['close'] > curr['mid_bb']:
        reports.append("🎯 REENTRY BUY ZONE: Price testing MA5/10 Low, safe zone to Buy.")

    return reports, trend, curr['close']

# 4. CHART GENERATOR
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

# 5. BACKGROUND AUTO-SCANNER (Sends signal automatically when detected)
def background_auto_scanner():
    while True:
        try:
            chat_id = os.getenv("TELEGRAM_CHAT_ID")
            if chat_id:
                for tf in ["15m", "1h"]:
                    df = fetch_live_market(tf)
                    if df is not None and len(df) >= 60:
                        df = calculate_advanced_bbma(df)
                        signals, trend, price = perform_deep_bbma_analysis(df)
                        
                        if signals:
                            signal_key = "".join(signals)
                            # Send only if new signal appears to avoid spam
                            if last_signal_state[tf] != signal_key:
                                last_signal_state[tf] = signal_key
                                chart_img = generate_chart_image(df)
                                
                                report = f"🚨 **AUTO BBMA SIGNAL ({tf.upper()})** 🚨\n"
                                report += f"💰 Current Price: `${price:.2f}`\n"
                                report += f"🌐 Major Trend: {trend}\n\n"
                                report += "📌 **Signals:**\n" + "\n".join(signals)
                                
                                bot.send_photo(chat_id, photo=chart_img, caption=report, parse_mode="Markdown")
            # Scan every 5 minutes
            time.sleep(300)
        except Exception as e:
            print(f"Auto scanner error: {e}")
            time.sleep(60)

# 6. TELEGRAM HANDLERS
@bot.message_handler(commands=['start', 'help'])
def start_cmd(message):
    help_text = (
        "🤖 **BBMA Auto Signal Bot**\n\n"
        "Commands:\n"
        "• /scan - Manual scan 1H\n"
        "• /scan_15m - Manual scan 15M\n"
        "• /scan_4h - Manual scan 4H"
    )
    bot.reply_to(message, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['scan', 'scan_15m', 'scan_4h'])
def scan_cmd(message):
    cmd = message.text.lower()
    timeframe = "15m" if "15m" in cmd else ("4h" if "4h" in cmd else "1h")
    
    bot.send_message(message.chat.id, f"🔍 Fetching live market data and analyzing BBMA ({timeframe.upper()})...")
    
    try:
        df = fetch_live_market(timeframe)
        if df is None or len(df) < 60:
            bot.send_message(message.chat.id, "❌ Insufficient market data. Please try again.")
            return
            
        df = calculate_advanced_bbma(df)
        signals, trend, price = perform_deep_bbma_analysis(df)
        chart_img = generate_chart_image(df)
        
        report = f"📊 **BBMA Market Analysis ({timeframe.upper()})**\n"
        report += f"💰 Current Price: `${price:.2f}`\n"
        report += f"🌐 Major Trend (EMA 50): {trend}\n\n"
        
        if signals:
            report += "🚨 **Detected Signals:**\n" + "\n".join(signals)
        else:
            report += "ℹ️ Market is running normally. Waiting for setup."
            
        bot.send_photo(message.chat.id, photo=chart_img, caption=report, parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Error: {str(e)}")

if __name__ == "__main__":
    # Start background auto scanner thread
    scanner_thread = threading.Thread(target=background_auto_scanner, daemon=True)
    scanner_thread.start()
    
    # Start bot polling
    bot.infinity_polling()
