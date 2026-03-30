import streamlit as st
import pandas as pd
import plotly.express as px
import folium
import gdown
import os
from streamlit_folium import folium_static
from folium.plugins import HeatMap

# Set Page Config
st.set_page_config(page_title="Used Vehicle Market Analysis", layout="wide")

# --- DATA CONFIGURATION ---
FILE_ID = "17VhcD1SApY6M1escKpKloilcO3XAMeWK"
OUTPUT_FILE = "vehicles.parquet"

@st.cache_data(show_spinner="Connecting to Data Cloud (452MB)...")
def load_data(file_id):
    url = f'https://drive.google.com/uc?id={file_id}'
    
    # 1. Download from Google Drive if not already present
    if not os.path.exists(OUTPUT_FILE):
        try:
            gdown.download(url, OUTPUT_FILE, quiet=False)
        except Exception as e:
            st.error(f"Download failed: {e}")
            return pd.DataFrame()

    try:
        # 2. MEMORY OPTIMIZATION: Load ONLY necessary columns
        # This is critical to prevent the 1GB RAM crash on Streamlit Cloud
        cols_to_load = [
            "manufacturer", "model", "year", "price", "lat", "long", 
            "cylinders", "fuel", "drive", "type", "transmission"
        ]
        
        df = pd.read_parquet(OUTPUT_FILE, columns=cols_to_load)

        # 3. DOWNCASTING: Reduce memory footprint of numbers
        df['price'] = pd.to_numeric(df['price'], downcast='float')
        df['year'] = pd.to_numeric(df['year'], downcast='integer')

        # 4. CATEGORICALS: Drastically reduces RAM for repetitive strings
        cat_cols = ["manufacturer", "fuel", "drive", "type", "transmission"]
        for col in cat_cols:
            if col in df.columns:
                df[col] = df[col].astype('category')

        # 5. CLEANING: Drop rows missing core info
        return df.dropna(subset=["manufacturer", "model", "price", "lat", "long"])
    
    except Exception as e:
        st.error(f"Error processing Parquet: {e}")
        return pd.DataFrame()

# Load the data automatically on startup
df = load_data(FILE_ID)

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("Navigation")

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
    st.sidebar.warning("Data loading... please wait.")

# --- PAGES ---

if page == "Home":
    st.title("🚗 Used Vehicle Market Analysis Dashboard")
    st.markdown("---")
    st.markdown("### Welcome!")
    st.markdown("""
    Dive into insights from the used vehicle market across the US. 
    This dashboard provides interactive visualizations of vehicle listings, pricing trends, and regional availability.
    """)
    
    if not df.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Listings", f"{len(df):,}")
        with col2:
            st.metric("Unique Brands", df['manufacturer'].nunique())
        with col3:
            st.metric("Avg Price", f"${df['price'].mean():,.2f}")

        st.markdown("---")
        st.markdown("### Dataset Preview (Top 10 Rows)")
        st.dataframe(df.head(10), use_container_width=True)
    else:
        st.error("Dataset not found or failed to load.")

elif page == "Models by Company":
    st.subheader("Models by Manufacturer")
    if not df.empty:
        selected_brand = st.selectbox("Choose a Company:", sorted(df['manufacturer'].unique()))
        brand_df = df[df['manufacturer'] == selected_brand].dropna(subset=['model']).copy()
        
        # Convert model to string for search functionality
        brand_df['model'] = brand_df['model'].astype(str)
        search_query = st.text_input("Search for a specific model:").lower()

        if search_query:
            brand_df = brand_df[brand_df['model'].str.lower().str.contains(search_query)]

        if not brand_df.empty:
            # Using observed=True for categorical grouping efficiency
            grouped = brand_df.groupby('model', observed=True).agg({
                'price': 'mean',
                'drive': lambda x: x.mode().iat[0] if not x.mode().empty else 'N/A',
                'type': lambda x: x.mode().iat[0] if not x.mode().empty else 'N/A',
                'transmission': lambda x: x.mode().iat[0] if not x.mode().empty else 'N/A',
                'fuel': lambda x: x.mode().iat[0] if not x.mode().empty else 'N/A',
                'cylinders': lambda x: x.mode().iat[0] if not x.mode().empty else 'N/A',
                'year': lambda x: int(x.median()) if not x.isnull().all() else 'N/A'
            }).reset_index()

            for _, row in grouped.iterrows():
                with st.expander(f"Model: {row['model']}"):
                    st.write(f"**Avg Price:** ${row['price']:,.2f} | **Median Year:** {row['year']}")
                    st.write(f"**Specs:** {row['drive']} drive, {row['type']} type, {row['transmission']} transmission")
                    st.write(f"**Engine:** {row['fuel']} fuel, {row['cylinders']} cylinders")
        else:
            st.warning("No models found for this selection.")

elif page == "Most Listed Vehicle Brands":
    st.subheader("Most Listed Vehicle Brands")
    if not df.empty:
        manufacturer_counts = df.manufacturer.value_counts().nlargest(10)
        fig_manu = px.pie(
            names=manufacturer_counts.index, 
            values=manufacturer_counts.values, 
            title="Top 10 Manufacturers",
            hole=0.4
        )
        st.plotly_chart(fig_manu, use_container_width=True)

elif page == "Transmission vs Type":
    st.subheader("Transmission vs Type")
    if not df.empty:
        fig_trans_type = px.histogram(
            df, x="transmission", color="type", 
            title="Transmission vs Type", barmode="group"
        )
        st.plotly_chart(fig_trans_type, use_container_width=True)

elif page == "Manufacturer vs Drive":
    st.subheader("Manufacturer vs Drive")
    if not df.empty:
        # Limited to top 15 manufacturers to keep the chart readable
        top_15 = df['manufacturer'].value_counts().nlargest(15).index
        filtered_df = df[df['manufacturer'].isin(top_15)]
        
        fig_drive = px.bar(
            filtered_df, x="manufacturer", color="drive", 
            title="Top 15 Manufacturers vs Drive Type", barmode="group"
        )
        st.plotly_chart(fig_drive, use_container_width=True)

elif page == "Brand-Specific Heatmap":
    st.subheader("Geographic Distribution Heatmap")
    if not df.empty:
        selected_brand = st.selectbox("Select a Manufacturer for Mapping:", sorted(df['manufacturer'].unique()))
        brand_df = df[df['manufacturer'] == selected_brand].dropna(subset=['lat', 'long'])

        if not brand_df.empty:
            st.info(f"Showing heatmap for {len(brand_df):,} listings.")
            # Center map on average coordinates
            m = folium.Map(location=[brand_df['lat'].mean(), brand_df['long'].mean()], zoom_start=4)
            
            # Use max 3000 points to ensure the map renders smoothly in-browser
            heat_data = brand_df[['lat', 'long']].head(3000).values.tolist()
            HeatMap(heat_data, radius=10, blur=15).add_to(m)
            folium_static(m)
        else:
            st.warning("No location data found for this brand.")
