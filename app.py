import ccxt
import pandas as pd
import numpy as np
import streamlit as st
import datetime
import time

# Initialize the Hyperliquid Exchange
def initialize_exchange():
    return ccxt.hyperliquid({
        'rateLimit': 50,
        'enableRateLimit': True,
        'walletAddress': '0x2ee47d996516dfa7efcb1ae9efa7a053f0de6b85'
    })

# Fetch active symbols and their mappings
def fetch_symbols(exchange):
    markets = exchange.load_markets()
    symbols = [market['id'] for market in markets.values() if market.get('active', True)]
    symbol_map = {market['id']: market['symbol'] for market in markets.values()}
    return symbols, symbol_map

# Retry mechanism for fetching OHLCV
def fetch_ohlcv_with_retry(exchange, symbol, timeframe="1m", limit=240, retries=3):
    for attempt in range(retries):
        try:
            return exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1)
            else:
                print(f"Failed to fetch OHLCV for {symbol} after {retries} retries: {e}")
                return []

# Fetch order book and compute VOI and OIR
def fetch_order_book_with_metrics(exchange, symbol):
    order_book = exchange.fetch_order_book(symbol, limit=10)
    bid_volumes = [level[1] for level in order_book['bids']]
    ask_volumes = [level[1] for level in order_book['asks']]
    bid_prices = [level[0] for level in order_book['bids']]
    ask_prices = [level[0] for level in order_book['asks']]

    # Volume Order Imbalance (VOI)
    voi3 = np.sum(bid_volumes[:3]) - np.sum(ask_volumes[:3])
    voi5 = np.sum(bid_volumes[:5]) - np.sum(ask_volumes[:5])
    voi10 = np.sum(bid_volumes[:10]) - np.sum(ask_volumes[:10])

    # Order Imbalance Ratios (OIR)
    oir3 = np.sum(bid_volumes[:3]) / np.sum(ask_volumes[:3]) if np.sum(ask_volumes[:3]) > 0 else np.nan
    oir5 = np.sum(bid_volumes[:5]) / np.sum(ask_volumes[:5]) if np.sum(ask_volumes[:5]) > 0 else np.nan
    oir10 = np.sum(bid_volumes[:10]) / np.sum(ask_volumes[:10]) if np.sum(ask_volumes[:10]) > 0 else np.nan

    return {
        "Mid Price": (bid_prices[0] + ask_prices[0]) / 2,
        "Spread": ask_prices[0] - bid_prices[0],
        "VOI3": voi3,
        "VOI5": voi5,
        "VOI10": voi10,
        "OIR3": oir3,
        "OIR5": oir5,
        "OIR10": oir10,
    }

# Calculate Advanced ERI
def calculate_advanced_eri(df, len_slow_ma=64, len_power_ema=13):
    vwma = ((df['close'] * df['volume']).rolling(window=len_slow_ma).sum() /
            df['volume'].rolling(window=len_slow_ma).sum())
    slow_vwma_ema = vwma.ewm(span=len_slow_ma, adjust=False).mean()

    # Determine trend
    last_price = df['close'].iloc[-1]
    eri_trend = "bullish" if last_price > slow_vwma_ema.iloc[-1] else "bearish"

    # Bull and bear power
    bull_power = df['high'] - slow_vwma_ema
    bear_power = df['low'] - slow_vwma_ema
    bull_power_smoothed = bull_power.ewm(span=len_power_ema, adjust=False).mean()
    bear_power_smoothed = bear_power.ewm(span=len_power_ema, adjust=False).mean()

    return {
        "ERI Trend": eri_trend,
        "ERI Bull Power": bull_power_smoothed.iloc[-1],
        "ERI Bear Power": bear_power_smoothed.iloc[-1]
    }

# Fetch and calculate all variables for each symbol
def fetch_and_calculate(exchange, symbols, symbol_map):
    data = []
    for symbol in symbols:
        try:
            # Fetch order book and metrics
            order_book_metrics = fetch_order_book_with_metrics(exchange, symbol)

            # Fetch OHLCV data
            ohlcv = fetch_ohlcv_with_retry(exchange, symbol)
            if not ohlcv or len(ohlcv) < 240:
                print(f"Skipping {symbol}: Not enough OHLCV data (less than 240).")
                continue

            df = pd.DataFrame(
                ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

            # ATR and ATRP
            df['TR'] = df[['high', 'low', 'close']].max(axis=1) - df[['high', 'low']].min(axis=1)
            df['ATR'] = df['TR'].rolling(window=14).mean()
            atrp = (df['ATR'].iloc[-1] / df['close'].iloc[-1]) * 100

            # Trend % and Direction
            ema = df['close'].ewm(span=6).mean()
            trend_pct = ((df['close'].iloc[-1] - ema.iloc[-1]) / df['close'].iloc[-1]) * 100
            trend = "long" if trend_pct > 0 else "short"

            # Advanced ERI
            eri_result = calculate_advanced_eri(df)

            # LTP Change
            df['ltps'] = df['close'].shift(1)
            df['ltp_ch'] = df['close'] - df['ltps']

            data.append({
                "Asset": symbol_map[symbol].split('/')[0],
                "Price": df['close'].iloc[-1],
                "Trend": trend,
                "ERI Trend": eri_result["ERI Trend"],
                "Trend %": trend_pct,
                "ATRP": atrp,
                **order_book_metrics,
                "1m Volume (USDT)": df['volume'].iloc[-1] * df['close'].iloc[-1],
                "5m 1x Volume (USDT)": df['volume'].iloc[-5:].sum() * df['close'].iloc[-1],
                "ERI Bull Power": eri_result["ERI Bull Power"],
                "ERI Bear Power": eri_result["ERI Bear Power"],
                "LTP Change (USD)": df['ltp_ch'].iloc[-1],
                "Timestamp": datetime.utcnow().isoformat(),
            })

        except Exception as e:
            print(f"Error processing {symbol}: {e}")
    return pd.DataFrame(data)

# Main Streamlit App
def main():
    st.title("Crypto Metrics Dashboard")
    exchange = initialize_exchange()
    symbols, symbol_map = fetch_symbols(exchange)

    st.sidebar.write(f"Fetched {len(symbols)} symbols.")
    refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 10, 120, 60)

    while True:
        data = fetch_and_calculate(exchange, symbols, symbol_map)
        st.subheader("Fetched Data (Full Table)")
        st.dataframe(data)

        # Filter data
        to_trade = data[data["5m 1x Volume (USDT)"] > 15000]
        rotator = data[data["1m Volume (USDT)"] > 16000]

        st.subheader("Tradeable Symbols (5m Volume > 15000)")
        st.dataframe(to_trade)

        st.subheader("Rotator Symbols (1m Volume > 16000)")
        st.dataframe(rotator)

        st.subheader("Top Symbols by Aggregated OIR")
        oir_sorted = data.sort_values(by="OIR10", ascending=False).head(10)
        st.dataframe(oir_sorted)

        st.subheader("Top Symbols by Aggregated VOI")
        voi_sorted = data.sort_values(by="VOI10", ascending=False).head(10)
        st.dataframe(voi_sorted)

        time.sleep(refresh_interval)

if __name__ == "__main__":
    main()
