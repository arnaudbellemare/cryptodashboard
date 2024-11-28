import streamlit as st
import pandas as pd
import requests

# Define the URL
url = 'https://api.quantumvoid.org/data/quantdatav2_bybit.json'

# Fetch the data
def fetch_data():
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()  # Return JSON data
    else:
        return None  # Return None if the request fails

# Streamlit app
def main():
    st.title("Interactive Data Viewer")
    
    # Fetch the data
    data = fetch_data()
    if data:
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Display sorting options
        sort_column = st.selectbox("Select column to sort by:", df.columns)
        sort_order = st.radio("Sort order:", ["Ascending", "Descending"])
        
        # Sort the DataFrame
        sorted_df = df.sort_values(by=sort_column, ascending=(sort_order == "Ascending"))
        
        # Display the table
        st.dataframe(sorted_df)
    else:
        st.error("Failed to retrieve data.")

if __name__ == "__main__":
    main()

