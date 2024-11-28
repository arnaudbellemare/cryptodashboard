import streamlit as st
import pandas as pd
import requests

# Define the URL
url = 'https://api.quantumvoid.org/data/quantdatav2_bybit.json'

# Fetch the data
def fetch_data(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return pd.DataFrame(data)
        else:
            st.error(f"Failed to fetch data. Status code: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

# Streamlit app
def main():
    st.title("Ticker Data Viewer")

    # Fetch data
    df = fetch_data(url)

    if df is not None and not df.empty:
        # Column selection
        st.subheader("Sort and View Data")
        sort_column = st.selectbox("Select column to sort by:", options=df.columns)
        sort_order = st.radio("Sort order:", options=["Ascending", "Descending"])

        # Sort the data
        sorted_df = df.sort_values(by=sort_column, ascending=(sort_order == "Ascending"))

        # Display the sorted table
        st.dataframe(sorted_df)

    else:
        st.warning("No data available to display.")

if __name__ == "__main__":
    main()
