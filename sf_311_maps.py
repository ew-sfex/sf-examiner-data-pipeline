#!/usr/bin/env python3
# DataSF to Datawrapper Automation Pipeline - 311 Service Request Maps
# For San Francisco Examiner

import os
import pandas as pd
from sodapy import Socrata
import datawrapper
import logging
from datetime import datetime, timedelta
import requests
import json
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sf_311_maps.log"),
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

# Configuration for 311 maps
MAP_CONFIGS = {
    "street_cleaning_map": {
        "dataset_id": "vw6y-z8j6",
        "chart_id": "nB5JE",  # New test map
        "service_filter": "service_name = 'Street and Sidewalk Cleaning'",
        "title": "Street and Sidewalk Cleaning Requests - Past 4 Weeks",
        "description": "Location of recent street cleaning requests",
        "marker_color": "#cf4236",  # SF Examiner red
        "tooltip_template": """<div style="font-family:Arial,sans-serif;line-height:1.3;">
<b>Street and Sidewalk Cleaning</b><br>
<b>Location:</b><br>{{ PROPER(address) }}<br>
<b>Neighborhood:</b><br>{{ PROPER(neighborhood) }}<br>
<b>Status:</b> <span style="color:{{ status == 'Closed' ? '#4a4' : '#d44' }}">{{ status }}</span><br>
<b>Reported:</b> {{ reported_datetime }} ({{ hours_ago }} hours ago)
</div>"""
    },
    "graffiti_map": {
        "dataset_id": "vw6y-z8j6",
        "chart_id": "0xtQT",  # Graffiti map
        "service_filter": "service_name LIKE 'Graffiti%'",
        "title": "Graffiti Reports - Past 4 Weeks",
        "description": "Location of recent graffiti reports",
        "marker_color": "#ffd74c",  # SF Examiner yellow
        "tooltip_template": """<div style="font-family:Arial,sans-serif;line-height:1.3;">
<b>Graffiti Report</b><br>
<b>Location:</b><br>{{ PROPER(address) }}<br>
<b>Neighborhood:</b><br>{{ PROPER(neighborhood) }}<br>
<b>Status:</b> <span style="color:{{ status == 'Closed' ? '#4a4' : '#d44' }}">{{ status }}</span><br>
<b>Reported:</b> {{ reported_datetime }} ({{ hours_ago }} hours ago)
</div>"""
    },
    "encampments_map": {
        "dataset_id": "vw6y-z8j6",
        "chart_id": "os0dX",
        "service_filter": "(service_name = 'Encampment' OR service_name = 'Encampments')",
        "title": "Encampment Reports - Past 4 Weeks",
        "description": "Location of recent encampment reports",
        "marker_color": "#7e883f",  # SF Examiner green
        "tooltip_template": """<div style="font-family:Arial,sans-serif;line-height:1.3;">
<b>Encampment Report</b><br>
<b>Location:</b><br>{{ PROPER(address) }}<br>
<b>Neighborhood:</b><br>{{ PROPER(neighborhood) }}<br>
<b>Status:</b> <span style="color:{{ status == 'Closed' ? '#4a4' : '#d44' }}">{{ status }}</span><br>
<b>Reported:</b> {{ reported_datetime }} ({{ hours_ago }} hours ago)
</div>"""
    },
    "tree_maintenance_map": {
        "dataset_id": "vw6y-z8j6",
        "chart_id": "9JMgr",
        "service_filter": "service_name = 'Tree Maintenance'",
        "title": "Tree Maintenance Requests - Past 4 Weeks",
        "description": "Location of recent tree maintenance requests",
        "marker_color": "#80d0d8",  # SF Examiner blue
        "tooltip_template": """<div style="font-family:Arial,sans-serif;line-height:1.3;">
<b>Tree Maintenance</b><br>
<b>Location:</b><br>{{ PROPER(address) }}<br>
<b>Neighborhood:</b><br>{{ PROPER(neighborhood) }}<br>
<b>Status:</b> <span style="color:{{ status == 'Closed' ? '#4a4' : '#d44' }}">{{ status }}</span><br>
<b>Reported:</b> {{ reported_datetime }} ({{ hours_ago }} hours ago)
</div>"""
    },
    "abandoned_vehicles_map": {
        "dataset_id": "vw6y-z8j6",
        "chart_id": "V5s4q",
        "service_filter": "(service_subtype LIKE '%abandoned_vehicle%' OR service_name = 'Abandoned Vehicle')",
        "title": "Abandoned Vehicle Reports - Past 4 Weeks",
        "description": "Location of recent abandoned vehicle reports",
        "marker_color": "#e3cbac",  # SF Examiner tan
        "tooltip_template": """<div style="font-family:Arial,sans-serif;line-height:1.3;">
<b>Abandoned Vehicle</b><br>
<b>Location:</b><br>{{ PROPER(address) }}<br>
<b>Neighborhood:</b><br>{{ PROPER(neighborhood) }}<br>
<b>Status:</b> <span style="color:{{ status == 'Closed' ? '#4a4' : '#d44' }}">{{ status }}</span><br>
<b>Reported:</b> {{ reported_datetime }} ({{ hours_ago }} hours ago)
</div>"""
    },
    "sewage_backups_map": {
        "dataset_id": "vw6y-z8j6",
        "chart_id": "Lu3TG",  # Sewage backups map
        "service_filter": "service_name = 'Sewer' AND service_subtype = 'sewage_back-up_discharge'",
        "title": "Sewage Backup Reports - Past 4 Weeks",
        "description": "Location of recent sewage backup reports",
        "marker_color": "#a57bc1",  # Purple for sewage issues
        "tooltip_template": """<div style="font-family:Arial,sans-serif;line-height:1.3;">
<b>Sewage Backup</b><br>
<b>Type:</b><br>{{ service_details }}<br>
<b>Location:</b><br>{{ PROPER(address) }}<br>
<b>Neighborhood:</b><br>{{ PROPER(neighborhood) }}<br>
<b>Status:</b> <span style="color:{{ status == 'Closed' ? '#4a4' : '#d44' }}">{{ status }}</span><br>
<b>Reported:</b> {{ reported_datetime }} ({{ hours_ago }} hours ago)
</div>"""
    },
    "street_sidewalk_defects_map": {
        "dataset_id": "vw6y-z8j6",
        "chart_id": "acPZT",  # Sidewalk and street defects map
        "service_filter": "(service_name = 'Sidewalk and Curb' OR service_name = 'Street Defect')",
        "title": "Sidewalk and Street Defects",
        "description": "Location of reported sidewalk, curb, and street defects",
        "marker_color": "#8B4513",  # Saddle brown for infrastructure issues
        "tooltip_template": """<div style="font-family:Arial,sans-serif;line-height:1.3;">
<b>Infrastructure Defect</b><br>
<b>Type:</b><br>{{ service_name }} - {{ service_subtype }}<br>
<b>Details:</b><br>{{ service_details }}<br>
<b>Location:</b><br>{{ PROPER(address) }}<br>
<b>Neighborhood:</b><br>{{ PROPER(neighborhood) }}<br>
<b>Status:</b> <span style="color:{{ status == 'Closed' ? '#4a4' : '#d44' }}">{{ status }}</span><br>
<b>Reported:</b> {{ reported_datetime }} ({{ hours_ago }} hours ago)
</div>"""
    },
    "human_waste_map": {
        "dataset_id": "vw6y-z8j6",
        "chart_id": "XDoKW",  # Human waste reports map
        "service_filter": "service_name = 'Street and Sidewalk Cleaning' AND service_details = 'human_waste_or_urine'",
        "title": "Human Waste Reports",
        "description": "Location of reported human waste or urine",
        "marker_color": "#8f4e35",  # Rust brown color
        "tooltip_template": """<div style="font-family:Arial,sans-serif;line-height:1.3;">
<b>Human Waste Report</b><br>
<b>Location:</b><br>{{ PROPER(address) }}<br>
<b>Neighborhood:</b><br>{{ PROPER(neighborhood) }}<br>
<b>Status:</b> <span style="color:{{ status == 'Closed' ? '#4a4' : '#d44' }}">{{ status }}</span><br>
<b>Reported:</b> {{ reported_datetime }} ({{ hours_ago }} hours ago)
</div>"""
    },
    "noise_complaints_map": {
        "dataset_id": "vw6y-z8j6",
        "chart_id": "AJzUh",  # Noise complaints map
        "service_filter": "service_name = 'Noise' AND agency_responsible IN ('Noise Report', 'Entertainment Commission', 'DPH Environmental Health - Noise')",
        "title": "Noise Complaints",
        "description": "Location of reported noise complaints and noise-related service requests",
        "marker_color": "#9932cc",  # Dark orchid purple
        "tooltip_template": """<div style="font-family:Arial,sans-serif;line-height:1.3;">
<b>Noise Complaint</b><br>
<b>Type:</b><br>{{ service_subtype }}<br>
<b>Location:</b><br>{{ PROPER(address) }}<br>
<b>Neighborhood:</b><br>{{ PROPER(neighborhood) }}<br>
<b>Agency:</b><br>{{ agency_responsible }}<br>
<b>Status:</b> <span style="color:{{ status == 'Closed' ? '#4a4' : '#d44' }}">{{ status }}</span><br>
<b>Reported:</b> {{ reported_datetime }} ({{ hours_ago }} hours ago)
</div>"""
    }
}

