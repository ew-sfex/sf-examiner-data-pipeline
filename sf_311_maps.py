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


def format_date_ap_style(dt):
    """
    Format a datetime object in AP Style (date only).
    - Abbreviated months with periods (except March, April, May, June, July)
    - No leading zeros on days
    - Format: "Jan. 2, 2025" or "March 15, 2025"
    """
    ap_months = {
        1: "Jan.", 2: "Feb.", 3: "March", 4: "April", 5: "May", 6: "June",
        7: "July", 8: "Aug.", 9: "Sept.", 10: "Oct.", 11: "Nov.", 12: "Dec."
    }
    month = ap_months[dt.month]
    day = dt.day
    year = dt.year
    return f"{month} {day}, {year}"


def format_datetime_ap_style(dt):
    """
    Format a datetime object in AP Style (date and time).
    - AP Style time: lowercase a.m./p.m., no leading zeros, noon/midnight for 12:00
    - Format: "Jan. 2, 2025, 1:38 p.m." or "March 15, 2025, noon"
    """
    ap_months = {
        1: "Jan.", 2: "Feb.", 3: "March", 4: "April", 5: "May", 6: "June",
        7: "July", 8: "Aug.", 9: "Sept.", 10: "Oct.", 11: "Nov.", 12: "Dec."
    }
    
    # Date part
    month = ap_months[dt.month]
    day = dt.day
    year = dt.year
    
    # Time part - AP Style
    hour = dt.hour
    minute = dt.minute
    
    if hour == 0 and minute == 0:
        time_str = "midnight"
    elif hour == 12 and minute == 0:
        time_str = "noon"
    else:
        if hour == 0:
            hour_12 = 12
            ampm = "a.m."
        elif hour < 12:
            hour_12 = hour
            ampm = "a.m."
        elif hour == 12:
            hour_12 = 12
            ampm = "p.m."
        else:
            hour_12 = hour - 12
            ampm = "p.m."
        
        if minute == 0:
            time_str = f"{hour_12} {ampm}"
        else:
            time_str = f"{hour_12}:{minute:02d} {ampm}"
    
    return f"{month} {day}, {year}, {time_str}"

# API Credentials
DATAWRAPPER_API_KEY = os.environ.get("DATAWRAPPER_API_KEY", "BVIPEwcGz4XlfLDxrzzpio0Fu9OBlgTSE8pYKNWxKF8lzxz89BHMI3zT1VWQrF2Y")
DATASF_APP_TOKEN = os.environ.get("DATASF_APP_TOKEN", "xdboBmIBQtjISZqIRYDWjKyxY")

# Initialize API clients
dw = datawrapper.Datawrapper(access_token=DATAWRAPPER_API_KEY)
client = Socrata("data.sfgov.org", DATASF_APP_TOKEN)

