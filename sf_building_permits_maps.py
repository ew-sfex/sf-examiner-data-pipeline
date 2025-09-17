#!/usr/bin/env python3
# DataSF to Datawrapper Automation Pipeline - Building Permits Maps
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
        logging.FileHandler("sf_building_permits_maps.log"),
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

# Configuration for Building Permits maps
MAP_CONFIGS = {
    "permits_issued_map": {
        "dataset_id": "i98e-djp9",  # Building Permits dataset
        "chart_id": "2X0Uf",  # Building Permits Issued map
        "permit_filter": "issued_date IS NOT NULL",
        "date_field": "issued_date",
        "title": "Building Permits Issued",
        "description": "Location of recently issued building permits",
        "marker_color": "#cf4236",  # SF Examiner red
        "tooltip_template": """<div style="font-family:Arial,sans-serif;line-height:1.3;">
<b>Building Permit Issued</b><br>
<b>Address:</b> {{ PROPER(address) }}<br>
<b>Type:</b> {{ PROPER(permit_type_definition) }}<br>
<b>Status:</b> {{ UPPER(status) }}<br>
<b>Issued:</b> {{ issued_datetime }}<br>
<b>Cost:</b> {{ FORMAT(estimated_cost, "$0,0") }}<br>
<b>Neighborhood:</b> {{ PROPER(neighborhood) }}
</div>"""
    },
    "permits_completed_map": {
        "dataset_id": "i98e-djp9",  # Building Permits dataset
        "chart_id": "fra7O",  # Building Permits Completed map
        "permit_filter": "completed_date IS NOT NULL",
        "date_field": "completed_date", 
        "title": "Building Permits Completed",
        "description": "Location of recently completed building permits",
        "marker_color": "#7e883f",  # SF Examiner green
        "tooltip_template": """<div style="font-family:Arial,sans-serif;line-height:1.3;">
<b>Building Permit Completed</b><br>
<b>Address:</b> {{ PROPER(address) }}<br>
<b>Type:</b> {{ PROPER(permit_type_definition) }}<br>
<b>Status:</b> {{ UPPER(status) }}<br>
<b>Completed:</b> {{ completed_datetime }}<br>
<b>Cost:</b> {{ FORMAT(estimated_cost, "$0,0") }}<br>
<b>Neighborhood:</b> {{ PROPER(neighborhood) }}
</div>"""
    }
}

