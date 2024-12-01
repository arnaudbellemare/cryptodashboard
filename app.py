pip install streamlit

import streamlit as st
import pandas as pd
import ccxt
import matplotlib.pyplot as plt
import time

# Initialize ccxt and fetch data
def fetch_hyperliquid_data():
    exchange = ccxt.hyperliquid({
        'rateLimit': 50,
        'enableRateLimit': True,
    })

    # Load markets
    markets = exchange.load_markets()
    symbols = [market['id'] for market in markets.values() if 'id' in market]

    # Fetch additional data for each symbol
    results = []
    for symbol in symbols:
        try:
            # Fetch order book
            orderbook = exchange.fetch_order_book(symbol, limit=50)
            if not orderbook or 'bids' not in orderbook or 'asks' not in orderbook:
                continue

            # Calculate mid-price
            mid_price = (orderbook['bids'][0][0] + orderbook['asks'][0][0]) / 2
            open_interest = float(markets[symbol]['info'].get('openInterest', 0))
            funding = float(markets[symbol]['info'].get('funding', 0))
            day_volume = float(markets[symbol]['info'].get('dayNtlVlm', 0))

            results.append({
                'Symbol': symbol,
                'Mid Price': mid_price,
                'Open Interest': open_interest,
                'Funding Rate': funding,
                'Daily Volume': day_volume,
            })
        except Exception as e:
            st.warning(f"Error fetching data for {symbol}: {e}")

        # Respect rate limits
        time.sleep(exchange.rateLimit / 1000)

    return pd.DataFrame(results)

# Fetch data
st.title("Hyperliquid Dashboard")
st.write("Streaming data and visualizing market stats for Hyperliquid.")

with st.spinner("Fetching data..."):
    data = fetch_hyperliquid_data()

# Display data as a table
st.subheader("Market Data Table")
st.dataframe(data)

# Plot charts for metrics
if not data.empty:
    st.subheader("Market Metrics Charts")

    # Select symbol for detailed charting
    symbol = st.selectbox("Select Symbol", data['Symbol'])

    # Plot funding rate
    fig, ax = plt.subplots()
    data.set_index('Symbol')[['Funding Rate']].plot(kind='bar', ax=ax, legend=False)
    ax.set_title("Funding Rate by Symbol")
    ax.set_xlabel("Symbol")
    ax.set_ylabel("Funding Rate")
    st.pyplot(fig)

    # Open interest vs. daily volume
    fig, ax = plt.subplots()
    ax.scatter(data['Open Interest'], data['Daily Volume'], alpha=0.7)
    ax.set_title("Open Interest vs. Daily Volume")
    ax.set_xlabel("Open Interest")
    ax.set_ylabel("Daily Volume")
    st.pyplot(fig)