# Configuration for 311 maps
# NOTE: Titles are NOT set by code - edit them directly in Datawrapper
MAP_CONFIGS = {
    "street_cleaning_map": {
        "dataset_id": "vw6y-z8j6",
        "chart_id": "nB5JE",
        "service_filter": "service_name = 'Street and Sidewalk Cleaning'",
        "marker_color": "#cf4236",  # SF Examiner red
        "description_template": "These are the {count} requests San Franciscans made for street and sidewalk cleaning to 311 on {date}. The City estimates that responses can take between 2 hours and 21 days, depending on the type of trash.",
        "tooltip_template": """<div style="font-family:Arial,sans-serif;line-height:1.3;">
<b>{{ service_details }}</b><br>
<b>Location:</b><br>{{ PROPER(address) }}<br>
<b>Neighborhood:</b><br>{{ PROPER(neighborhood) }}<br>
<b>Status:</b> <span style="color:{{ status == 'Closed' ? '#4a4' : '#d44' }}">{{ status }}</span><br>
<b>Reported:</b> {{ reported_datetime }}
</div>"""
    },
    "graffiti_map": {
        "dataset_id": "vw6y-z8j6",
        "chart_id": "0xtQT",
        "service_filter": "service_name LIKE 'Graffiti%'",
        "marker_color": "#ffd74c",  # SF Examiner yellow
        "description_template": "These are the {count} instances of graffiti in San Francisco requested for removal by 311 on {date}. The City estimates that most graffiti takes between two and three days to remove, while its presence on parking or traffic signs can take as many as 20 days.",
        "tooltip_template": """<div style="font-family:Arial,sans-serif;line-height:1.3;">
<b>{{ service_details }}</b><br>
<b>Location:</b><br>{{ PROPER(address) }}<br>
<b>Neighborhood:</b><br>{{ PROPER(neighborhood) }}<br>
<b>Status:</b> <span style="color:{{ status == 'Closed' ? '#4a4' : '#d44' }}">{{ status }}</span><br>
<b>Reported:</b> {{ reported_datetime }}
</div>"""
    },
    "encampments_map": {
        "dataset_id": "vw6y-z8j6",
        "chart_id": "os0dX",
        "service_filter": "(service_name = 'Encampment' OR service_name = 'Encampments')",
        "marker_color": "#7e883f",  # SF Examiner green
        "description_template": "These are the {count} homeless encampments reported to San Francisco 311 on {date}.",
        "tooltip_template": """<div style="font-family:Arial,sans-serif;line-height:1.3;">
<b>Encampment Report</b><br>
<b>Location:</b><br>{{ PROPER(address) }}<br>
<b>Neighborhood:</b><br>{{ PROPER(neighborhood) }}<br>
<b>Status:</b> <span style="color:{{ status == 'Closed' ? '#4a4' : '#d44' }}">{{ status }}</span><br>
<b>Reported:</b> {{ reported_datetime }}
</div>"""
    },
    "tree_maintenance_map": {
        "dataset_id": "vw6y-z8j6",
        "chart_id": "9JMgr",
        "service_filter": "service_name = 'Tree Maintenance'",
        "marker_color": "#80d0d8",  # SF Examiner blue
        "description_template": "These are the {count} reports of fallen or damaged trees made to San Francisco 311 on {date}. The City says responses can take up to 90 days, depending upon the issue.",
        "tooltip_template": """<div style="font-family:Arial,sans-serif;line-height:1.3;">
<b>{{ service_subtype }}</b><br>
<b>Location:</b><br>{{ PROPER(address) }}<br>
<b>Neighborhood:</b><br>{{ PROPER(neighborhood) }}<br>
<b>Status:</b> <span style="color:{{ status == 'Closed' ? '#4a4' : '#d44' }}">{{ status }}</span><br>
<b>Reported:</b> {{ reported_datetime }}
</div>"""
    },
    "abandoned_vehicles_map": {
        "dataset_id": "vw6y-z8j6",
        "chart_id": "V5s4q",
        "service_filter": "(service_subtype LIKE '%abandoned_vehicle%' OR service_name = 'Abandoned Vehicle')",
        "marker_color": "#e3cbac",  # SF Examiner tan
        "description_template": "These are the {count} reports to 311 of abandoned vehicles parked for more than 72 hours in a single spot on {date}. The City says responses can take between two and five business days.",
        "tooltip_template": """<div style="font-family:Arial,sans-serif;line-height:1.3;">
<b>Abandoned Vehicle</b><br>
<b>Location:</b><br>{{ PROPER(address) }}<br>
<b>Neighborhood:</b><br>{{ PROPER(neighborhood) }}<br>
<b>Status:</b> <span style="color:{{ status == 'Closed' ? '#4a4' : '#d44' }}">{{ status }}</span><br>
<b>Reported:</b> {{ reported_datetime }}
</div>"""
    },
    "sewage_backups_map": {
        "dataset_id": "vw6y-z8j6",
        "chart_id": "Lu3TG",
        "service_filter": "service_name = 'Sewer' AND service_subtype = 'sewage_back-up_discharge'",
        "marker_color": "#a57bc1",  # Purple for sewage issues
        "description_template": "These are the {count} reports of sewage backup filed with San Francisco 311 on {date}. The City estimates it can respond to most reports within one business day.",
        "tooltip_template": """<div style="font-family:Arial,sans-serif;line-height:1.3;">
<b>Sewage Backup</b><br>
<b>Location:</b><br>{{ PROPER(address) }}<br>
<b>Neighborhood:</b><br>{{ PROPER(neighborhood) }}<br>
<b>Status:</b> <span style="color:{{ status == 'Closed' ? '#4a4' : '#d44' }}">{{ status }}</span><br>
<b>Reported:</b> {{ reported_datetime }}
</div>"""
    },
    "street_sidewalk_defects_map": {
        "dataset_id": "vw6y-z8j6",
        "chart_id": "acPZT",
        "service_filter": "(service_name = 'Sidewalk and Curb' OR service_name = 'Street Defect')",
        "marker_color": "#8B4513",  # Saddle brown for infrastructure issues
        "description_template": "These are the {count} sidewalk and street defects — such as cracks and raising by tree roots — reported to San Francisco 311 on {date}. The City estimates inspections are conducted within three business days.",
        "tooltip_template": """<div style="font-family:Arial,sans-serif;line-height:1.3;">
<b>{{ service_subtype }}</b><br>
<b>Location:</b><br>{{ PROPER(address) }}<br>
<b>Neighborhood:</b><br>{{ PROPER(neighborhood) }}<br>
<b>Status:</b> <span style="color:{{ status == 'Closed' ? '#4a4' : '#d44' }}">{{ status }}</span><br>
<b>Reported:</b> {{ reported_datetime }}
</div>"""
    },
    "human_waste_map": {
        "dataset_id": "vw6y-z8j6",
        "chart_id": "XDoKW",
        "service_filter": "service_name = 'Street and Sidewalk Cleaning' AND service_details = 'human_waste_or_urine'",
        "marker_color": "#8f4e35",  # Rust brown color
        "description_template": "These are the {count} human waste reports San Franciscans made to 311 on {date}.",
        "tooltip_template": """<div style="font-family:Arial,sans-serif;line-height:1.3;">
<b>Human Waste Report</b><br>
<b>Location:</b><br>{{ PROPER(address) }}<br>
<b>Neighborhood:</b><br>{{ PROPER(neighborhood) }}<br>
<b>Status:</b> <span style="color:{{ status == 'Closed' ? '#4a4' : '#d44' }}">{{ status }}</span><br>
<b>Reported:</b> {{ reported_datetime }}
</div>"""
    },
    "noise_complaints_map": {
        "dataset_id": "vw6y-z8j6",
        "chart_id": "AJzUh",
        "service_filter": "service_name = 'Noise' AND agency_responsible IN ('Noise Report', 'Entertainment Commission', 'DPH Environmental Health - Noise')",
        "marker_color": "#9932cc",  # Dark orchid purple
        "description_template": "These are the {count} noise complaints reported to San Francisco 311 on {date}. The City allows for human- and animal-created noises unless they fall between 10 p.m. and 7 a.m. or become unreasonable. Some noise complaints are recorded only for data and not acted upon, according to San Francisco 311.",
        "tooltip_template": """<div style="font-family:Arial,sans-serif;line-height:1.3;">
<b>{{ service_subtype }}</b><br>
<b>Location:</b><br>{{ PROPER(address) }}<br>
<b>Neighborhood:</b><br>{{ PROPER(neighborhood) }}<br>
<b>Status:</b> <span style="color:{{ status == 'Closed' ? '#4a4' : '#d44' }}">{{ status }}</span><br>
<b>Reported:</b> {{ reported_datetime }}
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
        
        # Prepare columns for the final dataset - use AP Style datetime
        df['reported_datetime'] = df['requested_datetime'].apply(format_datetime_ap_style)
        end_date_ts = pd.Timestamp(end_date)
        # Keep hours_ago for data but don't display in tooltip
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
        
        # Format date for display in AP Style - Use the latest_date (most recent complete day)
        query_date_ap = format_date_ap_style(latest_date)
        current_date_ap = format_date_ap_style(datetime.now())
        
        # Build description from template
        description_template = config.get('description_template', "Showing {count} reports from {date}.")
        description = description_template.format(count=f"{len(dw_data):,}", date=query_date_ap)
        
        # Start with essential metadata we always want to update
        # NOTE: We do NOT set the title here - titles are managed directly in Datawrapper
        metadata = {
            "describe": {
                "source-name": "DataSF",
                "source-url": "https://datasf.org/opendata/",
                "intro": description,
                "byline": "San Francisco Examiner"
            },
            "annotate": {
                "notes": f"Data updated on {current_date_ap}"
            }
        }
        
        # Preserve visualization settings from current chart metadata
        # But only if they exist - otherwise use our default settings
        if current_viz_settings:
            metadata["visualize"] = current_viz_settings
            
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
        
        # Apply custom tooltip template from config (overrides preserved settings)
        tooltip_template = config.get('tooltip_template')
        if tooltip_template:
            if "visualize" not in metadata:
                metadata["visualize"] = {}
            metadata["visualize"]["tooltip"] = {
                "title": "",  # Clear the title field - we include title in body HTML
                "body": tooltip_template,
                "html": True,
                "style": "custom",
                "sticky": True,
                "enabled": True
            }
            logger.info(f"Applied custom tooltip template to {chart_id}")
        
        # Update chart metadata (title is NOT set - manage titles directly in Datawrapper)
        dw.update_chart(chart_id, metadata=metadata)
        logger.info(f"Updated map metadata for {chart_id} (preserving custom settings, title unchanged)")

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

def apply_map_template(chart_id, template_file="map_template.json", intro=None, tooltip_template=None):
    """
    Apply saved template settings to another map.
    NOTE: Titles are NOT set here - manage titles directly in Datawrapper.
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
        
        # Update describe section with current values (preserves existing title)
        metadata["describe"] = current_metadata.get('describe', {})
        
        # Update intro/description if provided
        if intro:
            metadata["describe"]["intro"] = intro
        
        # Apply custom tooltip template if provided
        if tooltip_template:
            # Force create visualize.tooltip if it doesn't exist
            if "tooltip" not in metadata["visualize"]:
                metadata["visualize"]["tooltip"] = {}
            
            # Set the tooltip template with full HTML
            metadata["visualize"]["tooltip"] = {
                "title": "",  # Clear the title field - we include title in body HTML
                "body": tooltip_template,
                "html": True,
                "style": "custom",
                "sticky": True,
                "enabled": True
            }
            
            logger.info(f"Applied custom tooltip template to chart {chart_id}")
            
        # Apply the settings (title is NOT updated)
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
            # Use AP Style date formatting
            query_date_ap = format_date_ap_style(latest_date)
            
            # Build description from template
            description_template = config.get('description_template', "Showing {count} reports from {date}.")
            description = description_template.format(count=f"{len(data):,}", date=query_date_ap)
            
            # Get the specific tooltip template for this map
            tooltip_template = config.get('tooltip_template')
            
            # Log the tooltip template being used
            logger.info(f"Applying tooltip template for {config_name}: {tooltip_template[:50]}...")
            
            # Apply template with the map-specific tooltip (title is NOT set)
            apply_map_template(
                chart_id=config["chart_id"],
                template_file=template_file,
                intro=description,
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