def get_map_data_from_datasf(chart_config):
    """Fetch location data from DataSF API for the most recent complete day."""
    
    # First, find the latest date in the dataset
    latest_date_query = f"""
    SELECT 
        requested_datetime
    WHERE 
        {chart_config['service_filter']}
        AND requested_datetime IS NOT NULL
    ORDER BY requested_datetime DESC
    LIMIT 1
    """
    
    try:
        latest_result = client.get(chart_config['dataset_id'], query=latest_date_query)
        if not latest_result:
            raise ValueError("No data found in dataset")
            
        latest_date = datetime.fromisoformat(latest_result[0]['requested_datetime'].split('T')[0])
        logging.info(f"Latest data available is from: {latest_date.strftime('%Y-%m-%d')}")
        
        # Use the last complete day
        end_date = latest_date.replace(hour=23, minute=59, second=59)
        # For maps, we want data from the most recent complete day
        # So we query for data from yesterday (start_date) to latest_date (end_date)
        start_date = end_date.replace(hour=0, minute=0, second=0)  # Start of the last complete day
        
    except Exception as e:
        logging.error(f"Error finding latest date, falling back to default date range: {str(e)}")
        # Fallback: use previous day
        end_date = datetime.now().replace(hour=23, minute=59, second=59) - timedelta(days=1)
        start_date = end_date - timedelta(days=1)
    
    # Format dates for query - end date should be next day for < comparison
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = (end_date + timedelta(days=1)).strftime('%Y-%m-%d')
    
    logging.info(f"Querying data for {start_date_str}")
    
    # Base query
    base_query = f"""
    SELECT 
        lat,
        long,
        requested_datetime,
        address,
        status_description,
        neighborhoods_sffind_boundaries,
        service_name,
        service_subtype,
        service_details,
        supervisor_district,
        police_district,
        source,
        agency_responsible
    WHERE 
        {chart_config['service_filter']}
        AND requested_datetime >= '{start_date_str}'
        AND requested_datetime < '{end_date_str}'
        AND lat IS NOT NULL
        AND long IS NOT NULL
    ORDER BY requested_datetime DESC
    """
    
    # Log the full query for debugging
    logging.info(f"Full query being executed:\n{base_query}")
    
    offset = 0
    limit = 1000
    all_results = []
    
    # Try a test query first to verify data exists
    test_query = f"""
    SELECT COUNT(*) as count
    WHERE {chart_config['service_filter']}
        AND requested_datetime >= '{start_date_str}'
        AND requested_datetime < '{end_date_str}'
    """
    logging.info(f"Executing test count query:\n{test_query}")
    try:
        count_result = client.get(chart_config['dataset_id'], query=test_query)
        total_count = int(count_result[0]['count']) if count_result else 0
        logging.info(f"Total records available for this query: {total_count}")
    except Exception as e:
        logging.error(f"Error executing test count query: {str(e)}")
        total_count = 0
    
    if total_count == 0:
        logging.warning(f"No data found for service filter: {chart_config['service_filter']}")
        logging.warning("Trying query without time filter to check if service exists...")
        test_query = f"SELECT COUNT(*) as count WHERE {chart_config['service_filter']}"
        try:
            count_result = client.get(chart_config['dataset_id'], query=test_query)
            total_count = int(count_result[0]['count']) if count_result else 0
            logging.info(f"Total records for service (all time): {total_count}")
        except Exception as e:
            logging.error(f"Error checking service existence: {str(e)}")
    
    while True:
        query = f"{base_query} LIMIT {limit} OFFSET {offset}"
        logging.info(f"Executing query with offset {offset}")
        
        try:
            results = client.get(chart_config['dataset_id'], query=query)
            if not results:
                break
                
            all_results.extend(results)
            if len(results) < limit:
                break
                
            offset += limit
            
        except Exception as e:
            logging.error(f"Error fetching data from DataSF at offset {offset}: {str(e)}")
            break
    
    df = pd.DataFrame.from_records(all_results)
    
    # Initialize final_df as empty DataFrame with required columns
    required_cols = [
        'lat', 'long', 'status', 'address', 'reported_datetime', 'hours_ago',
        'neighborhood', 'district', 'service_name', 'service_subtype',
        'service_details', 'source', 'agency_responsible'
    ]
    final_df = pd.DataFrame(columns=required_cols)
    
    if not df.empty:
        # Convert datetime
        df['requested_datetime'] = pd.to_datetime(df['requested_datetime'])
        
        # Prepare columns for the final dataset
        df['reported_datetime'] = df['requested_datetime'].dt.strftime('%B %d, %Y %I:%M %p')
        end_date_ts = pd.Timestamp(end_date)
        df['hours_ago'] = ((end_date_ts - df['requested_datetime']).dt.total_seconds() / 3600).round(1)
        
        # Handle potential missing columns and values
        # First, log the actual columns we have
        logging.info(f"Actual columns in response: {df.columns.tolist()}")
        
        # Add missing columns with default values if they don't exist
        required_columns = [
            'neighborhoods_sffind_boundaries', 'supervisor_district', 
            'service_subtype', 'service_details', 'source', 'service_name',
            'agency_responsible'
        ]
        
        for col in required_columns:
            if col not in df.columns:
                logging.warning(f"Column '{col}' not found in response, adding with default values")
                df[col] = 'Not Available'
        
        # Now fill missing values in existing columns
        df['neighborhoods_sffind_boundaries'] = df['neighborhoods_sffind_boundaries'].fillna('N/A')
        df['supervisor_district'] = df['supervisor_district'].fillna('N/A')
        df['service_subtype'] = df['service_subtype'].fillna('') # Use empty string if preferred
        df['service_details'] = df['service_details'].fillna('')
        df['source'] = df['source'].fillna('N/A')
        df['service_name'] = df['service_name'].fillna('N/A')
        df['agency_responsible'] = df['agency_responsible'].fillna('N/A')
        
        # For encampment reports specifically, use a default value if service_details is empty
        encampment_mask = (df['service_name'] == 'Encampment') | (df['service_name'] == 'Encampments')
        df.loc[encampment_mask & df['service_details'].isin(['', None, 'Not Available']), 'service_details'] = 'Encampment reported'
        
        # Format service_details and service_subtype:
        # 1. Replace underscores with spaces
        # 2. Capitalize only the first letter of the string (sentence case)
        df['service_details'] = df['service_details'].str.replace('_', ' ').apply(lambda x: x.capitalize() if isinstance(x, str) and x else x)
        df['service_subtype'] = df['service_subtype'].str.replace('_', ' ').apply(lambda x: x.capitalize() if isinstance(x, str) and x else x)
        
        # Format neighborhood with title case (proper capitalization)
        df['neighborhoods_sffind_boundaries'] = df['neighborhoods_sffind_boundaries'].apply(
            lambda x: x.title() if isinstance(x, str) else x
        )
        
        # Format address with proper capitalization and simplification
        def format_address(addr):
            if not isinstance(addr, str):
                return addr
                
            # Special handling for address abbreviations
            common_abbr = {'St': 'ST', 'Ave': 'AVE', 'Blvd': 'BLVD', 'Rd': 'RD', 'Dr': 'DR', 
                          'Ln': 'LN', 'Ct': 'CT', 'Pl': 'PL', 'Hwy': 'HWY'}
            
            # Get only the first part (street address) - everything before the first comma
            parts = addr.split(',')
            street_address = parts[0].strip() if parts else addr
            
            # Title case the street address
            street_address = street_address.title()
            
            # Fix abbreviations in street address
            for abbr, upper in common_abbr.items():
                street_address = street_address.replace(f" {abbr}", f" {upper}")
                street_address = street_address.replace(f" {abbr}.", f" {upper}")
            
            # Return only the street address part
            return street_address
            
        df['address'] = df['address'].apply(format_address)
        
        # Create final DataFrame with specific columns
        final_df = pd.DataFrame({
            'lat': df['lat'].astype(float),
            'long': df['long'].astype(float),
            'status': df['status_description'],
            'address': df['address'],
            'reported_datetime': df['reported_datetime'],
            'hours_ago': df['hours_ago'],
            'neighborhood': df['neighborhoods_sffind_boundaries'],
            'district': df['supervisor_district'],
            'service_name': df['service_name'],
            'service_subtype': df['service_subtype'],
            'service_details': df['service_details'],
            'source': df['source'],
            'agency_responsible': df['agency_responsible']
        })
        
        # Ensure the DataFrame has the correct column order (optional but good practice)
        final_df = final_df[required_cols]
        
        # Log the first few rows to verify format
        logging.info(f"Sample of final data:\n{final_df.head().to_string()}")
        
    logging.info(f"Retrieved total of {len(final_df)} locations from DataSF")
    return final_df, end_date

