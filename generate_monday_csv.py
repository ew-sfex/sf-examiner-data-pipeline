#!/usr/bin/env python3
"""
Generate Monday.com CSV inventory of all Datawrapper charts and maps.
Extracts chart metadata from all pipeline and map scripts.
"""

import csv
from datetime import datetime
from typing import List, Dict

# Current date for Last Updated column
CURRENT_DATE = datetime.now().strftime('%Y-%m-%d')

# All chart data extracted from the scripts
charts_data: List[Dict[str, str]] = []

# ============================================================================
# 311 SERVICE MAPS (9 maps) - sf_311_maps.py
# ============================================================================
maps_311 = [
    {
        "chart_id": "nB5JE",
        "title": "Street and sidewalk cleaning requests",
        "chart_type": "Map",
        "category": "311 Service",
        "script_name": "sf_311_maps.py",
        "data_source": "vw6y-z8j6",
        "update_frequency": "Daily",
        "time_range": "Most recent complete day",
        "notes": "Street and sidewalk cleaning service requests"
    },
    {
        "chart_id": "0xtQT",
        "title": "Graffiti reports",
        "chart_type": "Map",
        "category": "311 Service",
        "script_name": "sf_311_maps.py",
        "data_source": "vw6y-z8j6",
        "update_frequency": "Daily",
        "time_range": "Most recent complete day",
        "notes": "Graffiti report locations"
    },
    {
        "chart_id": "os0dX",
        "title": "Encampment reports",
        "chart_type": "Map",
        "category": "311 Service",
        "script_name": "sf_311_maps.py",
        "data_source": "vw6y-z8j6",
        "update_frequency": "Daily",
        "time_range": "Most recent complete day",
        "notes": "Encampment report locations"
    },
    {
        "chart_id": "9JMgr",
        "title": "Tree maintenance requests",
        "chart_type": "Map",
        "category": "311 Service",
        "script_name": "sf_311_maps.py",
        "data_source": "vw6y-z8j6",
        "update_frequency": "Daily",
        "time_range": "Most recent complete day",
        "notes": "Tree maintenance service request locations"
    },
    {
        "chart_id": "V5s4q",
        "title": "Abandoned vehicle reports",
        "chart_type": "Map",
        "category": "311 Service",
        "script_name": "sf_311_maps.py",
        "data_source": "vw6y-z8j6",
        "update_frequency": "Daily",
        "time_range": "Most recent complete day",
        "notes": "Abandoned vehicle report locations"
    },
    {
        "chart_id": "Lu3TG",
        "title": "Sewage backup reports",
        "chart_type": "Map",
        "category": "311 Service",
        "script_name": "sf_311_maps.py",
        "data_source": "vw6y-z8j6",
        "update_frequency": "Daily",
        "time_range": "Most recent complete day",
        "notes": "Sewage backup and discharge reports"
    },
    {
        "chart_id": "acPZT",
        "title": "Sidewalk and street defects",
        "chart_type": "Map",
        "category": "311 Service",
        "script_name": "sf_311_maps.py",
        "data_source": "vw6y-z8j6",
        "update_frequency": "Daily",
        "time_range": "Most recent complete day",
        "notes": "Infrastructure defect reports"
    },
    {
        "chart_id": "XDoKW",
        "title": "Human waste reports",
        "chart_type": "Map",
        "category": "311 Service",
        "script_name": "sf_311_maps.py",
        "data_source": "vw6y-z8j6",
        "update_frequency": "Daily",
        "time_range": "Most recent complete day",
        "notes": "Human waste or urine reports"
    },
    {
        "chart_id": "AJzUh",
        "title": "Noise complaints",
        "chart_type": "Map",
        "category": "311 Service",
        "script_name": "sf_311_maps.py",
        "data_source": "vw6y-z8j6",
        "update_frequency": "Daily",
        "time_range": "Most recent complete day",
        "notes": "Noise complaint locations"
    }
]

