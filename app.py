import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# Configure Streamlit page settings to make the app wider
st.set_page_config(
    page_title="Live Crypto Dashboard",
    layout="wide",  # Makes the app take the full width of the browser
    initial_sidebar_state="expanded"
)

# Function to fetch live data from JSON
def fetch_live_data():
    url = 'https://api.quantumvoid.org/data/quantdatav2_bybit.json'
    try:
        response = requests.get(url, headers={'Cache-Control': 'no-cache'})
        if response.status_code == 200:
            data = response.json()
            print("Fetched Data:", data)  # Debugging: Log fetched data
            if isinstance(data, list):
                return pd.DataFrame(data), datetime.now()  # Return data and fetch time
        else:
            st.error(f"Failed to fetch data. HTTP Status Code: {response.status_code}")
    except Exception as e:
        st.error(f"An error occurred while fetching data: {e}")
        print(f"Error fetching data: {e}")  # Debugging
    return pd.DataFrame(), None  # Return empty DataFrame and None if API fails

# Streamlit app layout
st.title("Live Crypto Data Dashboard")

# Fetch live data
data, last_fetched = fetch_live_data()

# Display last fetch time
if last_fetched:
    st.write(f"**Data last fetched at:** {last_fetched.strftime('%Y-%m-%d %H:%M:%S')} (Server Time)")

# Display data if available
if not data.empty:
    # User interaction: Choose a column to sort and sort order
    sort_column = st.selectbox("Sort by Column", options=data.columns, index=0, key="sort_column")
    sort_order = st.radio("Sort Order", ["Ascending", "Descending"], index=0, key="sort_order")
    ascending = True if sort_order == "Ascending" else False

    # Sort the DataFrame
    sorted_data = data.sort_values(by=sort_column, ascending=ascending)

    # Display the data table
    st.dataframe(
        sorted_data,
        height=700,  # Adjust the height in pixels for a taller table
        use_container_width=True  # Ensures the table stretches to the full width
    )

    # Download button for the data
    csv = sorted_data.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Data as CSV",
        data=csv,
        file_name='crypto_data.csv',
        mime='text/csv',
    )
else:
    st.error("No data available. Please try again later.")

