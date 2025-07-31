#!/usr/bin/env python3
# DataSF to Datawrapper Automation Pipeline - 911 Call Data
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
        logging.FileHandler("sf_911_pipeline.log"),
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

# Configuration for 911 charts
CHART_CONFIGS = {
    "violent_crimes_monthly_comparison": {
        "dataset_id": "wg3w-h783",  # Police Department Incident Reports 2018 to Present
        "chart_id": "1DNOm",  # Violent crimes trend chart
        "query": "SELECT date_extract_m(incident_date) AS month, date_extract_y(incident_date) AS year, COUNT(*) AS count WHERE incident_category IN ('Homicide', 'Robbery', 'Assault', 'Sex Offense') AND incident_date >= '{}' AND incident_date <= '{}' GROUP BY year, month ORDER BY year ASC, month ASC",
        "title": "Violent Crime Incidents",
        "description": "Comparing monthly patterns across years",
        "color": "#cf4236"  # SF Examiner red
    },
    "property_crimes_monthly_comparison": {
        "dataset_id": "wg3w-h783",
        "chart_id": "MRgFo",  # Property crimes trend chart
        "query": "SELECT date_extract_m(incident_date) AS month, date_extract_y(incident_date) AS year, COUNT(*) AS count WHERE incident_category IN ('Burglary', 'Larceny Theft', 'Motor Vehicle Theft', 'Arson') AND incident_date >= '{}' AND incident_date <= '{}' GROUP BY year, month ORDER BY year ASC, month ASC",
        "title": "Property Crime Incidents",
        "description": "Comparing monthly patterns across years",
        "color": "#ffd74c"  # SF Examiner yellow
    },
    "drug_offenses_monthly_comparison": {
        "dataset_id": "wg3w-h783",
        "chart_id": "ZquUz",  # Drug offenses trend chart
        "query": "SELECT date_extract_m(incident_date) AS month, date_extract_y(incident_date) AS year, COUNT(*) AS count WHERE incident_category = 'Drug Offense' AND incident_date >= '{}' AND incident_date <= '{}' GROUP BY year, month ORDER BY year ASC, month ASC",
        "title": "Drug Offense Incidents",
        "description": "Comparing monthly patterns across years",
        "color": "#7e883f"  # SF Examiner green
    },
    "vehicle_related_monthly_comparison": {
        "dataset_id": "wg3w-h783",
        "chart_id": "Z9xal",  # Vehicle-related incidents trend chart
        "query": "SELECT date_extract_m(incident_date) AS month, date_extract_y(incident_date) AS year, COUNT(*) AS count WHERE incident_category IN ('Traffic Collision', 'Traffic Violation', 'Motor Vehicle Theft') AND incident_date >= '{}' AND incident_date <= '{}' GROUP BY year, month ORDER BY year ASC, month ASC",
        "title": "Vehicle-Related Incidents",
        "description": "Comparing monthly patterns across years",
        "color": "#80d0d8"  # SF Examiner blue
    },
    "firearms_monthly_comparison": {
        "dataset_id": "wg3w-h783",
        "chart_id": "DgPPX",  # Firearm-related incidents trend chart
        "query": "SELECT date_extract_m(incident_date) AS month, date_extract_y(incident_date) AS year, COUNT(*) AS count WHERE (incident_category IN ('Weapons Carrying Etc', 'Weapons Offense') OR incident_subcategory IN ('Robbery - Armed with Gun', 'Assault - Gun', 'Assault with a Gun', 'Discharge of a Firearm', 'Illegal Discharge of a Firearm')) AND incident_date >= '{}' AND incident_date <= '{}' GROUP BY year, month ORDER BY year ASC, month ASC",
        "title": "Firearm-Related Incidents",
        "description": "Comparing monthly patterns across years",
        "color": "#e3cbac"  # SF Examiner tan
    }
}