# ============================================================================
# 311 SERVICE LINE CHARTS (5 charts) - sf_311_pipeline.py
# ============================================================================
charts_311 = [
    {
        "chart_id": "Fgte7",
        "title": "Street and sidewalk cleaning requests",
        "chart_type": "Line Chart",
        "category": "311 Service",
        "script_name": "sf_311_pipeline.py",
        "data_source": "vw6y-z8j6",
        "update_frequency": "Daily",
        "time_range": "2020-present (monthly comparison)",
        "notes": "Monthly trend comparison across years"
    },
    {
        "chart_id": "aswDZ",
        "title": "Graffiti reports",
        "chart_type": "Line Chart",
        "category": "311 Service",
        "script_name": "sf_311_pipeline.py",
        "data_source": "vw6y-z8j6",
        "update_frequency": "Daily",
        "time_range": "2020-present (monthly comparison)",
        "notes": "Monthly trend comparison across years"
    },
    {
        "chart_id": "BJfSt",
        "title": "Encampment reports",
        "chart_type": "Line Chart",
        "category": "311 Service",
        "script_name": "sf_311_pipeline.py",
        "data_source": "vw6y-z8j6",
        "update_frequency": "Daily",
        "time_range": "2020-present (monthly comparison)",
        "notes": "Monthly trend comparison across years"
    },
    {
        "chart_id": "dQte4",
        "title": "Tree maintenance requests",
        "chart_type": "Line Chart",
        "category": "311 Service",
        "script_name": "sf_311_pipeline.py",
        "data_source": "vw6y-z8j6",
        "update_frequency": "Daily",
        "time_range": "2020-present (monthly comparison)",
        "notes": "Monthly trend comparison across years"
    },
    {
        "chart_id": "R3cXx",
        "title": "Abandoned vehicle reports",
        "chart_type": "Line Chart",
        "category": "311 Service",
        "script_name": "sf_311_pipeline.py",
        "data_source": "vw6y-z8j6",
        "update_frequency": "Daily",
        "time_range": "2020-present (monthly comparison)",
        "notes": "Monthly trend comparison across years"
    }
]

# ============================================================================
# 911 CRIME MAPS (5 maps) - sf_911_maps.py
# ============================================================================
maps_911 = [
    {
        "chart_id": "TX5ff",
        "title": "Violent crime incidents",
        "chart_type": "Map",
        "category": "911 Crime",
        "script_name": "sf_911_maps.py",
        "data_source": "wg3w-h783",
        "update_frequency": "Daily",
        "time_range": "Last 7 days",
        "notes": "Homicide, Robbery, Assault, Sex Offense incidents"
    },
    {
        "chart_id": "AbO6X",
        "title": "Property crime incidents",
        "chart_type": "Map",
        "category": "911 Crime",
        "script_name": "sf_911_maps.py",
        "data_source": "wg3w-h783",
        "update_frequency": "Daily",
        "time_range": "Last 7 days",
        "notes": "Burglary, Larceny Theft, Motor Vehicle Theft, Arson"
    },
    {
        "chart_id": "h8x3T",
        "title": "Drug offense incidents",
        "chart_type": "Map",
        "category": "911 Crime",
        "script_name": "sf_911_maps.py",
        "data_source": "wg3w-h783",
        "update_frequency": "Daily",
        "time_range": "Last 7 days",
        "notes": "Drug offense incident locations"
    },
    {
        "chart_id": "y8sSh",
        "title": "Vehicle-related incidents",
        "chart_type": "Map",
        "category": "911 Crime",
        "script_name": "sf_911_maps.py",
        "data_source": "wg3w-h783",
        "update_frequency": "Daily",
        "time_range": "Last 7 days",
        "notes": "Traffic collisions, violations, and vehicle thefts"
    },
    {
        "chart_id": "YiMUb",
        "title": "Firearm-related incidents",
        "chart_type": "Map",
        "category": "911 Crime",
        "script_name": "sf_911_maps.py",
        "data_source": "wg3w-h783",
        "update_frequency": "Daily",
        "time_range": "Last 7 days",
        "notes": "Incidents involving firearms"
    }
]

