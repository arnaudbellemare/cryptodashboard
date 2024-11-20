import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# Configure Streamlit page settings to make the app wider
st.set_page_config(
    page_title="Interactive Crypto Dashboard",
    layout="wide",  # Makes the app take the full width of the browser
    initial_sidebar_state="expanded"
)

# Function to fetch data
def fetch_data():
    url = 'https://api.quantumvoid.org/data/quantdatav2_bybit.json'
    response = requests.get(url, headers={'Cache-Control': 'no-cache'})
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list):
            return pd.DataFrame(data), datetime.now()  # Return data and fetch time
    return pd.DataFrame(), None  # Return empty DataFrame and None if API fails

# Streamlit app layout
st.title("Interactive Crypto Data Dashboard")

# Initialize session state
if "data" not in st.session_state or "last_fetched" not in st.session_state:
    st.session_state.data, st.session_state.last_fetched = fetch_data()

# Manual Refresh Button
if st.button("Refresh Data"):
    # Fetch new data and update session state
    st.session_state.data, st.session_state.last_fetched = fetch_data()

# Display last fetch time
if st.session_state.last_fetched:
    st.write(f"**Data last fetched at:** {st.session_state.last_fetched.strftime('%Y-%m-%d %H:%M:%S')}")

# Display data if available
if not st.session_state.data.empty:
    # User interaction: Choose a column to sort and sort order
    sort_column = st.selectbox("Sort by Column", options=st.session_state.data.columns, index=0, key="sort_column")
    sort_order = st.radio("Sort Order", ["Ascending", "Descending"], index=0, key="sort_order")
    ascending = True if sort_order == "Ascending" else False

    # Sort the DataFrame
    sorted_df = st.session_state.data.sort_values(by=sort_column, ascending=ascending)

    # Display the data table with larger (wider and taller) size
    st.dataframe(
        sorted_df,
        height=1000,  # Adjust the height in pixels for a taller table
        use_container_width=True  # Ensures the table stretches to the full width
    )

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