def update_datawrapper_map(chart_id, data, config, latest_date):
    """Update a Datawrapper map with new location data"""
    try:
        logger.info(f"Updating Datawrapper map {chart_id}")
        
        # Verify data format before sending
        if not all(col in data.columns for col in ['lat', 'long', 'status']):
            raise ValueError(f"Missing required columns. Found: {data.columns.tolist()}")
        
        # Create a new DataFrame with Datawrapper's expected column names
        dw_data = pd.DataFrame({
            'latitude': pd.to_numeric(data['lat'], errors='coerce'),
            'longitude': pd.to_numeric(data['long'], errors='coerce'),
            'status': data['status'],
            'address': data['address'],
            'reported_datetime': data['reported_datetime'],
            'hours_ago': data['hours_ago'],
            'neighborhood': data['neighborhood'],
            'district': data['district'],
            'service_name': data['service_name'],
            'service_subtype': data['service_subtype'],
            'service_details': data['service_details'],
            'source': data['source'],
            'agency_responsible': data['agency_responsible']
        })
        
        # Drop any rows with invalid lat/long
        dw_data = dw_data.dropna(subset=['latitude', 'longitude'])
        
        # FIRST: Fetch current chart metadata to preserve custom settings
        current_chart = dw.get_chart(chart_id)
        current_metadata = current_chart.get('metadata', {})
        
        # Get current visualization settings (especially preserving status-based colors)
        current_viz_settings = current_metadata.get('visualize', {})
        current_color_settings = current_viz_settings.get('color', {})
        
        # Format date for display - Use the actual query date (one day before latest_date)
        query_date = (latest_date - timedelta(days=1)).strftime("%B %d, %Y")
        
        # Start with essential metadata we always want to update
        metadata = {
            "describe": {
                "source-name": "DataSF",
                "source-url": "https://datasf.org/opendata/",
                "intro": f"Showing {len(dw_data):,} reports from {query_date}.",
                "byline": "San Francisco Examiner",
                # Use the base title without "Past 4 Weeks" or dates
                "title": config['title'].split(" - ")[0].strip()
            }
        }
        
        # Preserve visualization settings from current chart metadata
        # But only if they exist - otherwise use our default settings
        if current_viz_settings:
            metadata["visualize"] = current_viz_settings
            
            # Update specific date-related text while preserving other settings
            if "intro" in metadata["describe"]:
                metadata["describe"]["intro"] = f"Showing {len(dw_data):,} reports from {query_date}."
            
            # Ensure we're using the right mapping settings
            if "mapping" not in metadata:
                metadata["mapping"] = {
                    "latitude": "latitude",
                    "longitude": "longitude",
                    "color": "status"
                }
        else:
            # Default visualization settings if none exist yet
            metadata["visualize"] = {
                "map": {
                    "type": "points"
                },
                "general": {
                    "height": 600,
                    "miniMap": True,
                    "zoomButtons": True,
                    "scrollWheelZoom": True
                },
                "zoom": {
                    "min": 11,
                    "max": 18,
                    "default": 12
                },
                "bounds": {
                    "lat1": 37.71,
                    "lat2": 37.84,
                    "lon1": -122.51,
                    "lon2": -122.36
                },
                "color": {
                    "column": "status",
                    "palette": {
                        "type": "categorical",
                        "colors": {
                            "Open": "#ff4444",
                            "Closed": "#44ff44",
                            "In Progress": "#ffaa44",
                            "Duplicate": "#aaaaaa",
                            "other": "#888888"
                        }
                    }
                },
                "basemap": "usa-sanfran-analysis-neighborhood",
                "legends": {
                    "color": {
                        "size": 170,
                        "enabled": True,
                        "position": "above",
                        "orientation": "horizontal"
                    }
                }
            }
            metadata["mapping"] = {
                "latitude": "latitude",
                "longitude": "longitude",
                "color": "status"
            }
        
        # Update the chart metadata (preserving custom settings)
        dw.update_chart(chart_id, metadata=metadata)
        logger.info(f"Updated map metadata for {chart_id} (preserving custom settings)")

        # Update the data using direct API call with proper encoding
        api_token = DATAWRAPPER_API_KEY
        csv_content = dw_data.to_csv(index=False)
        
        response = requests.put(
            f"https://api.datawrapper.de/v3/charts/{chart_id}/data",
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "text/csv; charset=utf-8"
            },
            data=csv_content.encode('utf-8')
        )
        
        if response.status_code != 204:
            logger.error(f"Error uploading data: {response.status_code} {response.text}")
            raise Exception(f"Failed to upload data: {response.status_code}")
        logger.info(f"Uploaded data columns for {chart_id} via API")

        # Publish map
        dw.publish_chart(chart_id)
        
        map_info = dw.get_chart(chart_id)
        published_url = map_info.get("publicUrl", "Unknown URL")
        
        logger.info(f"Map published successfully: {published_url}")
        return published_url
    
    except Exception as e:
        logger.error(f"Error updating Datawrapper map: {e}")
        raise