# ============================================================================
# 911 CRIME LINE CHARTS (5 charts) - sf_911_pipeline.py
# ============================================================================
charts_911 = [
    {
        "chart_id": "1DNOm",
        "title": "Violent crime incidents",
        "chart_type": "Line Chart",
        "category": "911 Crime",
        "script_name": "sf_911_pipeline.py",
        "data_source": "wg3w-h783",
        "update_frequency": "Daily",
        "time_range": "Last 5 years (monthly comparison)",
        "notes": "Monthly trend comparison across years"
    },
    {
        "chart_id": "MRgFo",
        "title": "Property crime incidents",
        "chart_type": "Line Chart",
        "category": "911 Crime",
        "script_name": "sf_911_pipeline.py",
        "data_source": "wg3w-h783",
        "update_frequency": "Daily",
        "time_range": "Last 5 years (monthly comparison)",
        "notes": "Monthly trend comparison across years"
    },
    {
        "chart_id": "ZquUz",
        "title": "Drug offense incidents",
        "chart_type": "Line Chart",
        "category": "911 Crime",
        "script_name": "sf_911_pipeline.py",
        "data_source": "wg3w-h783",
        "update_frequency": "Daily",
        "time_range": "Last 5 years (monthly comparison)",
        "notes": "Monthly trend comparison across years"
    },
    {
        "chart_id": "Z9xal",
        "title": "Vehicle-related incidents",
        "chart_type": "Line Chart",
        "category": "911 Crime",
        "script_name": "sf_911_pipeline.py",
        "data_source": "wg3w-h783",
        "update_frequency": "Daily",
        "time_range": "Last 5 years (monthly comparison)",
        "notes": "Monthly trend comparison across years"
    },
    {
        "chart_id": "DgPPX",
        "title": "Firearm-related incidents",
        "chart_type": "Line Chart",
        "category": "911 Crime",
        "script_name": "sf_911_pipeline.py",
        "data_source": "wg3w-h783",
        "update_frequency": "Daily",
        "time_range": "Last 5 years (monthly comparison)",
        "notes": "Monthly trend comparison across years"
    }
]

# ============================================================================
# BUILDING PERMITS MAPS (2 maps) - sf_building_permits_maps.py
# ============================================================================
maps_permits = [
    {
        "chart_id": "2X0Uf",
        "title": "Building permits issued",
        "chart_type": "Map",
        "category": "Building Permits",
        "script_name": "sf_building_permits_maps.py",
        "data_source": "i98e-djp9",
        "update_frequency": "Daily",
        "time_range": "Last 7 days",
        "notes": "Recently issued building permit locations"
    },
    {
        "chart_id": "fra7O",
        "title": "Building permits completed",
        "chart_type": "Map",
        "category": "Building Permits",
        "script_name": "sf_building_permits_maps.py",
        "data_source": "i98e-djp9",
        "update_frequency": "Daily",
        "time_range": "Last 7 days",
        "notes": "Recently completed building permit locations"
    }
]

# ============================================================================
# BUILDING PERMITS LINE CHARTS (2 charts) - sf_building_permits_pipeline.py
# ============================================================================
charts_permits = [
    {
        "chart_id": "qKV9i",
        "title": "Building permits issued",
        "chart_type": "Line Chart",
        "category": "Building Permits",
        "script_name": "sf_building_permits_pipeline.py",
        "data_source": "i98e-djp9",
        "update_frequency": "Daily",
        "time_range": "2020-present (monthly comparison)",
        "notes": "Monthly trend comparison across years"
    },
    {
        "chart_id": "B6RMy",
        "title": "Building permits completed",
        "chart_type": "Line Chart",
        "category": "Building Permits",
        "script_name": "sf_building_permits_pipeline.py",
        "data_source": "i98e-djp9",
        "update_frequency": "Daily",
        "time_range": "2020-present (monthly comparison)",
        "notes": "Monthly trend comparison across years"
    }
]

