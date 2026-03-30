import streamlit as st
import pandas as pd
import plotly.express as px
import folium
import requests
from io import BytesIO
from streamlit_folium import folium_static
from folium.plugins import HeatMap

# Set Page Config
st.set_page_config(page_title="Used Vehicle Market Analysis", layout="wide")

# --- DATA CONFIGURATION ---
# Your provided Google Drive File ID
FILE_ID = "17VhcD1SApY6M1escKpKloilcO3XAMeWK"

@st.cache_data(show_spinner="Connecting to Data Cloud...")
def load_data_from_drive(file_id):
    url = f'https://drive.google.com/uc?export=download&id={file_id}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # Load the Parquet data directly from the response
        df = pd.read_parquet(BytesIO(response.content))
        
        # Immediate RAM Optimization
        required_cols = ["manufacturer", "model", "year", "price", "lat", "long", 
                         "cylinders", "fuel", "drive", "type", "transmission"]
        df = df[required_cols]

        # Memory Optimization: Downcasting
        df['price'] = pd.to_numeric(df['price'], downcast='float')
        df['year'] = pd.to_numeric(df['year'], downcast='integer')

        # Memory Optimization: Categorical Types
        cat_cols = ["manufacturer", "fuel", "drive", "type", "transmission"]
        for col in cat_cols:
            if col in df.columns:
                df[col] = df[col].astype('category')

        return df.dropna(subset=["manufacturer", "model", "year", "price", "lat", "long"])
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

# Automatically load data on startup
df = load_data_from_drive(FILE_ID)

# --- SIDEBAR NAVIGATION (CLEAN VERSION) ---
st.sidebar.title("Navigation")

# Only show the radio buttons, NO file uploader logic here
if not df.empty:
    page = st.sidebar.radio("Go to", [
        "Home", 
        "Models by Company",
        "Most Listed Vehicle Brands", 
        "Transmission vs Type", 
        "Manufacturer vs Drive", 
        "Brand-Specific Heatmap"
    ])
else:
    page = "Home"
    st.sidebar.warning("Waiting for data...")

# --- PAGES ---
if page == "Home":
    st.title("🚗 Used Vehicle Market Analysis Dashboard")
    st.markdown("---")
    
    if not df.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Listings", f"{len(df):,}")
        with col2:
            st.metric("Unique Brands", df['manufacturer'].nunique())
        with col3:
            st.metric("Avg Price", f"${df['price'].mean():,.2f}")

        st.markdown("### Welcome!")
        st.markdown("Explore regional trends and vehicle specifications across the US.")
        st.dataframe(df.head(10), use_container_width=True)
    else:
        st.error("Data failed to load from Google Drive. Please check your File ID and Drive sharing settings.")

elif page == "Models by Company":
    st.subheader("Models by Manufacturer")
    if not df.empty:
        selected_brand = st.selectbox("Choose a Company:", sorted(df['manufacturer'].unique()))
        brand_df = df[df['manufacturer'] == selected_brand].dropna(subset=['model']).copy()
        
        search_query = st.text_input("Search for a model:").lower()
        if search_query:
            brand_df = brand_df[brand_df['model'].astype(str).str.lower().str.contains(search_query)]

        if not brand_df.empty:
            grouped = brand_df.groupby('model', observed=True).agg({
                'price': 'mean',
                'year': lambda x: int(x.median())
            }).reset_index()
            st.dataframe(grouped, use_container_width=True)

# ... (rest of your chart logic goes here, following the same pattern)

elif page == "Brand-Specific Heatmap":
    st.subheader("Heatmap of Selected Brand")
    if not df.empty:
        selected_brand = st.selectbox("Select a Manufacturer:", sorted(df['manufacturer'].unique()))
        brand_df = df[df['manufacturer'] == selected_brand].dropna(subset=['lat', 'long'])
        if not brand_df.empty:
            m = folium.Map(location=[brand_df['lat'].mean(), brand_df['long'].mean()], zoom_start=5)
            HeatMap(brand_df[['lat', 'long']].head(2000).values.tolist()).add_to(m)
            folium_static(m)
