import streamlit as st
import pandas as pd
import plotly.express as px
import folium
import gdown
import os
from streamlit_folium import folium_static
from folium.plugins import HeatMap

# 1. Page Config & Professional Branding
st.set_page_config(page_title="Vehicle Analytics Pro", layout="wide")

#  CSS for UI Polish and Spec Cards
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 26px; color: #00d4ff; }
    section[data-testid="stSidebar"] { background-color: #161b22; }
    
    .spec-card {
        border: 1px solid #333; 
        padding: 20px; 
        border-radius: 12px; 
        background-color: #1e252e;
        margin-bottom: 20px;
        min-height: 280px; 
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .spec-label { color: #888; font-size: 11px; text-transform: uppercase; }
    .spec-value { color: #ffffff; font-size: 14px; font-weight: 500; margin-bottom: 10px; }
    .model-title { color: #00d4ff; margin-top: 0; margin-bottom: 15px; font-size: 1.1rem; border-bottom: 1px solid #333; padding-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA CONFIGURATION ---
FILE_ID = "17VhcD1SApY6M1escKpKloilcO3XAMeWK"
OUTPUT_FILE = "vehicles.parquet"

@st.cache_data(show_spinner="Syncing and Cleaning Data...")
def load_data(file_id):
    url = f'https://drive.google.com/uc?id={file_id}'
    if not os.path.exists(OUTPUT_FILE):
        gdown.download(url, OUTPUT_FILE, quiet=False)
    try:
        cols = ["manufacturer", "model", "year", "price", "lat", "long", 
                "fuel", "drive", "transmission", "type"]
        df = pd.read_parquet(OUTPUT_FILE, columns=cols)
        
        # --- CLEANING ---
        clean_cols = ["manufacturer", "fuel", "transmission", "type", "drive"]
        for col in clean_cols:
            if col in df.columns:
                df = df[~df[col].astype(str).str.lower().str.contains("other", na=False)]

        # Optimization
        df['price'] = pd.to_numeric(df['price'], downcast='float')
        df['year'] = pd.to_numeric(df['year'], downcast='integer')
        
        return df.dropna(subset=["manufacturer", "model", "price", "type", "drive"])
    except Exception as e:
        st.error(f"Load Error: {e}"); return pd.DataFrame()

df = load_data(FILE_ID)

# --- SIDEBAR NAVIGATION ---
st.sidebar.markdown("<h1 style='text-align: center; color: #00d4ff;'>VehiclePro</h1>", unsafe_allow_html=True)
st.sidebar.markdown("---")

page = st.sidebar.radio("NAVIGATE EXPLORER", [
    "Dashboard Home", 
    "Manufacturer Inventory",
    "Market Trends", 
    "Regional Heatmap"
])


# --- PAGES ---

if page == "Dashboard Home":
    st.title("Market Intelligence Dashboard")
    if not df.empty:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Active Listings", f"{len(df):,}")
        c2.metric("Market Brands", df['manufacturer'].nunique())
        c3.metric("Avg Price", f"${df['price'].mean():,.0f}")
        
        top_brand = df['manufacturer'].value_counts().index[0]
        top_val = (df['manufacturer'].value_counts().iloc[0] / len(df)) * 100
        c4.metric(f"Market Leader ({top_brand.title()})", f"{top_val:.1f}% Share")
        
        st.markdown("---")
        st.markdown("### Sample Inventory Stream")
        st.dataframe(df.head(15), use_container_width=True)

elif page == "Manufacturer Inventory":
    st.title("Manufacturer Inventory")
    if not df.empty:
        brand = st.selectbox("Select a Manufacturer:", sorted(df['manufacturer'].unique()))
        b_df = df[df['manufacturer'] == brand].copy()
        b_df['model'] = b_df['model'].astype(str)
        
        search = st.text_input("Filter Model Name:")
        if search:
            b_df = b_df[b_df['model'].str.contains(search, case=False)]

        grouped = b_df.groupby('model', observed=True).agg({
            'price': 'mean', 'year': 'median',
            'fuel': lambda x: x.mode().iat[0] if not x.mode().empty else 'N/A',
            'transmission': lambda x: x.mode().iat[0] if not x.mode().empty else 'N/A',
            'drive': lambda x: x.mode().iat[0] if not x.mode().empty else 'N/A',
            'type': lambda x: x.mode().iat[0] if not x.mode().empty else 'N/A'
        }).reset_index().head(24)

        cols = st.columns(3)
        for i, (idx, row) in enumerate(grouped.iterrows()):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="spec-card">
                    <h3 class="model-title">{row['model'].title()}</h3>
                    <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                        <div style="flex: 1; min-width: 100px;">
                            <div class="spec-label">Avg Price</div>
                            <div class="spec-value">${row['price']:,.0f}</div>
                            <div class="spec-label">Fuel</div>
                            <div class="spec-value">{row['fuel'].title()}</div>
                        </div>
                        <div style="flex: 1; min-width: 100px;">
                            <div class="spec-label">Median Year</div>
                            <div class="spec-value">{int(row['year'])}</div>
                            <div class="spec-label">Gearbox</div>
                            <div class="spec-value">{row['transmission'].title()}</div>
                        </div>
                    </div>
                    <div style="margin-top: 10px;">
                        <div class="spec-label">Drive / Configuration</div>
                        <div class="spec-value">{row['drive'].upper()} • {row['type'].title()}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

elif page == "Market Trends":
    st.title("Advanced Market Share & Trends")
    
    t1, t2, t3, t4 = st.tabs([
        "Price Depreciation", 
        "Market Share (Hierarchical)", 
        "Price Ranking", 
        "Market Volume"
    ])
    
    with t1:
        st.subheader("Depreciation Curve by Fuel Type")
        sample_df = df.sample(min(len(df), 2500))
        fig_trend = px.scatter(sample_df, x="year", y="price", color="fuel",
                               trendline="lowess", template="plotly_dark", opacity=0.4)
        st.plotly_chart(fig_trend, use_container_width=True)

    with t2:
        st.subheader("Body Style & Drive Configuration Market Share")
        sun_df = df.dropna(subset=['type', 'drive']).sample(min(len(df), 2000))
        fig_sun = px.sunburst(
            sun_df, 
            path=['type', 'drive'], 
            values='price', 
            color='type',
            template="plotly_dark",
            color_discrete_sequence=px.colors.sequential.Tealgrn,
            title="Interactive Hierarchy of Vehicle Types"
        )
        st.plotly_chart(fig_sun, use_container_width=True)
        st.info("Click on a center slice to drill down into specific drive configurations.")

    with t3:
        st.subheader("Top 15 Most Expensive Brands (Average)")
        avg_price_df = df.groupby('manufacturer')['price'].mean().sort_values(ascending=False).head(15).reset_index()
        fig_bar = px.bar(avg_price_df, x='price', y='manufacturer', orientation='h',
                         color='price', color_continuous_scale='Tealgrn', template="plotly_dark")
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)

    with t4:
        st.subheader("Market Volume by Vehicle Type")
        type_counts = df['type'].value_counts().reset_index()
        type_counts.columns = ['type', 'count']
        fig_pie = px.pie(type_counts, values='count', names='type', hole=0.4, 
                         template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_pie, use_container_width=True)

elif page == "Regional Heatmap":
    st.title("Geographic Supply Density")
    brand_m = st.selectbox("Filter Map by Brand:", sorted(df['manufacturer'].unique()))
    m_df = df[df['manufacturer'] == brand_m].dropna(subset=['lat', 'long'])
    if not m_df.empty:
        center = [m_df['lat'].mean(), m_df['long'].mean()]
        m = folium.Map(location=center, zoom_start=4, tiles="CartoDB dark_matter")
        HeatMap(m_df[['lat', 'long']].sample(min(len(m_df), 2000)).values.tolist(), radius=10, blur=15).add_to(m)
        folium_static(m)