def get_data_from_datasf(chart_config):
    """Fetch data from DataSF API based on chart configuration."""
    client = Socrata("data.sfgov.org", app_token=DATASF_APP_TOKEN)
    
    # First, find the latest date in the dataset
    latest_date_query = f"SELECT MAX(incident_date) as latest_date FROM {chart_config['dataset_id']}"
    try:
        latest_date_result = client.get(chart_config['dataset_id'], query=latest_date_query)
        if latest_date_result:
            latest_date = datetime.fromisoformat(latest_date_result[0]['latest_date'].split('T')[0])
            # Set end_date to the last day of the month for the latest available date
            end_date = latest_date.replace(day=1) - timedelta(days=1)
            logging.info(f"Latest data available through: {end_date.strftime('%Y-%m-%d')}")
        else:
            # Fallback to current date if we can't determine the latest date
            end_date = datetime.now()
            if end_date.day <= 5:  # If within first 5 days of month, use previous month as end date
                end_date = end_date.replace(day=1) - timedelta(days=1)
            end_date = end_date.replace(day=1) - timedelta(days=1)  # Last day of previous month
    except Exception as e:
        logging.warning(f"Could not determine latest date, using current date: {str(e)}")
        end_date = datetime.now()
        if end_date.day <= 5:
            end_date = end_date.replace(day=1) - timedelta(days=1)
        end_date = end_date.replace(day=1) - timedelta(days=1)
    
    # Calculate start date as January of 5 years ago
    start_date = datetime(datetime.now().year - 5, 1, 1)
    
    # Format dates for query
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    # Get the base query from config and format it with dates if needed
    query = chart_config['query']
    formatted_query = query.format(start_date_str, end_date_str)
        
    logging.info(f"Executing query: {formatted_query}")
    
    try:
        results = client.get(chart_config['dataset_id'], query=formatted_query)
        df = pd.DataFrame.from_records(results)
        
        if not df.empty and 'month' in df.columns and 'year' in df.columns:
            # Log raw data for debugging
            logging.info(f"Raw data before pivoting:\n{df.head()}")
            
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

def update_datawrapper_chart(chart_id, data, config):
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
        
        # Get the primary color from config
        primary_color = config.get("color", "#cf4236")
        
        # Additional SF Examiner colors
        sf_colors = ["#cf4236", "#ffd74c", "#7e883f", "#80d0d8", "#e3cbac", "#CCC9c8"]
        
        # Assign colors in reverse order so most recent year is red
        for i, year in enumerate(reversed(years)):
            # Use red (#cf4236) for the most recent year, then cycle through others
            if i == 0:
                colors[year] = "#cf4236"  # Always red for most recent year
            else:
                colors[year] = sf_colors[min(i + 1, len(sf_colors) - 1)]
            
            line_settings[year] = {
                "stroke": "3px",
                "type": "line",
                "value-labels": False,
                "tooltip": True,
                "interpolation": "linear",
                "symbols": {
                    "enabled": True if i == 0 else False,
                    "type": "circle",
                    "fill": colors[year],
                    "stroke": colors[year],
                    "size": 5
                }
            }
        
        # Calculate the date range for display
        date_range = f"{years[0]} - {years[-1]}"
        
        # Create the title with date range
        title = f"{config['title']} ({date_range})"
        
        current_date = datetime.now().strftime("%B %d, %Y")
        metadata = {
            "describe": {
                "source-name": "DataSF - Police Department Incident Reports",
                "source-url": "https://data.sfgov.org/Public-Safety/Police-Department-Incident-Reports-2018-to-Present/wg3w-h783",
                "intro": "",
                "byline": "San Francisco Examiner",
                "title": title
            },
            "annotate": {
                "notes": f"Data updated on {current_date}"
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
                    "label": "Number of Incidents"
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
        
        # Update chart
        update_datawrapper_chart(
            chart_id=config["chart_id"],
            data=data,
            config=config
        )
        logger.info(f"Successfully updated {config_name} chart")
    
    except Exception as e:
        logger.error(f"Failed to update {config_name} chart: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

def update_all_charts():
    """Update all configured charts"""
    logger.info("Starting scheduled update of all 911 charts")
    for chart_name in CHART_CONFIGS:
        process_and_update_chart(chart_name)
    logger.info("Completed update of all 911 charts")

if __name__ == "__main__":
    update_all_charts() 