# ============================================================================
# BUSINESS ACTIVITY MAPS (1 map) - sf_business_openings_maps.py
# ============================================================================
maps_business = [
    {
        "chart_id": "TWHZY",
        "title": "Recent business activity",
        "chart_type": "Map",
        "category": "Business Activity",
        "script_name": "sf_business_openings_maps.py",
        "data_source": "g8m3-pdis",
        "update_frequency": "Daily",
        "time_range": "Last 7 days",
        "notes": "New business openings and relocations"
    }
]

# ============================================================================
# BUSINESS ACTIVITY LINE CHARTS (1 chart) - sf_business_openings_pipeline.py
# ============================================================================
charts_business = [
    {
        "chart_id": "jy28w",
        "title": "Business openings",
        "chart_type": "Line Chart",
        "category": "Business Activity",
        "script_name": "sf_business_openings_pipeline.py",
        "data_source": "g8m3-pdis",
        "update_frequency": "Daily",
        "time_range": "2020-present (monthly comparison)",
        "notes": "Monthly trend comparison across years"
    }
]

# ============================================================================
# REAL ESTATE LINE CHARTS (6 charts)
# ============================================================================
# Metro charts - sf_rdc_inventory_charts.py
charts_rdc_metro = [
    {
        "chart_id": "ri9VR",
        "title": "San Francisco median listing price per square foot",
        "chart_type": "Line Chart",
        "category": "Real Estate",
        "script_name": "sf_rdc_inventory_charts.py",
        "data_source": "Realtor.com RDC Metro Inventory",
        "update_frequency": "Monthly",
        "time_range": "2020-present (monthly comparison)",
        "notes": "SF metro area listing price per sqft"
    },
    {
        "chart_id": "fnk2G",
        "title": "San Francisco active for-sale listings",
        "chart_type": "Line Chart",
        "category": "Real Estate",
        "script_name": "sf_rdc_inventory_charts.py",
        "data_source": "Realtor.com RDC Metro Inventory",
        "update_frequency": "Monthly",
        "time_range": "2020-present (monthly comparison)",
        "notes": "SF metro area active listing count"
    },
    {
        "chart_id": "xBni4",
        "title": "San Francisco median listing price",
        "chart_type": "Line Chart",
        "category": "Real Estate",
        "script_name": "sf_rdc_inventory_charts.py",
        "data_source": "Realtor.com RDC Metro Inventory",
        "update_frequency": "Monthly",
        "time_range": "2020-present (monthly comparison)",
        "notes": "SF metro area median listing price"
    },
    {
        "chart_id": "wcABj",
        "title": "San Francisco median days on market",
        "chart_type": "Line Chart",
        "category": "Real Estate",
        "script_name": "sf_rdc_inventory_charts.py",
        "data_source": "Realtor.com RDC Metro Inventory",
        "update_frequency": "Monthly",
        "time_range": "2020-present (monthly comparison)",
        "notes": "SF metro area median days on market"
    }
]

# County charts - sf_rdc_county_charts.py
charts_rdc_county = [
    {
        "chart_id": "L9p0d",
        "title": "Bay Area listing price per square foot (by county)",
        "chart_type": "Line Chart",
        "category": "Real Estate",
        "script_name": "sf_rdc_county_charts.py",
        "data_source": "Realtor.com RDC Metro Inventory",
        "update_frequency": "Monthly",
        "time_range": "2019-present (by county)",
        "notes": "9 Bay Area counties price per sqft comparison"
    },
    {
        "chart_id": "NNv75",
        "title": "Bay Area median listing price (by county)",
        "chart_type": "Line Chart",
        "category": "Real Estate",
        "script_name": "sf_rdc_county_charts.py",
        "data_source": "Realtor.com RDC Metro Inventory",
        "update_frequency": "Monthly",
        "time_range": "2019-present (by county)",
        "notes": "9 Bay Area counties median listing price comparison"
    }
]

