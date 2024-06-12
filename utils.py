import numpy as np
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_body_and_shadow(tickerData):
    """Calculate the body size and the upper and lower shadow sizes."""
    tickerData['Body'] = abs(tickerData['Open'] - tickerData['Close'])
    tickerData['Lower Shadow'] = tickerData[['Open', 'Close']].min(axis=1) - tickerData['Low']
    tickerData['Upper Shadow'] = tickerData['High'] - tickerData[['Open', 'Close']].max(axis=1)
    return tickerData

def identify_fvg(tickerData):
    """Identify Fair Value Gaps (FVG) in the data."""
    fvg_list = []
    for i in range(1, len(tickerData) - 1):
        first_candle = tickerData.iloc[i - 1]
        third_candle = tickerData.iloc[i + 1]
        
        if first_candle['High'] < third_candle['Low']:
            fvg_list.append((i - 1, i + 1, 'Bullish'))
            
        if first_candle['Low'] > third_candle['High']:
            fvg_list.append((i - 1, i + 1, 'Bearish'))
    
    return fvg_list


def identify_major_highs_lows(tickerData, window=5):
    major_highs = []
    major_lows = []

    for i in range(window, len(tickerData) - window):
        current_high = tickerData.iloc[i]['High']
        current_low = tickerData.iloc[i]['Low']
        
        preceding_highs = tickerData.iloc[i - window:i]['High']
        following_highs = tickerData.iloc[i + 1:i + 1 + window]['High']
        preceding_lows = tickerData.iloc[i - window:i]['Low']
        following_lows = tickerData.iloc[i + 1:i + 1 + window]['Low']
        
        if current_high > preceding_highs.max() and current_high > following_highs.max():
            major_highs.append(i)
        
        if current_low < preceding_lows.min() and current_low < following_lows.min():
            major_lows.append(i)
    
    return major_highs, major_lows

def identify_bos(tickerData, major_highs, major_lows):
    bos_list = []

    for i in range(1, len(tickerData)):
        current_candle = tickerData.iloc[i]

        for high_index in major_highs:
            if i > high_index:
                major_high_value = tickerData.iloc[high_index]['High']
                if current_candle['Open'] < major_high_value and current_candle['Close'] > major_high_value:
                    bos_list.append((i, 'Bullish'))
                    break

        for low_index in major_lows:
            if i > low_index:
                major_low_value = tickerData.iloc[low_index]['Low']
                if current_candle['Open'] > major_low_value and current_candle['Close'] < major_low_value:
                    bos_list.append((i, 'Bearish'))
                    break
    
    return bos_list


def calculate_median_volume(tickerData):
    """Calculate the median volume of the candles in the DataFrame."""
    if 'Volume' not in tickerData.columns:
        logging.warning("Volume data is not available in the DataFrame.")
        return None
    median_volume = tickerData['Volume'].median()
    return median_volume

def calculate_median_body_size(tickerData):
    """Calculate the median body size (absolute difference between the open and close) of the candles in the DataFrame."""
    if 'Open' not in tickerData.columns or 'Close' not in tickerData.columns:
        logging.warning("Open or Close data is not available in the DataFrame.")
        return None
    tickerData['Body'] = abs(tickerData['Open'] - tickerData['Close'])
    median_body_size = tickerData['Body'].median()
    logging.info(f"Median body size: {median_body_size}")
    return median_body_size

def is_boring_candle(candle, median_body_size, median_volume):
    """Identify if a candle is a boring candle.
    
    A boring candle has:
    - Body size smaller than half of the median body size.
    - Volume less than half of the median volume.
    - Total wick length (upper + lower) less than the body length.
    """
    body_size = abs(candle['Open'] - candle['Close'])
    volume = candle['Volume']
    lower_wick = min(candle['Open'], candle['Close']) - candle['Low']
    upper_wick = candle['High'] - max(candle['Open'], candle['Close'])
    total_wick_length = lower_wick + upper_wick

    if (body_size < 0.75 * median_body_size and
        volume < 0.75 * median_volume and
        total_wick_length < body_size):
        return True
    return False

def find_first_boring_candle(tickerData, median_body_size, median_volume):
    """Find the first boring candle to the left of the last candle that is entirely below the low of the last candle."""
    last_candle_low = tickerData.iloc[-1]['Low']
    
    for i in range(len(tickerData) - 2, -1, -1):  # Start from the second last candle and move left
        candle = tickerData.iloc[i]
        if (is_boring_candle(candle, median_body_size, median_volume) and
            candle['High'] < last_candle_low):
            return i  # Return the index of the first boring candle
    
    return None  # Return None if no such candle is found