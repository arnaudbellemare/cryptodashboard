import streamlit as st
import pandas as pd
import requests
from datetime import datetime

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

# Fetch the data
if "data" not in st.session_state or "last_fetched" not in st.session_state:
    st.session_state.data, st.session_state.last_fetched = fetch_data()

# Display last fetch time
if st.session_state.last_fetched:
    st.write(f"**Data last fetched at:** {st.session_state.last_fetched.strftime('%Y-%m-%d %H:%M:%S')}")

# Display data if available
if not st.session_state.data.empty:
    # User interaction: Choose a column to sort and sort order
    sort_column = st.selectbox("Sort by Column", options=st.session_state.data.columns, index=0)
    sort_order = st.radio("Sort Order", ["Ascending", "Descending"], index=0)
    ascending = True if sort_order == "Ascending" else False

    # Sort the DataFrame
    sorted_df = st.session_state.data.sort_values(by=sort_column, ascending=ascending)

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

# Refresh the data every 60 seconds
if st.button("Refresh Data"):
    st.session_state.data, st.session_state.last_fetched = fetch_data()
    st.experimental_rerun()
