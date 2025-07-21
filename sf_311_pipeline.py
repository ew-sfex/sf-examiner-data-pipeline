#!/usr/bin/env python3
# DataSF to Datawrapper Automation Pipeline - 311 Service Requests
# For San Francisco Examiner

import os
import pandas as pd
from sodapy import Socrata
import datawrapper
import logging
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sf_311_pipeline.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# API Credentials
DATAWRAPPER_API_KEY = os.environ.get("DATAWRAPPER_API_KEY", "BVIPEwcGz4XlfLDxrzzpio0Fu9OBlgTSE8pYKNWxKF8lzxz89BHMI3zT1VWQrF2Y")
DATASF_APP_TOKEN = os.environ.get("DATASF_APP_TOKEN", "xdboBmIBQtjISZqIRYDWjKyxY")

# Initialize API clients
dw = datawrapper.Datawrapper(access_token=DATAWRAPPER_API_KEY)
client = Socrata("data.sfgov.org", DATASF_APP_TOKEN)

# Configuration for 311 charts
CHART_CONFIGS = {
    "street_cleaning_monthly_comparison": {
        "dataset_id": "vw6y-z8j6",
        "chart_id": "Fgte7",
        "query": "SELECT date_extract_m(requested_datetime) AS month, date_extract_y(requested_datetime) AS year, COUNT(*) AS count WHERE service_name = 'Street and Sidewalk Cleaning' AND requested_datetime >= '{}' AND requested_datetime <= '{}' GROUP BY year, month ORDER BY year ASC, month ASC",
        "title": "Street and Sidewalk Cleaning Requests",
        "description": "Comparing monthly patterns across years"
    },
    "graffiti_monthly_comparison": {
        "dataset_id": "vw6y-z8j6",
        "chart_id": "aswDZ",
        "query": "SELECT date_extract_m(requested_datetime) AS month, date_extract_y(requested_datetime) AS year, COUNT(*) AS count WHERE service_name LIKE 'Graffiti%' AND requested_datetime >= '{}' AND requested_datetime <= '{}' GROUP BY year, month ORDER BY year ASC, month ASC",
        "title": "Graffiti Reports",
        "description": "Comparing monthly patterns across years"
    },
    "encampments_monthly_comparison": {
        "dataset_id": "vw6y-z8j6",
        "chart_id": "BJfSt",
        "query": "SELECT date_extract_m(requested_datetime) AS month, date_extract_y(requested_datetime) AS year, COUNT(*) AS count WHERE (service_name = 'Encampment' OR service_name = 'Encampments') AND requested_datetime >= '{}' AND requested_datetime <= '{}' GROUP BY year, month ORDER BY year ASC, month ASC",
        "title": "Encampment Reports",
        "description": "Comparing monthly patterns across years"
    },
    "tree_maintenance_monthly_comparison": {
        "dataset_id": "vw6y-z8j6",
        "chart_id": "dQte4",
        "query": "SELECT date_extract_m(requested_datetime) AS month, date_extract_y(requested_datetime) AS year, COUNT(*) AS count WHERE service_name = 'Tree Maintenance' AND requested_datetime >= '{}' AND requested_datetime <= '{}' GROUP BY year, month ORDER BY year ASC, month ASC",
        "title": "Tree Maintenance Requests",
        "description": "Comparing monthly patterns across years"
    },
    "abandoned_vehicles_monthly_comparison": {
        "dataset_id": "vw6y-z8j6",
        "chart_id": "R3cXx",
        "query": "SELECT date_extract_m(requested_datetime) AS month, date_extract_y(requested_datetime) AS year, COUNT(*) AS count WHERE (service_subtype LIKE '%abandoned_vehicle%' OR service_name = 'Abandoned Vehicle') AND requested_datetime >= '{}' AND requested_datetime <= '{}' GROUP BY year, month ORDER BY year ASC, month ASC",
        "title": "Abandoned Vehicle Reports",
        "description": "Comparing monthly patterns across years"
    }
}

