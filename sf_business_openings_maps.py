#!/usr/bin/env python3
# DataSF to Datawrapper Automation Pipeline - Business Openings Maps
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
        logging.FileHandler("sf_business_openings_maps.log"),
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

# Configuration for Business Openings maps
MAP_CONFIGS = {
    "business_openings_map": {
        "dataset_id": "g8m3-pdis",  # Registered Business Locations dataset
        "chart_id": "TWHZY",  # Business Openings map
        "business_filter": "location_start_date IS NOT NULL AND (city = 'San Francisco' OR city = 'San Fran' OR city = 'SF' OR city = 'San Francisceo' OR city = 'San Franciscce' OR city = 'San Francicsco' OR city = 'Santo Francisco')",
        "date_field": "location_start_date", 
        "title": "Recent business activity",
        "description": "New business openings and business relocations",
        "marker_color": "#80d0d8",  # SF Examiner blue
        "tooltip_template": """<div style="font-family:Arial,sans-serif;line-height:1.3;">
<b>{{ activity_type }}</b><br>
<b>Business:</b> {{ PROPER(dba_name) }}<br>
<b>Address:</b> {{ PROPER(address) }}<br>
<b>Type:</b> {{ PROPER(business_type) }}<br>
<b>Started:</b> {{ opened_datetime }}<br>
<b>Neighborhood:</b> {{ PROPER(neighborhood) }}
</div>"""
    }
}