def save_map_template(source_chart_id, template_file="map_template.json"):
    """
    Save the current visualization settings from a working map to a template file
    """
    try:
        # Get current chart settings
        current_chart = dw.get_chart(source_chart_id)
        current_metadata = current_chart.get('metadata', {})
        
        # Extract the important visualization settings
        template = {
            "visualize": current_metadata.get('visualize', {}),
            "mapping": current_metadata.get('mapping', {}),
            "axes": current_metadata.get('axes', {})
        }
        
        # Save to file
        with open(template_file, 'w') as f:
            json.dump(template, f, indent=2)
            
        logger.info(f"Saved map template to {template_file} from chart {source_chart_id}")
        return template
        
    except Exception as e:
        logger.error(f"Error saving map template: {e}")
        raise

def apply_map_template(chart_id, template_file="map_template.json", title=None, intro=None, tooltip_template=None):
    """
    Apply saved template settings to another map
    """
    try:
        # Load template settings
        if isinstance(template_file, dict):
            # Template is already loaded as dict
            template = template_file
        else:
            # Load template from file
            with open(template_file, 'r') as f:
                template = json.load(f)
        
        # Get current chart metadata
        current_chart = dw.get_chart(chart_id)
        current_metadata = current_chart.get('metadata', {})
        
        # Create new metadata with template settings
        metadata = {
            "visualize": template.get('visualize', {}),
            "mapping": template.get('mapping', {}),
            "axes": template.get('axes', {})
        }
        
        # Update describe section with current values
        metadata["describe"] = current_metadata.get('describe', {})
        
        # Update specific fields if provided
        if title:
            metadata["describe"]["title"] = title
        if intro:
            metadata["describe"]["intro"] = intro
        
        # Apply custom tooltip template if provided
        if tooltip_template:
            # Force create visualize.tooltip if it doesn't exist
            if "tooltip" not in metadata["visualize"]:
                metadata["visualize"]["tooltip"] = {}
            
            # Set the tooltip template with full HTML
            metadata["visualize"]["tooltip"] = {
                "body": tooltip_template,
                "html": True,
                "style": "custom",
                "sticky": True,
                "enabled": True
            }
            
            logger.info(f"Applied custom tooltip template to chart {chart_id}")
            
        # Apply the settings
        dw.update_chart(chart_id, metadata=metadata)
        logger.info(f"Applied template settings to chart {chart_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error applying map template: {e}")
        raise