def get_data_from_datasf(chart_config):
    """Fetch data from DataSF API based on chart configuration."""
    client = Socrata("data.sfgov.org", app_token=DATASF_APP_TOKEN)
    
    # First, find the latest date in the dataset
    latest_date_query = f"SELECT MAX(requested_datetime) as latest_date FROM {chart_config['dataset_id']}"
    try:
        latest_date_result = client.get(chart_config['dataset_id'], query=latest_date_query)
        if latest_date_result:
            latest_date = datetime.fromisoformat(latest_date_result[0]['latest_date'].split('T')[0])
            # Set end_date to the end of the current month
            end_date = datetime.now().replace(day=1, hour=23, minute=59, second=59)
            # Add one month and subtract one day to get end of current month
            if end_date.month == 12:
                end_date = end_date.replace(year=end_date.year + 1, month=1)
            else:
                end_date = end_date.replace(month=end_date.month + 1)
            end_date = end_date - timedelta(days=1)
            logging.info(f"Latest data available through: {end_date.strftime('%Y-%m-%d')}")
        else:
            # Fallback to current date if we can't determine the latest date
            end_date = datetime.now().replace(day=1, hour=23, minute=59, second=59)
            if end_date.month == 12:
                end_date = end_date.replace(year=end_date.year + 1, month=1)
            else:
                end_date = end_date.replace(month=end_date.month + 1)
            end_date = end_date - timedelta(days=1)
    except Exception as e:
        logging.warning(f"Could not determine latest date, using current date: {str(e)}")
        end_date = datetime.now().replace(day=1, hour=23, minute=59, second=59)
        if end_date.month == 12:
            end_date = end_date.replace(year=end_date.year + 1, month=1)
        else:
            end_date = end_date.replace(month=end_date.month + 1)
        end_date = end_date - timedelta(days=1)
    
    # Calculate start date as January 2020
    start_date = datetime(2020, 1, 1)
    
    # Format dates for query
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    # Get the base query from config and format it with dates if needed
    query = chart_config['query']
    if '{' in query:  # Check if query needs date formatting
        formatted_query = query.format(start_date_str, end_date_str)
    else:
        formatted_query = query
        
    logging.info(f"Executing query: {formatted_query}")
    
    try:
        results = client.get(chart_config['dataset_id'], query=formatted_query)
        df = pd.DataFrame.from_records(results)
        
        if not df.empty and 'month' in df.columns and 'year' in df.columns:
            # Log raw data for debugging
            logging.info(f"Raw data before pivoting:\n{df}")
            
            # Convert month numbers to month names
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            df['month'] = df['month'].astype(int).map(lambda x: month_names[x-1])
            
            # Ensure proper ordering of months
            df['month'] = pd.Categorical(df['month'], categories=month_names, ordered=True)
            
            # Pivot the data to create columns for each year
            df_pivot = df.pivot(index='month', columns='year', values='count')
            
            # Ensure all months are present in correct order
            df_pivot = df_pivot.reindex(month_names)
            
            # Reset index to make month a column again
            df_pivot.reset_index(inplace=True)
            df = df_pivot
            
            # Ensure year columns are in order
            year_cols = [col for col in df.columns if col != 'month']
            df = df[['month'] + sorted(year_cols)]
            
        logging.info(f"Retrieved {len(df)} records from DataSF")
        if not df.empty:
            logging.info(f"Sample of retrieved data:\n{df.head()}")
            if 'month' in df.columns:
                logging.info(f"Unique months in data: {df['month'].unique().tolist()}")
        return df
    except Exception as e:
        logging.error(f"Error fetching data from DataSF: {str(e)}")
        raise