def get_map_data_from_datasf(chart_config):
    """Fetch business opening location data from DataSF API for the last 7 days."""
    
    # First, find the latest date in the dataset for the specific date field
    date_field = chart_config['date_field']
    latest_date_query = f"""
    SELECT 
        {date_field}
    WHERE 
        {chart_config['business_filter']}
        AND {date_field} IS NOT NULL
    ORDER BY {date_field} DESC
    LIMIT 1
    """
    
    try:
        latest_result = client.get(chart_config['dataset_id'], query=latest_date_query)
        if not latest_result:
            raise ValueError("No data found in dataset")
            
        latest_date = datetime.fromisoformat(latest_result[0][date_field].split('T')[0])
        
        # Reject future dates (data errors) - use today instead
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if latest_date > today:
            logging.warning(f"Latest date {latest_date.strftime('%Y-%m-%d')} is in the future; using today instead")
            latest_date = today
        
        logging.info(f"Latest data available is from: {latest_date.strftime('%Y-%m-%d')}")
        
        # For business openings, we want data from the last 7 days (like 911 maps)
        end_date = latest_date
        start_date = end_date - timedelta(days=7)
        
    except Exception as e:
        logging.error(f"Error finding latest date, falling back to default date range: {str(e)}")
        # Fallback: use previous 7 days from current date
        end_date = datetime.now().replace(hour=23, minute=59, second=59)
        start_date = end_date - timedelta(days=7)
    
    # Format dates for query
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    logging.info(f"Querying data from {start_date_str} to {end_date_str}")
    
    # Base query - get business activity data (openings + relocations)
    base_query = f"""
    SELECT 
        certificate_number,
        dba_name,
        ownership_name,
        {date_field},
        dba_start_date,
        full_business_address,
        naic_code_description,
        neighborhoods_analysis_boundaries,
        supervisor_district,
        location
    WHERE 
        {chart_config['business_filter']}
        AND {date_field} >= '{start_date_str}'
        AND {date_field} <= '{end_date_str}'
        AND location IS NOT NULL
    ORDER BY {date_field} DESC
    """
    
    # Log the full query for debugging
    logging.info(f"Full query being executed:\n{base_query}")
    
    offset = 0
    limit = 1000
    all_results = []
    
    # Try a test query first to verify data exists
    test_query = f"""
    SELECT COUNT(*) as count
    WHERE {chart_config['business_filter']}
        AND {date_field} >= '{start_date_str}'
        AND {date_field} <= '{end_date_str}'
        AND location IS NOT NULL
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
        logging.warning(f"No data found for business filter: {chart_config['business_filter']}")
        logging.warning("Trying query without time filter to check if businesses exist...")
        test_query = f"SELECT COUNT(*) as count WHERE {chart_config['business_filter']} AND location IS NOT NULL"
        try:
            count_result = client.get(chart_config['dataset_id'], query=test_query)
            total_count = int(count_result[0]['count']) if count_result else 0
            logging.info(f"Total records for businesses (all time): {total_count}")
        except Exception as e:
            logging.error(f"Error checking business existence: {str(e)}")
    
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
        'lat', 'long', 'dba_name', 'address', 'opened_datetime',
        'neighborhood', 'district', 'business_type', 'activity_type'
    ]
    final_df = pd.DataFrame(columns=required_cols)
    
    if not df.empty:
        # Extract latitude and longitude from location field
        if 'location' in df.columns:
            # Parse the location JSON field
            df['lat'] = df['location'].apply(lambda x: x['coordinates'][1] if isinstance(x, dict) and 'coordinates' in x else None)
            df['long'] = df['location'].apply(lambda x: x['coordinates'][0] if isinstance(x, dict) and 'coordinates' in x else None)
        else:
            df['lat'] = None
            df['long'] = None
        
        # Convert datetime
        if date_field in df.columns:
            df[date_field] = pd.to_datetime(df[date_field])
        if 'dba_start_date' in df.columns:
            df['dba_start_date'] = pd.to_datetime(df['dba_start_date'])
        
        # Create formatted datetime field
        df['opened_datetime'] = df[date_field].dt.strftime('%B %d, %Y')
        
        # Determine business activity type (new vs relocated)
        def determine_activity_type(row):
            if pd.isna(row['dba_start_date']) or pd.isna(row[date_field]):
                return 'Unknown'
            elif row['dba_start_date'].date() == row[date_field].date():
                return 'New Business'
            elif row['dba_start_date'] < row[date_field]:
                return 'Business Relocation'
            else:
                return 'Unknown'
        
        df['activity_type'] = df.apply(determine_activity_type, axis=1)
        
        # Handle potential missing columns and values
        logging.info(f"Actual columns in response: {df.columns.tolist()}")
        
        # Add missing columns with default values if they don't exist
        required_columns = [
            'neighborhoods_analysis_boundaries', 'supervisor_district', 
            'naic_code_description', 'dba_name', 'full_business_address'
        ]
        
        for col in required_columns:
            if col not in df.columns:
                logging.warning(f"Column '{col}' not found in response, adding with default values")
                df[col] = 'Not Available'
        
        # Fill missing values in existing columns
        df['neighborhoods_analysis_boundaries'] = df['neighborhoods_analysis_boundaries'].fillna('N/A')
        df['supervisor_district'] = df['supervisor_district'].fillna('N/A')
        df['naic_code_description'] = df['naic_code_description'].fillna('Unknown')
        df['dba_name'] = df['dba_name'].fillna('Unknown Business')
        df['full_business_address'] = df['full_business_address'].fillna('Address Unknown')
        
        # Format neighborhood with title case
        df['neighborhoods_analysis_boundaries'] = df['neighborhoods_analysis_boundaries'].apply(
            lambda x: x.title() if isinstance(x, str) else x
        )
        
        # Create final DataFrame with specific columns
        final_df = pd.DataFrame({
            'lat': pd.to_numeric(df['lat'], errors='coerce'),
            'long': pd.to_numeric(df['long'], errors='coerce'),
            'dba_name': df['dba_name'],
            'address': df['full_business_address'],
            'opened_datetime': df['opened_datetime'],
            'neighborhood': df['neighborhoods_analysis_boundaries'],
            'district': df['supervisor_district'],
            'business_type': df['naic_code_description'],
            'activity_type': df['activity_type']
        })
        
        # Drop any rows with invalid lat/long
        final_df = final_df.dropna(subset=['lat', 'long'])
        
        # Ensure the DataFrame has the correct column order
        final_df = final_df[required_cols]
        
        # Log the first few rows to verify format
        logging.info(f"Sample of final data:\n{final_df.head().to_string()}")
        
    logging.info(f"Retrieved total of {len(final_df)} business openings from DataSF")
    return final_df, end_date

def update_datawrapper_map(chart_id, data, config, latest_date):
    """Update a Datawrapper map with new business opening data"""
    try:
        logger.info(f"Updating Datawrapper map {chart_id}")
        
        # Verify data format before sending
        if not all(col in data.columns for col in ['lat', 'long']):
            raise ValueError(f"Missing required columns. Found: {data.columns.tolist()}")
        
        # Create a new DataFrame with Datawrapper's expected column names
        dw_data = pd.DataFrame({
            'latitude': pd.to_numeric(data['lat'], errors='coerce'),
            'longitude': pd.to_numeric(data['long'], errors='coerce'),
            'dba_name': data['dba_name'],
            'address': data['address'],
            'opened_datetime': data['opened_datetime'],
            'neighborhood': data['neighborhood'],
            'district': data['district'],
            'business_type': data['business_type'],
            'activity_type': data['activity_type']
        })
        
        # Drop any rows with invalid lat/long
        dw_data = dw_data.dropna(subset=['latitude', 'longitude'])
        
        # FIRST: Fetch current chart metadata to preserve custom settings
        current_chart = dw.get_chart(chart_id)
        current_metadata = current_chart.get('metadata', {})
        
        # Get current visualization settings
        current_viz_settings = current_metadata.get('visualize', {})
        
        # Format date for display (7-day range like 911 maps)
        query_date_range = f"{(latest_date - timedelta(days=7)).strftime('%B %d')} - {latest_date.strftime('%B %d, %Y')}"
        current_date = datetime.now().strftime("%B %d, %Y")
        
        # Start with essential metadata we always want to update
        metadata = {
            "describe": {
                "source-name": "DataSF - Registered Business Locations",
                "source-url": "https://data.sfgov.org/Economy-and-Community/Registered-Business-Locations-San-Francisco/g8m3-pdis",
                "intro": f"Showing {len(dw_data):,} new businesses from {query_date_range}.",
                "byline": "San Francisco Examiner",
                "title": config['title']
            },
            "annotate": {
                "notes": f"Data updated on {current_date}"
            }
        }
        
        # Preserve visualization settings from current chart metadata
        # But only if they exist - otherwise use our default settings
        if current_viz_settings:
            metadata["visualize"] = current_viz_settings
            
            # Update specific date-related text while preserving other settings
            if "intro" in metadata["describe"]:
                metadata["describe"]["intro"] = f"Showing {len(dw_data):,} new businesses from {query_date_range}."
            
            # Ensure we're using the right mapping settings with color coding
            if "mapping" not in metadata:
                metadata["mapping"] = {
                    "latitude": "latitude",
                    "longitude": "longitude",
                    "color": "activity_type"
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
                    "column": "activity_type",
                    "palette": {
                        "type": "categorical",
                        "colors": {
                            "New Business": "#cf4236",  # Red for new businesses
                            "Business Relocation": "#80d0d8",  # Blue for relocations
                            "Unknown": "#888888"
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
                "color": "activity_type"
            }
        
        # Update the chart metadata (preserving custom settings)
        desired_title = metadata['describe']['title']
        dw.update_chart(chart_id, title=desired_title, metadata=metadata)
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

def save_map_template(source_chart_id, template_file="business_openings_map_template.json"):
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

def apply_map_template(chart_id, template_file="business_openings_map_template.json", title=None, intro=None, tooltip_template=None):
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
        
        # Apply template settings if provided
        if template_file:
            # Use the 7-day date range for display (like 911 maps)
            query_date_range = f"{(latest_date - timedelta(days=7)).strftime('%B %d')} - {latest_date.strftime('%B %d, %Y')}"
            
            # Get the specific tooltip template for this map
            tooltip_template = config.get('tooltip_template')
            
            # Log the tooltip template being used
            logger.info(f"Applying tooltip template for {config_name}: {tooltip_template[:50]}...")
            
            # Apply template with the map-specific tooltip
            apply_map_template(
                chart_id=config["chart_id"],
                template_file=template_file,
                title=config['title'],
                intro=f"Showing {len(data):,} new businesses from {query_date_range}.",
                tooltip_template=tooltip_template
            )
        
        logger.info(f"Successfully updated {config_name} map")
    
    except Exception as e:
        import traceback
        logger.error(f"Failed to update {config_name} map: {e}")
        logger.error(traceback.format_exc())

def update_all_maps():
    """Update all configured maps"""
    logger.info("Starting scheduled update of all business openings maps")
    
    # First, save template from the working map (when configured)
    template = None
    template_file = "business_openings_map_template.json"
    
    # Check if any maps have valid chart IDs
    has_valid_chart = any(cfg["chart_id"] for cfg in MAP_CONFIGS.values())
    
    if has_valid_chart:
        # Try to save template from the first working map
        for map_name, config in MAP_CONFIGS.items():
            if config["chart_id"]:
                try:
                    template = save_map_template(config["chart_id"], template_file)
                    logger.info(f"Saved template from {map_name} chart ID {config['chart_id']}")
                    break
                except Exception as e:
                    logger.warning(f"Could not save template from {map_name}: {e}")
    
    # Then update all maps with valid chart IDs
    for map_name in MAP_CONFIGS:
        if MAP_CONFIGS[map_name]["chart_id"]:
            process_and_update_map(map_name, template)
        else:
            logger.warning(f"Skipping {map_name} - no chart ID configured")
    
    logger.info("Completed update of all business openings maps")

if __name__ == "__main__":
    # Check if any maps have chart IDs configured
    if any(cfg["chart_id"] for cfg in MAP_CONFIGS.values()):
        update_all_maps()
    else:
        logger.warning("No chart IDs configured. Please create maps in Datawrapper and update the chart_id values.")
        logger.info("To create a map:") 
        logger.info("1. Go to https://app.datawrapper.de/create")
        logger.info("2. Select 'Locator Map'")
        logger.info("3. Create a map with a few test points")
        logger.info("4. Get the chart ID from the URL (e.g., '1abc2' from https://app.datawrapper.de/map/1abc2)")
        logger.info("5. Update the chart_id in MAP_CONFIGS")
