import ccxt
import pandas as pd
import numpy as np
import time
import streamlit as st
from scipy.stats import zscore
import plotly.express as px

# Initialize hyperliquid exchange
def initialize_exchange():
    return ccxt.hyperliquid({
        'rateLimit': 50,
        'enableRateLimit': True,
    })

# Fetch market and symbol data
@st.cache_resource
def fetch_symbols(exchange):
    markets = exchange.load_markets()
    symbols = [market['id'] for market in markets.values() if 'id' in market]
    symbol_map = {market['id']: market['symbol'] for market in markets.values()}  # Map IDs to meaningful symbols
    return symbols, symbol_map

# Fetch order book data
@st.cache_data
def fetch_hyperliquid_data(exchange, symbols, symbol_map):
    results = []
    for symbol in symbols:
        try:
            # Fetch order book
            orderbook = exchange.fetch_order_book(symbol, limit=10)
            if not orderbook or 'bids' not in orderbook or 'asks' not in orderbook:
                continue

            # Metrics from order book
            bid_prices = [bid[0] for bid in orderbook['bids'][:10]]
            ask_prices = [ask[0] for ask in orderbook['asks'][:10]]
            bid_sizes = [bid[1] for bid in orderbook['bids'][:10]]
            ask_sizes = [ask[1] for ask in orderbook['asks'][:10]]

            # Calculate top-level sizes
            bid_sz_00 = bid_sizes[0]
            ask_sz_00 = ask_sizes[0]

            # Calculate skew (depth imbalance on top level)
            skew = np.log(bid_sz_00) - np.log(ask_sz_00)

            # Calculate imbalance (order imbalance on top ten levels)
            imbalance = np.log(sum(bid_sizes)) - np.log(sum(ask_sizes))

            # Add data
            results.append({
                'Crypto': symbol_map[symbol],
                'Skew': skew,
                'Imbalance': imbalance,
                'Bid Sizes': bid_sizes,
                'Ask Sizes': ask_sizes,
                'Bid Prices': bid_prices,
                'Ask Prices': ask_prices,
            })
        except Exception as e:
            st.warning(f"Error fetching data for {symbol}: {e}")
        time.sleep(exchange.rateLimit / 1000)  # Respect rate limits

    return pd.DataFrame(results)

# Calculate Z-scores and rankings
def calculate_metrics(df):
    for col in ['Skew', 'Imbalance']:
        df[f'{col} Z-Score'] = zscore(df[col], nan_policy='omit')
        df[f'{col} Rank'] = df[f'{col} Z-Score'].rank(ascending=False)
    return df

# Interactive Streamlit App
def app():
    st.title("Crypto Order Book Analysis with Streamlit")

    # Initialize exchange
    st.sidebar.write("Initializing exchange...")
    exchange = initialize_exchange()

    # Fetch symbols
    st.sidebar.write("Fetching symbols...")
    symbols, symbol_map = fetch_symbols(exchange)
    st.sidebar.write(f"Available cryptos: {len(symbols)} symbols loaded.")

    # Fetch data
    st.sidebar.write("Fetching order book data...")
    data = fetch_hyperliquid_data(exchange, symbols, symbol_map)

    if not data.empty:
        st.write("### Data Fetched Successfully")
        st.dataframe(data.head())

        # Calculate metrics
        data = calculate_metrics(data)

        # Choose metric for visualization
        metric = st.selectbox("Select Metric for Visualization:", ["Skew", "Imbalance"])

        # Visualize metric
        st.write(f"### {metric} by Crypto")
        fig = px.bar(data, x='Crypto', y=metric, title=f"{metric} by Crypto", color=metric)
        st.plotly_chart(fig)

        # Most bullish and bearish
        top_n = st.slider("Number of Top/Bottom Cryptos to Display:", 5, 20, 10)
        sorted_data = data.sort_values(by=metric, ascending=False)
        most_bullish = sorted_data.head(top_n)
        most_bearish = sorted_data.tail(top_n)

        st.write(f"### Most Bullish Cryptos by {metric}")
        st.dataframe(most_bullish[['Crypto', metric]])

        st.write(f"### Most Bearish Cryptos by {metric}")
        st.dataframe(most_bearish[['Crypto', metric]])

    else:
        st.error("No data available. Please try again.")

if __name__ == "__main__":
    app()