def process_and_update_map(config_name, template_file=None):
    """Process data and update a specific map"""
    config = MAP_CONFIGS[config_name]
    if not config["chart_id"]:
        logger.warning(f"Chart ID not configured for {config_name}")
        return
    
    try:
        # Get data
        data, latest_date = get_map_data_from_datasf(config)
        
        # Log data columns to help debug
        logger.info(f"{config_name} data columns: {data.columns.tolist()}")
        logger.info(f"{config_name} has {len(data)} records")
        
        if len(data) == 0:
            logger.warning(f"No data available for {config_name}, skipping update")
            return
        
        # Update map
        update_datawrapper_map(
            chart_id=config["chart_id"],
            data=data,
            config=config,
            latest_date=latest_date
        )
        
        # Apply template settings if provided and this is not the source map
        if template_file and config["chart_id"] != "nB5JE":  # Assuming nB5JE is the source
            # Use the latest_date as the query date (the most recent complete day)
            query_date = latest_date.strftime("%B %d, %Y")
            
            # Get the specific tooltip template for this map
            tooltip_template = config.get('tooltip_template')
            
            # Log the tooltip template being used
            logger.info(f"Applying tooltip template for {config_name}: {tooltip_template[:50]}...")
            
            # Apply template with the map-specific tooltip
            apply_map_template(
                chart_id=config["chart_id"],
                template_file=template_file,
                # Use the base title without "Past 4 Weeks" or dates
                title=config['title'].split(" - ")[0].strip(),
                intro=f"Showing {len(data):,} reports from {query_date}.",
                tooltip_template=tooltip_template
            )
        
        logger.info(f"Successfully updated {config_name} map")
    
    except Exception as e:
        import traceback
        logger.error(f"Failed to update {config_name} map: {e}")
        logger.error(traceback.format_exc())

def update_all_maps():
    """Update all configured maps"""
    logger.info("Starting scheduled update of all maps")
    
    # First, save template from the working map
    template = None
    try:
        template = save_map_template("nB5JE", "map_template.json")
        logger.info("Saved current map settings as template")
    except Exception as e:
        logger.warning(f"Could not save template, will use default settings: {e}")
    
    # Then update all maps using the template
    for map_name in MAP_CONFIGS:
        process_and_update_map(map_name, template)
        
    logger.info("Completed update of all maps")

if __name__ == "__main__":
    update_all_maps() 