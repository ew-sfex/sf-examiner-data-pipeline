#!/usr/bin/env python3
# DataSF to Datawrapper Automation Pipeline - 911 Call Maps
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
        logging.FileHandler("sf_911_maps.log"),
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

# Configuration for 911 maps
# Source dataset: https://data.sfgov.org/Public-Safety/Police-Department-Incident-Reports-2018-to-Present/wg3w-h783
MAP_CONFIGS = {
    "violent_crimes_map": {
        "dataset_id": "wg3w-h783", # Police Department Incident Reports 2018 to Present
        "chart_id": "TX5ff",  # Violent crimes map
        "incident_filter": "incident_category IN ('Homicide', 'Robbery', 'Assault', 'Sex Offense')",
        "title": "Violent Crime Incidents",
        "description": "Location of recent violent crime incidents",
        "marker_color": "#cf4236",  # SF Examiner red
        "tooltip_template": """<div style="font-family:Arial,sans-serif;line-height:1.3;">
<b>Violent Crime: {{ incident_category }}</b><br>
<b>Type:</b> {{ incident_subcategory }}<br>
<b>Location:</b><br>{{ PROPER(incident_address) }}<br>
<b>Neighborhood:</b><br>{{ PROPER(neighborhood) }}<br>
<b>Status:</b> {{ resolution }}<br>
<b>Reported:</b> {{ incident_datetime }}
</div>"""
    },
    "property_crimes_map": {
        "dataset_id": "wg3w-h783",
        "chart_id": "AbO6X",  # Property crimes map
        "incident_filter": "incident_category IN ('Burglary', 'Larceny Theft', 'Motor Vehicle Theft', 'Arson')",
        "title": "Property Crime Incidents",
        "description": "Location of recent property crime incidents",
        "marker_color": "#ffd74c",  # SF Examiner yellow
        "tooltip_template": """<div style="font-family:Arial,sans-serif;line-height:1.3;">
<b>Property Crime: {{ incident_category }}</b><br>
<b>Type:</b> {{ incident_subcategory }}<br>
<b>Location:</b><br>{{ PROPER(incident_address) }}<br>
<b>Neighborhood:</b><br>{{ PROPER(neighborhood) }}<br>
<b>Status:</b> {{ resolution }}<br>
<b>Reported:</b> {{ incident_datetime }}
</div>"""
    },
    "drug_offenses_map": {
        "dataset_id": "wg3w-h783",
        "chart_id": "h8x3T",  # Drug offenses map
        "incident_filter": "incident_category = 'Drug Offense'",
        "title": "Drug Offense Incidents",
        "description": "Location of recent drug offense incidents",
        "marker_color": "#7e883f",  # SF Examiner green
        "tooltip_template": """<div style="font-family:Arial,sans-serif;line-height:1.3;">
<b>Drug Offense</b><br>
<b>Type:</b> {{ incident_subcategory }}<br>
<b>Location:</b><br>{{ PROPER(incident_address) }}<br>
<b>Neighborhood:</b><br>{{ PROPER(neighborhood) }}<br>
<b>Status:</b> {{ resolution }}<br>
<b>Reported:</b> {{ incident_datetime }}
</div>"""
    },
    "vehicle_related_map": {
        "dataset_id": "wg3w-h783",
        "chart_id": "y8sSh",  # Vehicle-related incidents map
        "incident_filter": "incident_category IN ('Traffic Collision', 'Traffic Violation', 'Motor Vehicle Theft')",
        "title": "Vehicle-Related Incidents",
        "description": "Location of recent traffic collisions, violations, and vehicle thefts",
        "marker_color": "#80d0d8",  # SF Examiner blue
        "tooltip_template": """<div style="font-family:Arial,sans-serif;line-height:1.3;">
<b>Vehicle Incident: {{ incident_category }}</b><br>
<b>Type:</b> {{ incident_subcategory }}<br>
<b>Location:</b><br>{{ PROPER(incident_address) }}<br>
<b>Neighborhood:</b><br>{{ PROPER(neighborhood) }}<br>
<b>Status:</b> {{ resolution }}<br>
<b>Reported:</b> {{ incident_datetime }}
</div>"""
    },
    "firearms_map": {
        "dataset_id": "wg3w-h783",
        "chart_id": "YiMUb",  # Firearm-related incidents map
        "incident_filter": "(incident_category IN ('Weapons Carrying Etc', 'Weapons Offense') OR incident_subcategory IN ('Robbery - Armed with Gun', 'Assault - Gun', 'Assault with a Gun', 'Discharge of a Firearm', 'Illegal Discharge of a Firearm'))",
        "title": "Firearm-Related Incidents",
        "description": "Location of recent incidents involving firearms",
        "marker_color": "#e3cbac",  # SF Examiner tan
        "tooltip_template": """<div style="font-family:Arial,sans-serif;line-height:1.3;">
<b>Firearm Incident: {{ incident_category }}</b><br>
<b>Type:</b> {{ incident_subcategory }}<br>
<b>Location:</b><br>{{ PROPER(incident_address) }}<br>
<b>Neighborhood:</b><br>{{ PROPER(neighborhood) }}<br>
<b>Status:</b> {{ resolution }}<br>
<b>Reported:</b> {{ incident_datetime }}
</div>"""
    }
}

