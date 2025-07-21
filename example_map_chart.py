#!/usr/bin/env python3
# Example Map Chart - San Francisco Crime Incidents
# For San Francisco Examiner

import os
import pandas as pd
from sodapy import Socrata
import datawrapper
import logging
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Credentials
DATAWRAPPER_API_KEY = os.environ.get("DATAWRAPPER_API_KEY", "YOUR_DATAWRAPPER_API_KEY")
DATASF_APP_TOKEN = os.environ.get("DATASF_APP_TOKEN", "YOUR_DATASF_APP_TOKEN")

# Initialize API clients
dw = datawrapper.Datawrapper(access_token=DATAWRAPPER_API_KEY)
client = Socrata("data.sfgov.org", DATASF_APP_TOKEN)

def get_recent_sf_crime_data():
    """
    Get crime incidents from the past 7 days
    Uses SF Police Department Incident Reports dataset
    """
    # Calculate date 7 days ago
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%S')
    
    # Query for recent incidents with location data
    query = f"""
    SELECT 
        incident_datetime,
        incident_category,
        incident_description,
        latitude,
        longitude,
        police_district
    WHERE 
        incident_datetime >= '{seven_days_ago}'
        AND latitude IS NOT NULL 
        AND longitude IS NOT NULL
    LIMIT 1000
    """
    
    # SF Police Department Incident Reports 2018 to Present dataset ID
    dataset_id = "wg3w-h783"
    
    logger.info(f"Fetching crime data since {seven_days_ago}")
    results = client.query(dataset_id, query=query)
    
    # Convert to pandas DataFrame
    df = pd.DataFrame.from_records(results)
    logger.info(f"Retrieved {len(df)} crime incidents")
    
    return df

def create_crime_map_chart(data):
    """Create or update a symbol map of recent crime incidents"""
    # Create a new chart or use an existing one
    # For production use, you should use an existing chart_id
    
    # Create new chart
    chart_info = dw.create_chart(
        title="Recent Crime Incidents in San Francisco",
        type="d3-maps-symbols"
    )
    chart_id = chart_info['id']
    logger.info(f"Created new chart with ID: {chart_id}")
    
    # Upload data
    dw.add_data(chart_id, data)
    logger.info("Uploaded data to chart")
    
    # Configure the chart
    properties = {
        "metadata": {
            "describe": {
                "intro": f"Incidents reported in the past 7 days (as of {datetime.now().strftime('%B %d, %Y')})",
                "byline": "San Francisco Examiner",
                "source-name": "DataSF - SF Police Department",
                "source-url": "https://data.sfgov.org/"
            },
        },
        "visualize": {
            "tooltip": {
                "title": "{{ incident_category }}",
                "body": "Time: {{ incident_datetime }}<br>Description: {{ incident_description }}<br>District: {{ police_district }}",
                "fields": {
                    "incident_category": "incident_category",
                    "incident_datetime": "incident_datetime",
                    "incident_description": "incident_description",
                    "police_district": "police_district"
                }
            },
            "basemap": "san-francisco",  # Using San Francisco basemap
            "map-height": 500
        },
        "axes": {
            "lat": "latitude",
            "lon": "longitude",
            "color": "incident_category"
        }
    }
    
    dw.update_chart(chart_id, properties)
    logger.info("Updated chart properties")
    
    # Publish the chart
    dw.publish_chart(chart_id)
    
    # Get the published URL
    chart_info = dw.chart_properties(chart_id)
    published_url = chart_info.get("publicUrl", "Unknown URL")
    
    logger.info(f"Chart published successfully: {published_url}")
    return published_url

if __name__ == "__main__":
    try:
        # Get crime data
        crime_data = get_recent_sf_crime_data()
        
        # Create and publish the map
        chart_url = create_crime_map_chart(crime_data)
        
        print(f"Your crime map is available at: {chart_url}")
        
    except Exception as e:
        logger.error(f"Error creating crime map: {e}") 