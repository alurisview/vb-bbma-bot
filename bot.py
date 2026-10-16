import os
import telebot
import pandas as pd
import pandas_ta as ta
import fxcmpy
import matplotlib.pyplot as plt
from io import BytesIO

# Initialize Telegram Bot Token & FXCM Token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FXCM_TOKEN = os.getenv("FXCM_TOKEN")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# 1. FETCH LIVE MARKET DATA FROM FXCM (XAU/USD)
def fetch_live_market(timeframe="1h"):
    tf_map = {
        "15m": "m15",
        "1h": "H1",
        "4h": "H4"
    }
    period = tf_map.get(timeframe, "H1")
    
    try:
        # Connect to FXCM (using demo or live server based on your account)
        con = fxcmpy.fxcmpy(access_token=FXCM_TOKEN, server='demo', log_level='error')
        df = con.get_candles('XAU/USD', period=period, number=100)
        con.close()
        
        if df is None or df.empty:
            return None
            
        df.reset_index(inplace=True)
        
        # Map FXCM columns to standard lowercase format
        if 'bidclose' in df.columns:
            df['open'] = df['bidopen']
            df['high'] = df['bidhigh']
            df['low'] = df['bidlow']
            df['close'] = df['bidclose']
        elif 'askclose' in df.columns:
            df['open'] = df['askopen']
            df['high'] = df['askhigh']
            df['low'] = df['asklow']
            df['close'] = df['askclose']
            
        return df[['open', 'high', 'low', 'close']]
    except Exception as e:
        print(f"FXCM Connection Error: {e}")
        return None