def get_map_data_from_datasf(chart_config):
    """Fetch incident data from DataSF API for the most recent complete day."""
    
    # First, find the latest date in the dataset
    latest_date_query = f"""
    SELECT 
        incident_date
    WHERE 
        {chart_config['incident_filter']}
        AND incident_date IS NOT NULL
    ORDER BY incident_date DESC
    LIMIT 1
    """
    
    try:
        latest_result = client.get(chart_config['dataset_id'], query=latest_date_query)
        if not latest_result:
            raise ValueError("No data found in dataset")
            
        latest_date = datetime.fromisoformat(latest_result[0]['incident_date'].split('T')[0])
        logging.info(f"Latest data available is from: {latest_date.strftime('%Y-%m-%d')}")
        
        # Query for the last 7 days of incidents
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
    
    # Base query
    base_query = f"""
    SELECT 
        latitude,
        longitude,
        incident_datetime,
        incident_date,
        incident_time,
        incident_year,
        incident_day_of_week,
        report_datetime,
        row_id,
        incident_id,
        incident_number,
        cad_number,
        report_type_code,
        report_type_description,
        filed_online,
        incident_code,
        incident_category,
        incident_subcategory,
        incident_description,
        resolution,
        intersection,
        cnn,
        police_district,
        analysis_neighborhood,
        supervisor_district,
        supervisor_district_2012
    WHERE 
        ({chart_config['incident_filter']})
        AND incident_date >= '{start_date_str}'
        AND incident_date <= '{end_date_str}'
        AND latitude IS NOT NULL
        AND longitude IS NOT NULL
    ORDER BY incident_datetime DESC
    """
    
    # Log the full query for debugging
    logging.info(f"Full query being executed:\n{base_query}")
    
    offset = 0
    limit = 1000
    all_results = []
    
    # Try a test query first to verify data exists
    test_query = f"""
    SELECT COUNT(*) as count
    WHERE ({chart_config['incident_filter']})
        AND incident_date >= '{start_date_str}'
        AND incident_date <= '{end_date_str}'
    """
    logging.info(f"Executing test count query:\n{test_query}")
    try:
        count_result = client.get(chart_config['dataset_id'], query=test_query)
        total_count = int(count_result[0]['count']) if count_result else 0
        logging.info(f"Total records for category (all time): {total_count}")
    except Exception as e:
        logging.error(f"Error checking category existence: {str(e)}")
        total_count = 0
    
    if total_count == 0:
        logging.warning(f"No data found for incident filter: {chart_config['incident_filter']}")
        logging.warning("Trying query without time filter to check if category exists...")
        test_query = f"SELECT COUNT(*) as count WHERE ({chart_config['incident_filter']})"
        try:
            count_result = client.get(chart_config['dataset_id'], query=test_query)
            total_count = int(count_result[0]['count']) if count_result else 0
            logging.info(f"Total records for category (all time): {total_count}")
        except Exception as e:
            logging.error(f"Error checking category existence: {str(e)}")
    
    # Now fetch actual data
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
        'lat', 'long', 'incident_datetime', 'incident_address',
        'neighborhood', 'district', 'incident_category',
        'incident_subcategory', 'resolution'
    ]
    final_df = pd.DataFrame(columns=required_cols)
    
    if not df.empty:
        # Convert datetime
        df['incident_datetime'] = pd.to_datetime(df['incident_datetime'])
        
        # Prepare columns for the final dataset
        df['formatted_datetime'] = df['incident_datetime'].dt.strftime('%B %d, %Y %I:%M %p')
        end_date_ts = pd.Timestamp(end_date)
        df['days_ago'] = ((end_date_ts - df['incident_datetime']).dt.total_seconds() / 86400).round(1)
        
        # Handle potential missing columns and values
        # First, log the actual columns we have
        logging.info(f"Actual columns in response: {df.columns.tolist()}")
        
        # Format neighborhood with title case (proper capitalization)
        if 'analysis_neighborhood' in df.columns:
            df['analysis_neighborhood'] = df['analysis_neighborhood'].apply(
                lambda x: x.title() if isinstance(x, str) else 'Unknown'
            )
        else:
            df['analysis_neighborhood'] = 'Unknown'
        
        # Create incident_address from intersection if available
        if 'intersection' in df.columns:
            df['incident_address'] = df['intersection'].fillna('Unknown Location')
        else:
            df['incident_address'] = 'Unknown Location'
        
        # Fill missing values for required columns
        df['resolution'] = df['resolution'].fillna('Open/Pending')
        df['incident_category'] = df['incident_category'].fillna('Unknown')
        df['incident_subcategory'] = df['incident_subcategory'].fillna('Unknown')
        df['police_district'] = df['police_district'].fillna('Unknown')
        
        # Create final DataFrame with specific columns
        final_df = pd.DataFrame({
            'lat': df['latitude'].astype(float),
            'long': df['longitude'].astype(float),
            'incident_datetime': df['formatted_datetime'],
            'incident_address': df['incident_address'],
            'neighborhood': df['analysis_neighborhood'],
            'district': df['police_district'],
            'incident_category': df['incident_category'],
            'incident_subcategory': df['incident_subcategory'],
            'resolution': df['resolution'],
            'days_ago': df['days_ago']
        })
        
        # Log the first few rows to verify format
        logging.info(f"Sample of final data:\n{final_df.head().to_string()}")
        
    logging.info(f"Retrieved total of {len(final_df)} incidents from DataSF")
    return final_df, end_date