def get_map_data_from_datasf(chart_config):
    """Fetch building permit location data from DataSF API for the most recent complete month."""
    
    # First, find the latest date in the dataset for the specific date field
    date_field = chart_config['date_field']
    latest_date_query = f"""
    SELECT 
        {date_field}
    WHERE 
        {chart_config['permit_filter']}
        AND {date_field} IS NOT NULL
    ORDER BY {date_field} DESC
    LIMIT 1
    """
    
    try:
        latest_result = client.get(chart_config['dataset_id'], query=latest_date_query)
        if not latest_result:
            raise ValueError("No data found in dataset")
            
        latest_date = datetime.fromisoformat(latest_result[0][date_field].split('T')[0])
        logging.info(f"Latest data available is from: {latest_date.strftime('%Y-%m-%d')}")
        
        # For building permits, we want data from the last 7 days (like 911 maps)
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
    
    # Base query - extract latitude/longitude from location field
    base_query = f"""
    SELECT 
        permit_number,
        permit_type_definition,
        description,
        status,
        {date_field},
        estimated_cost,
        street_number,
        street_name,
        street_suffix,
        neighborhoods_analysis_boundaries,
        supervisor_district,
        location
    WHERE 
        {chart_config['permit_filter']}
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
    WHERE {chart_config['permit_filter']}
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
        logging.warning(f"No data found for permit filter: {chart_config['permit_filter']}")
        logging.warning("Trying query without time filter to check if permits exist...")
        test_query = f"SELECT COUNT(*) as count WHERE {chart_config['permit_filter']} AND location IS NOT NULL"
        try:
            count_result = client.get(chart_config['dataset_id'], query=test_query)
            total_count = int(count_result[0]['count']) if count_result else 0
            logging.info(f"Total records for permits (all time): {total_count}")
        except Exception as e:
            logging.error(f"Error checking permit existence: {str(e)}")
    
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
        'lat', 'long', 'status', 'address', 'issued_datetime', 'completed_datetime',
        'neighborhood', 'district', 'permit_type_definition', 'estimated_cost', 'description'
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
        
        # Create formatted datetime fields
        if date_field == 'issued_date':
            df['issued_datetime'] = df[date_field].dt.strftime('%B %d, %Y %I:%M %p')
            df['completed_datetime'] = 'Not completed'
        else:  # completed_date
            df['completed_datetime'] = df[date_field].dt.strftime('%B %d, %Y %I:%M %p')
            df['issued_datetime'] = 'N/A'
        
        # Handle potential missing columns and values
        logging.info(f"Actual columns in response: {df.columns.tolist()}")
        
        # Add missing columns with default values if they don't exist
        required_columns = [
            'neighborhoods_analysis_boundaries', 'supervisor_district', 
            'permit_type_definition', 'estimated_cost', 'status',
            'street_number', 'street_name', 'street_suffix', 'description'
        ]
        
        for col in required_columns:
            if col not in df.columns:
                logging.warning(f"Column '{col}' not found in response, adding with default values")
                df[col] = 'Not Available'
        
        # Fill missing values in existing columns
        df['neighborhoods_analysis_boundaries'] = df['neighborhoods_analysis_boundaries'].fillna('N/A')
        df['supervisor_district'] = df['supervisor_district'].fillna('N/A')
        df['permit_type_definition'] = df['permit_type_definition'].fillna('Unknown')
        df['estimated_cost'] = df['estimated_cost'].fillna('0')
        df['status'] = df['status'].fillna('Unknown')
        df['description'] = df['description'].fillna('No description available')
        
        # Format estimated cost as currency
        df['estimated_cost'] = df['estimated_cost'].apply(
            lambda x: f"{float(x):,.0f}" if str(x).replace('.', '').isdigit() else "Unknown"
        )
        
        # Create address from street components
        def create_address(row):
            parts = []
            if pd.notna(row['street_number']) and row['street_number'] != 'Not Available':
                parts.append(str(row['street_number']))
            if pd.notna(row['street_name']) and row['street_name'] != 'Not Available':
                parts.append(str(row['street_name']))
            if pd.notna(row['street_suffix']) and row['street_suffix'] != 'Not Available':
                parts.append(str(row['street_suffix']))
            return ' '.join(parts) if parts else 'Address Unknown'
        
        df['address'] = df.apply(create_address, axis=1)
        
        # Format neighborhood with title case
        df['neighborhoods_analysis_boundaries'] = df['neighborhoods_analysis_boundaries'].apply(
            lambda x: x.title() if isinstance(x, str) else x
        )
        
        # Create final DataFrame with specific columns
        final_df = pd.DataFrame({
            'lat': pd.to_numeric(df['lat'], errors='coerce'),
            'long': pd.to_numeric(df['long'], errors='coerce'),
            'status': df['status'],
            'address': df['address'],
            'issued_datetime': df['issued_datetime'],
            'completed_datetime': df['completed_datetime'],
            'neighborhood': df['neighborhoods_analysis_boundaries'],
            'district': df['supervisor_district'],
            'permit_type_definition': df['permit_type_definition'],
            'estimated_cost': df['estimated_cost'],
            'description': df['description']
        })
        
        # Drop any rows with invalid lat/long
        final_df = final_df.dropna(subset=['lat', 'long'])
        
        # Ensure the DataFrame has the correct column order
        final_df = final_df[required_cols]
        
        # Log the first few rows to verify format
        logging.info(f"Sample of final data:\n{final_df.head().to_string()}")
        
    logging.info(f"Retrieved total of {len(final_df)} permits from DataSF")
    return final_df, end_date

def update_datawrapper_map(chart_id, data, config, latest_date):
    """Update a Datawrapper map with new building permit data"""
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
            'issued_datetime': data['issued_datetime'],
            'completed_datetime': data['completed_datetime'],
            'neighborhood': data['neighborhood'],
            'district': data['district'],
            'permit_type_definition': data['permit_type_definition'],
            'estimated_cost': data['estimated_cost'],
            'description': data['description']
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
                "source-name": "DataSF - Building Permits",
                "source-url": "https://data.sfgov.org/Housing-and-Buildings/Building-Permits/i98e-djp9",
                "intro": f"Showing {len(dw_data):,} permits from {query_date_range}.",
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
                metadata["describe"]["intro"] = f"Showing {len(dw_data):,} permits from {query_date_range}."
            
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
                            "issued": "#44ff44",
                            "complete": "#4444ff",
                            "filed": "#ffaa44",
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

def save_map_template(source_chart_id, template_file="building_permits_map_template.json"):
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

def apply_map_template(chart_id, template_file="building_permits_map_template.json", title=None, intro=None, tooltip_template=None):
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
        if template_file and config["chart_id"] != "2X0Uf":  # 2X0Uf is the source map
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
                intro=f"Showing {len(data):,} permits from {query_date_range}.",
                tooltip_template=tooltip_template
            )
        
        logger.info(f"Successfully updated {config_name} map")
    
    except Exception as e:
        import traceback
        logger.error(f"Failed to update {config_name} map: {e}")
        logger.error(traceback.format_exc())

def update_all_maps():
    """Update all configured maps"""
    logger.info("Starting scheduled update of all building permits maps")
    
    # First, save template from the first working map (when configured)
    template = None
    template_file = "building_permits_map_template.json"
    
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
    
    logger.info("Completed update of all building permits maps")

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
