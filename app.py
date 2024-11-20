import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time

# Function to fetch data
def fetch_data():
    url = 'https://api.quantumvoid.org/data/quantdatav2_bybit.json'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list):
            return pd.DataFrame(data), datetime.now()  # Return data and fetch time
    return pd.DataFrame(), None  # Return empty DataFrame and None if API fails

# Streamlit app layout
st.title("Interactive Crypto Data Dashboard")

# Fetch and refresh data every minute
while True:
    df, fetch_time = fetch_data()

    if not df.empty:
        # Show when the data was last fetched
        if fetch_time:
            st.write(f"**Data last fetched at:** {fetch_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # User interaction: Choose a column to sort and sort order
        sort_column = st.selectbox("Sort by Column", options=df.columns, index=0)
        sort_order = st.radio("Sort Order", ["Ascending", "Descending"], index=0)
        ascending = True if sort_order == "Ascending" else False

        # Sort the DataFrame
        sorted_df = df.sort_values(by=sort_column, ascending=ascending)

        # Display the data table
        st.dataframe(sorted_df)

        # Download button for the data
        csv = sorted_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Data as CSV",
            data=csv,
            file_name='crypto_data.csv',
            mime='text/csv',
        )
    else:
        st.error("Failed to fetch data or the data is empty.")

    # Refresh every 60 seconds
    time.sleep(60)