# ============================================================================
# WILDFIRE MAP (1 map) - Placeholder for wildfire tracking
# ============================================================================
maps_wildfire = [
    {
        "chart_id": "TBD",
        "title": "California wildfire activity",
        "chart_type": "Map",
        "category": "Wildfire",
        "script_name": "TBD",
        "data_source": "TBD",
        "update_frequency": "TBD",
        "time_range": "TBD",
        "notes": "Wildfire map - configuration pending"
    }
]

# ============================================================================
# Combine all charts
# ============================================================================
all_charts = (
    maps_311 + charts_311 +
    maps_911 + charts_911 +
    maps_permits + charts_permits +
    maps_business + charts_business +
    charts_rdc_metro + charts_rdc_county +
    maps_wildfire
)

# Add calculated fields
for chart in all_charts:
    # Public URL
    if chart["chart_id"] != "TBD":
        chart["public_url"] = f"https://datawrapper.dwcdn.net/{chart['chart_id']}/"
    else:
        chart["public_url"] = "TBD"
    
    # Status
    chart["status"] = "Active" if chart["chart_id"] != "TBD" else "Pending"
    
    # Priority based on category
    priority_map = {
        "911 Crime": "High",
        "311 Service": "High",
        "Real Estate": "Medium",
        "Building Permits": "Medium",
        "Business Activity": "Medium",
        "Wildfire": "High"
    }
    chart["priority"] = priority_map.get(chart["category"], "Medium")
    
    # Owner (blank for manual assignment)
    chart["owner"] = ""
    
    # Last Updated
    chart["last_updated"] = CURRENT_DATE

# ============================================================================
# Generate CSV
# ============================================================================
def generate_csv(filename: str = "datawrapper_charts_inventory.csv"):
    """Generate the Monday.com inventory CSV file."""
    
    # Define CSV columns in order
    fieldnames = [
        "Chart ID",
        "Chart Name/Title",
        "Chart Type",
        "Category",
        "Script Name",
        "Data Source",
        "Update Frequency",
        "Time Range Displayed",
        "Public URL",
        "Status",
        "Priority",
        "Owner/Responsible",
        "Last Updated",
        "Notes"
    ]
    
    # Map internal keys to CSV column names
    key_mapping = {
        "Chart ID": "chart_id",
        "Chart Name/Title": "title",
        "Chart Type": "chart_type",
        "Category": "category",
        "Script Name": "script_name",
        "Data Source": "data_source",
        "Update Frequency": "update_frequency",
        "Time Range Displayed": "time_range",
        "Public URL": "public_url",
        "Status": "status",
        "Priority": "priority",
        "Owner/Responsible": "owner",
        "Last Updated": "last_updated",
        "Notes": "notes"
    }
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for chart in all_charts:
            # Map internal keys to CSV columns
            row = {}
            for col_name, key in key_mapping.items():
                row[col_name] = chart.get(key, "")
            writer.writerow(row)
    
    print(f"✅ CSV generated successfully: {filename}")
    print(f"📊 Total charts: {len(all_charts)}")
    print(f"\nBreakdown by category:")
    
    # Count by category
    category_counts = {}
    for chart in all_charts:
        cat = chart["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    for category, count in sorted(category_counts.items()):
        print(f"  - {category}: {count}")
    
    print(f"\nBreakdown by type:")
    # Count by type
    type_counts = {}
    for chart in all_charts:
        chart_type = chart["chart_type"]
        type_counts[chart_type] = type_counts.get(chart_type, 0) + 1
    
    for chart_type, count in sorted(type_counts.items()):
        print(f"  - {chart_type}: {count}")

if __name__ == "__main__":
    generate_csv()