def update_datawrapper_chart(chart_id, data, title=None):
    """Update a Datawrapper chart with new data"""
    try:
        logger.info(f"Updating Datawrapper chart {chart_id}")
        
        # Update data
        dw.add_data(chart_id, data)
        
        # Get the years from the data columns (excluding 'month' column)
        years = sorted([str(col) for col in data.columns if col != 'month'])
        
        # Create color mapping with the SF Examiner colors
        colors = {}
        line_settings = {}
        sf_colors = ["#cf4236", "#ffd74c", "#7e883f", "#80d0d8", "#e3cbac", "#CCC9c8"]
        
        # Assign colors in reverse order so most recent year is red
        for i, year in enumerate(reversed(years)):
            colors[year] = sf_colors[min(i, len(sf_colors) - 1)]
            line_settings[year] = {
                "stroke": "3px",
                "type": "line",
                "value-labels": False,
                "tooltip": True,
                "interpolation": "linear",
                "symbols": {
                    "enabled": True if i == 0 else False,
                    "type": "circle",
                    "fill": sf_colors[min(i, len(sf_colors) - 1)],
                    "stroke": sf_colors[min(i, len(sf_colors) - 1)],
                    "size": 5
                }
            }
        
        current_date = datetime.now().strftime("%B %d, %Y")
        metadata = {
            "describe": {
                "source-name": "DataSF",
                "source-url": "https://datasf.org/opendata/",
                "intro": f"Data updated on {current_date}",
                "byline": "San Francisco Examiner",
                "title": title
            },
            "visualize": {
                "type": "d3-lines",
                "interpolation": "linear",
                "custom-colors": colors,
                "y-grid": "on",
                "y-grid-format": "0,0",
                "y-grid-labels": "auto",
                "y-grid-subdivide": True,
                "value-label-colors": True,
                "label-colors": True,
                "lines": line_settings,
                "connect-null-values": False,
                "null-value-handling": "gap",
                "line-width": 3
            },
            "axes": {
                "y": {
                    "min": 0,
                    "label": "Number of Reports"
                },
                "x": {
                    "range": [0, 11],
                    "ticks": "all",
                    "grid": False
                }
            }
        }
        
        dw.update_chart(chart_id, metadata=metadata)
        logger.info(f"Updated chart metadata for {chart_id}")
        
        # Publish chart
        dw.publish_chart(chart_id)
        
        # Get the published URL using the newer get_chart method
        chart_info = dw.get_chart(chart_id)
        published_url = chart_info.get("publicUrl", "Unknown URL")
        
        logger.info(f"Chart published successfully: {published_url}")
        return published_url
    
    except Exception as e:
        logger.error(f"Error updating Datawrapper chart: {e}")
        raise

def process_and_update_chart(config_name):
    """Process data and update a specific chart"""
    config = CHART_CONFIGS[config_name]
    if not config["chart_id"]:
        logger.warning(f"Chart ID not configured for {config_name}")
        return
    
    try:
        # Get data
        data = get_data_from_datasf(config)
        
        # For monthly comparison chart, add custom title to show date range
        if config_name == "street_cleaning_monthly_comparison":
            # Get the years from the dataframe columns (exclude the 'month' column)
            years = [str(col) for col in data.columns if col != 'month']
            date_range = f"{years[0]} - {years[-1]}"
            
            # Update the title to include the date range
            dynamic_title = f"{config['title']} ({date_range})"
        else:
            dynamic_title = config['title']
        
        # Update chart
        update_datawrapper_chart(
            chart_id=config["chart_id"],
            data=data,
            title=dynamic_title
        )
        logger.info(f"Successfully updated {config_name} chart")
    
    except Exception as e:
        logger.error(f"Failed to update {config_name} chart: {e}")

def update_all_charts():
    """Update all configured charts"""
    logger.info("Starting scheduled update of all charts")
    for chart_name in CHART_CONFIGS:
        process_and_update_chart(chart_name)
    logger.info("Completed update of all charts")

if __name__ == "__main__":
    update_all_charts() 