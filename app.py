import streamlit as st
import pandas as pd
import requests

# Function to fetch data
@st.cache_data(ttl=60)  # Cache data for 60 seconds
def fetch_data():
    url = 'https://api.quantumvoid.org/data/quantdatav2_bybit.json'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list):  # Ensure it's a list of dictionaries
            return pd.DataFrame(data)
    return pd.DataFrame()  # Return an empty DataFrame if the API fails

# Streamlit app layout
st.title("Interactive Data Table for Crypto Market")

# Fetch the data
df = fetch_data()

if not df.empty:
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
