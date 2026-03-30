# VehiclePro: Used Vehicle Market Intelligence Dashboard

###  Project Overview
This project is an interactive Data Science dashboard built using **Streamlit**. It analyzes a massive dataset of used vehicle listings across the US to provide insights into market share, pricing trends, and regional availability.

###  Dataset Details
The dataset used in this project originally exceeded 1GB in CSV format. 
- **Source:** [https://www.kaggle.com/datasets/austinreese/craigslist-carstrucks-data)(US Used Cars D Market).
- **Size:** Optimized to 452MB (Parquet format) for performance.
- **Key Features:** Manufacturer, Model, Year, Price, Fuel Type, Transmission, Drive Configuration, and Geospatial Coordinates (Lat/Long).

###  Technical Implementation
- **Data Engineering:** Converted raw CSV to **Apache Parquet** to reduce disk space by 60% and improve loading speed.
- **Cloud Integration:** Hosted the dataset on Google Drive and implemented **`gdown`** for robust automated data retrieval.
- **Memory Management:** Implemented column pruning and downcasting (float64 to float32) to stay within the 1GB RAM limit of Streamlit Cloud.
- **Visualization:** Used **Plotly Express** for hierarchical sunburst charts and LOWESS trendlines, and **Folium** for geographic density heatmaps.

### Methodology
- ***This dashboard was developed to analyze used vehicle market dynamics. 
    The primary goal was to handle a large-scale dataset efficiently in a cloud environment.

    ### Data Processing Pipeline
    1. **Ingestion:** Data is pulled from a remote cloud source via `gdown`.
    2. **Optimization:** We utilize **Parquet** columnar storage. Unlike CSVs, Parquet allows us to load only the specific columns needed for a visualization, drastically reducing RAM usage.
    3. **Cleaning:** Automated removal of 'Other' categories and 'NaN' values to ensure statistical integrity.
    4. **Transformation:** Numerical features are downcast, and repetitive strings are converted to **Categorical** dtypes to optimize memory footprint.

    ### Key Insights Provided
    - **Inventory Analysis:** Deep dive into specific manufacturer stock.
    - **Market Share:** Hierarchical view of body styles and drive configurations.
    - **Depreciation:** Visualizing how different fuel types lose value over time.
    - **Regional Supply:** Identifying geographic hotspots for specific brands.