def update_datawrapper_map(chart_id, data, config, latest_date):
    """Update a Datawrapper map with new incident data"""
    try:
        logger.info(f"Updating Datawrapper map {chart_id}")
        
        # Verify data format before sending
        if not all(col in data.columns for col in ['lat', 'long']):
            raise ValueError(f"Missing required columns. Found: {data.columns.tolist()}")
        
        # Create a new DataFrame with Datawrapper's expected column names
        dw_data = pd.DataFrame({
            'latitude': pd.to_numeric(data['lat'], errors='coerce'),
            'longitude': pd.to_numeric(data['long'], errors='coerce'),
            'incident_category': data['incident_category'],
            'incident_subcategory': data['incident_subcategory'],
            'incident_address': data['incident_address'],
            'incident_datetime': data['incident_datetime'],
            'days_ago': data['days_ago'],
            'neighborhood': data['neighborhood'],
            'district': data['district'],
            'resolution': data['resolution']
        })
        
        # Drop any rows with invalid lat/long
        dw_data = dw_data.dropna(subset=['latitude', 'longitude'])
        
        # FIRST: Fetch current chart metadata to preserve custom settings
        current_chart = dw.get_chart(chart_id)
        current_metadata = current_chart.get('metadata', {})
        
        # Get current visualization settings
        current_viz_settings = current_metadata.get('visualize', {})
        
        # Format date for display
        query_date_range = f"{(latest_date - timedelta(days=7)).strftime('%B %d')} - {latest_date.strftime('%B %d, %Y')}"
        
        # Start with essential metadata we always want to update
        metadata = {
            "describe": {
                "source-name": "DataSF - Police Department Incident Reports",
                "source-url": "https://data.sfgov.org/Public-Safety/Police-Department-Incident-Reports-2018-to-Present/wg3w-h783",
                "intro": f"Showing {len(dw_data):,} incidents from {query_date_range}.",
                "byline": "San Francisco Examiner",
                "title": config['title']
            }
        }
        
        # Preserve visualization settings from current chart metadata
        # But only if they exist - otherwise use our default settings
        if current_viz_settings:
            metadata["visualize"] = current_viz_settings
            
            # Update specific date-related text while preserving other settings
            if "intro" in metadata["describe"]:
                metadata["describe"]["intro"] = f"Showing {len(dw_data):,} incidents from {query_date_range}."
            
            # Ensure we're using the right mapping settings
            if "mapping" not in metadata:
                metadata["mapping"] = {
                    "latitude": "latitude",
                    "longitude": "longitude",
                    "color": "incident_category"
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
                    "column": "incident_category",
                    "palette": {
                        "type": "categorical"
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
                "color": "incident_category"
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
        published_url = update_datawrapper_map(
            chart_id=config["chart_id"],
            data=data,
            config=config,
            latest_date=latest_date
        )
        
        # Apply template settings if provided and this chart has a chart_id
        if template_file and config["chart_id"]:
            # Calculate the date range for display
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
                intro=f"Showing {len(data):,} incidents from {query_date_range}.",
                tooltip_template=tooltip_template
            )
        
        logger.info(f"Successfully updated {config_name} map: {published_url}")
    
    except Exception as e:
        import traceback
        logger.error(f"Failed to update {config_name} map: {e}")
        logger.error(traceback.format_exc())

def update_all_maps():
    """Update all configured maps with chart IDs"""
    logger.info("Starting scheduled update of all 911 incident maps")
    
    # First, check if we have a source template to use
    template = None
    template_file = "911_map_template.json"
    
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
    
    logger.info("Completed update of all maps with valid chart IDs")

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
        logger.info("5. Update the chart_id in MAP_CONFIGS for each map type") 