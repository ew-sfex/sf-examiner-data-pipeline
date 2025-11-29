# Datawrapper Automation Pipeline - Project Blueprint

**A comprehensive guide for building automated data visualization pipelines**

*Created from the SF Examiner project - proven in production*

---

## 🎯 What This System Does

This blueprint enables you to build **automated data pipelines** that:
- **Fetch** data from public APIs or databases
- **Process** and transform data into visualization-ready formats
- **Update** Datawrapper charts and maps automatically
- **Schedule** daily/hourly updates with zero manual intervention
- **Monitor** pipeline health with comprehensive logging

**Proven Scale:** The SF Examiner project runs 25 visualizations (15 maps + 10 charts) with 2-minute nightly updates.

---

## 🏗️ System Architecture

### Core Pattern: Modular Pipeline Scripts

Each data source gets **two Python scripts**:

1. **`source_maps.py`** - Updates location-based visualizations (Datawrapper maps)
2. **`source_charts.py`** - Updates trend visualizations (Datawrapper charts)

**Why separate?** Different data freshness needs:
- Maps: Show "last 24 hours" or "last 7 days" (real-time)
- Charts: Show monthly trends over years (historical)

### Directory Structure

```
your-project/
├── Core Pipeline Scripts
│   ├── dataset1_maps.py          # Real-time location data
│   ├── dataset1_charts.py        # Historical trends
│   ├── dataset2_maps.py
│   └── dataset2_charts.py
│
├── Master Orchestration
│   ├── run_all_updates.py        # Executes all pipelines
│   └── setup_cron.sh             # Automated scheduling setup
│
├── Configuration
│   ├── requirements.txt          # Python dependencies
│   ├── .env.example              # API key template
│   └── .gitignore                # Exclude secrets/data
│
├── Templates (optional)
│   ├── map_template.json         # Datawrapper map config
│   └── chart_template.json       # Datawrapper chart config
│
├── Data Storage (optional)
│   └── data_sources/
│       ├── raw/                  # Original API responses
│       └── processed/            # Cleaned/transformed data
│
├── Deployment
│   ├── .github/workflows/
│   │   └── update-charts.yml     # GitHub Actions (cloud)
│   └── setup_cron.sh             # Traditional server setup
│
└── Documentation
    ├── README.md                 # User-facing documentation
    ├── DEPLOYMENT_GUIDE.md       # Server setup guide
    └── GITHUB_DEPLOYMENT.md      # Cloud setup guide
```

---

## 🚀 Quick Start Guide

### 1. Initial Setup (5 minutes)

```bash
# Create project directory
mkdir your-project-name
cd your-project-name

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install pandas datawrapper requests python-dotenv
pip freeze > requirements.txt
```

### 2. Get API Credentials

**Datawrapper:**
1. Create account at https://app.datawrapper.de/
2. Generate API token at https://app.datawrapper.de/account/api-tokens
3. Copy token for later

**Your Data Source:**
- Identify your data API (e.g., Socrata/DataSF, REST API, database)
- Get authentication credentials if required

### 3. Create First Pipeline Script

See **Code Templates** section below for complete examples.

### 4. Test Locally

```bash
# Run individual pipeline
python your_first_pipeline.py

# Check Datawrapper to verify chart updated
```

---

## 📝 Code Templates

### Template 1: Basic Pipeline Script

```python
#!/usr/bin/env python3
"""
Data Pipeline: [DATASET_NAME] to Datawrapper
Updates [description of visualizations]
"""

import os
import pandas as pd
import requests
import datawrapper
import logging
from datetime import datetime, timedelta

# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pipeline_name.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# API CREDENTIALS
# ============================================================================

# Use environment variables with fallback for development
DATAWRAPPER_API_KEY = os.environ.get("DATAWRAPPER_API_KEY", "YOUR_KEY_HERE")
DATA_SOURCE_API_KEY = os.environ.get("DATA_SOURCE_API_KEY", "YOUR_KEY_HERE")

# Initialize Datawrapper client
dw = datawrapper.Datawrapper(access_token=DATAWRAPPER_API_KEY)

# ============================================================================
# CONFIGURATION
# ============================================================================

CHART_CONFIGS = {
    "chart_name_1": {
        "chart_id": "xxxxx",           # Your Datawrapper chart ID
        "title": "Chart Title Here",
        "description": "Chart description",
        "data_endpoint": "https://api.example.com/data",
        "query_params": {
            "filter": "value",
            "limit": 1000
        }
    },
    "chart_name_2": {
        "chart_id": "yyyyy",
        "title": "Another Chart",
        # ... more config
    }
}

# ============================================================================
# DATA FETCHING FUNCTIONS
# ============================================================================

def fetch_data_from_api(endpoint, params=None):
    """
    Fetch data from external API
    
    Args:
        endpoint: API endpoint URL
        params: Query parameters dictionary
        
    Returns:
        pandas.DataFrame: Processed data
    """
    try:
        logger.info(f"Fetching data from {endpoint}")
        
        # Make API request
        headers = {"Authorization": f"Bearer {DATA_SOURCE_API_KEY}"}
        response = requests.get(endpoint, params=params, headers=headers)
        response.raise_for_status()
        
        # Convert to DataFrame
        data = response.json()
        df = pd.DataFrame(data)
        
        logger.info(f"Fetched {len(df)} records")
        return df
        
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        raise

# ============================================================================
# DATA PROCESSING FUNCTIONS
# ============================================================================

def process_data_for_chart(df, chart_config):
    """
    Transform raw data into chart-ready format
    
    Args:
        df: Raw data DataFrame
        chart_config: Configuration dictionary for this chart
        
    Returns:
        pandas.DataFrame: Processed data ready for Datawrapper
    """
    try:
        # Example processing steps:
        
        # 1. Filter data
        df_filtered = df[df['category'] == chart_config.get('filter_value')]
        
        # 2. Group/aggregate
        df_grouped = df_filtered.groupby('date').agg({
            'count': 'sum',
            'value': 'mean'
        }).reset_index()
        
        # 3. Sort
        df_sorted = df_grouped.sort_values('date')
        
        # 4. Rename columns to be chart-friendly
        df_final = df_sorted.rename(columns={
            'date': 'Date',
            'count': 'Total Count',
            'value': 'Average Value'
        })
        
        return df_final
        
    except Exception as e:
        logger.error(f"Error processing data: {e}")
        raise

# ============================================================================
# DATAWRAPPER UPDATE FUNCTIONS
# ============================================================================

def update_chart(chart_id, data_df, title=None, description=None):
    """
    Update a Datawrapper chart with new data
    
    Args:
        chart_id: Datawrapper chart ID
        data_df: pandas DataFrame with chart data
        title: Optional new title
        description: Optional new description
    """
    try:
        logger.info(f"Updating chart {chart_id}")
        
        # Upload data
        dw.add_data(chart_id, data_df)
        logger.info(f"Data uploaded: {len(data_df)} rows")
        
        # Update metadata if provided
        if title or description:
            properties = {}
            if title:
                properties['title'] = title
            if description:
                properties['metadata'] = {'describe': {'intro': description}}
            
            dw.update_chart(chart_id, **properties)
            logger.info("Metadata updated")
        
        # Republish chart
        dw.publish_chart(chart_id)
        logger.info(f"✅ Chart {chart_id} published successfully")
        
    except Exception as e:
        logger.error(f"❌ Error updating chart {chart_id}: {e}")
        raise

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def update_all_charts():
    """Main function to update all configured charts"""
    logger.info("=" * 60)
    logger.info("Starting chart update process")
    logger.info("=" * 60)
    
    success_count = 0
    error_count = 0
    
    for chart_name, config in CHART_CONFIGS.items():
        try:
            logger.info(f"\nProcessing: {chart_name}")
            
            # Fetch data
            raw_data = fetch_data_from_api(
                config['data_endpoint'],
                config.get('query_params')
            )
            
            # Process data
            chart_data = process_data_for_chart(raw_data, config)
            
            # Update chart
            update_chart(
                config['chart_id'],
                chart_data,
                config.get('title'),
                config.get('description')
            )
            
            success_count += 1
            
        except Exception as e:
            logger.error(f"Failed to update {chart_name}: {e}")
            error_count += 1
    
    # Summary
    logger.info("=" * 60)
    logger.info(f"Update complete: {success_count} succeeded, {error_count} failed")
    logger.info("=" * 60)

if __name__ == "__main__":
    update_all_charts()
```

### Template 2: Map Pipeline Script

```python
#!/usr/bin/env python3
"""
Map Pipeline: [DATASET_NAME] Location Maps
Updates Datawrapper maps with recent location data
"""

import os
import pandas as pd
import datawrapper
import logging
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("maps_pipeline.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# API credentials
DATAWRAPPER_API_KEY = os.environ.get("DATAWRAPPER_API_KEY")
dw = datawrapper.Datawrapper(access_token=DATAWRAPPER_API_KEY)

# ============================================================================
# MAP CONFIGURATION
# ============================================================================

MAP_CONFIGS = {
    "location_type_1": {
        "chart_id": "xxxxx",
        "title": "Recent Incidents - Location Type 1",
        "days_back": 7,  # Show last 7 days
        "marker_color": "#cf4236",  # Hex color for markers
        "tooltip_template": """
            <div style="font-family:Arial,sans-serif;line-height:1.3;">
            <b>{{ title }}</b><br>
            <b>Location:</b> {{ address }}<br>
            <b>Date:</b> {{ date }}<br>
            <b>Status:</b> <span style="color:{{ status == 'Open' ? '#d44' : '#4a4' }}">{{ status }}</span>
            </div>
        """
    }
}

# ============================================================================
# DATA PROCESSING FOR MAPS
# ============================================================================

def prepare_map_data(raw_data, days_back=7):
    """
    Process data for map visualization
    
    Returns DataFrame with required columns:
    - lat: Latitude
    - lng: Longitude  
    - tooltip fields (customizable)
    """
    
    # Filter to recent dates
    cutoff_date = datetime.now() - timedelta(days=days_back)
    df = raw_data[raw_data['date'] >= cutoff_date].copy()
    
    # Remove records without coordinates
    df = df.dropna(subset=['latitude', 'longitude'])
    
    # Rename columns for Datawrapper
    df = df.rename(columns={
        'latitude': 'lat',
        'longitude': 'lng'
    })
    
    # Calculate time ago for tooltip
    df['hours_ago'] = (datetime.now() - df['date']).dt.total_seconds() / 3600
    df['hours_ago'] = df['hours_ago'].round(1)
    
    return df

def update_map(chart_id, data_df, config):
    """Update a Datawrapper map with location data"""
    try:
        logger.info(f"Updating map {chart_id} with {len(data_df)} points")
        
        # Upload data
        dw.add_data(chart_id, data_df)
        
        # Update map properties
        dw.update_chart(chart_id, 
            title=config['title'],
            metadata={
                'visualize': {
                    'tooltip': {'body': config.get('tooltip_template', '')},
                    'marker-color': config.get('marker_color', '#000000')
                }
            }
        )
        
        # Republish
        dw.publish_chart(chart_id)
        logger.info(f"✅ Map {chart_id} published")
        
    except Exception as e:
        logger.error(f"❌ Error updating map {chart_id}: {e}")
        raise

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def update_all_maps():
    """Update all configured maps"""
    logger.info("Starting map updates")
    
    for map_name, config in MAP_CONFIGS.items():
        try:
            # Fetch and process data (implement based on your data source)
            raw_data = fetch_your_data()
            map_data = prepare_map_data(raw_data, config['days_back'])
            
            # Update map
            update_map(config['chart_id'], map_data, config)
            
        except Exception as e:
            logger.error(f"Failed to update {map_name}: {e}")
    
    logger.info("Map updates complete")

if __name__ == "__main__":
    update_all_maps()
```

### Template 3: Master Orchestration Script

```python
#!/usr/bin/env python3
"""
Master Update Script
Runs all pipeline scripts and logs results
"""

import subprocess
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("master_update.log"),
        logging.StreamHandler()
    ]
)

def run_script(script_name, description):
    """Run a Python script and return success status"""
    try:
        logging.info(f"Starting {description}...")
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode == 0:
            logging.info(f"✅ {description} completed successfully")
            return True
        else:
            logging.error(f"❌ {description} failed")
            logging.error(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logging.error(f"❌ {description} timed out")
        return False
    except Exception as e:
        logging.error(f"❌ {description} failed: {e}")
        return False

def main():
    start_time = datetime.now()
    logging.info("🚀 Starting data pipeline updates")
    
    # List all your pipeline scripts here
    scripts = [
        ("dataset1_maps.py", "Dataset 1 Maps"),
        ("dataset1_charts.py", "Dataset 1 Charts"),
        ("dataset2_maps.py", "Dataset 2 Maps"),
        ("dataset2_charts.py", "Dataset 2 Charts"),
    ]
    
    results = {}
    for script, description in scripts:
        results[description] = run_script(script, description)
    
    # Summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    successful = sum(results.values())
    total = len(results)
    
    logging.info("\n" + "=" * 60)
    logging.info("📊 UPDATE SUMMARY")
    logging.info("=" * 60)
    
    for description, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        logging.info(f"{description}: {status}")
    
    logging.info(f"\nCompleted {successful}/{total} updates")
    logging.info(f"Duration: {duration}")
    
    return 0 if successful == total else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
```

---

## 🔐 Environment Variables & Security

### Create `.env` file (do NOT commit to git)

```bash
# .env
DATAWRAPPER_API_KEY=your_datawrapper_token_here
DATA_SOURCE_API_KEY=your_data_source_token_here
```

### Load environment variables in scripts

```python
from dotenv import load_dotenv
load_dotenv()

DATAWRAPPER_API_KEY = os.environ.get("DATAWRAPPER_API_KEY")
```

### Create `.env.example` template (safe to commit)

```bash
# .env.example
DATAWRAPPER_API_KEY=your_key_here
DATA_SOURCE_API_KEY=your_key_here
```

### Update `.gitignore`

```
# Environment
.env
*.log

# Python
__pycache__/
*.py[cod]
venv/
.venv/

# Data
data_sources/
*.csv
*.parquet
*.json

# OS
.DS_Store
```

---

## 📅 Deployment Options

### Option 1: GitHub Actions (Recommended) ⭐

**Pros:** Free, reliable, zero maintenance, professional monitoring

**Setup:**

1. Create `.github/workflows/update-charts.yml`:

```yaml
name: Update Datawrapper Charts

on:
  schedule:
    - cron: '0 3 * * *'  # 3 AM daily (UTC)
  workflow_dispatch:  # Manual trigger option

jobs:
  update:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run updates
      env:
        DATAWRAPPER_API_KEY: ${{ secrets.DATAWRAPPER_API_KEY }}
        DATA_SOURCE_API_KEY: ${{ secrets.DATA_SOURCE_API_KEY }}
      run: |
        python run_all_updates.py
    
    - name: Upload logs
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: update-logs
        path: '*.log'
```

2. Add secrets in GitHub:
   - Go to repository Settings → Secrets → Actions
   - Add `DATAWRAPPER_API_KEY`
   - Add `DATA_SOURCE_API_KEY`

3. Test with manual run:
   - Actions tab → Update Datawrapper Charts → Run workflow

### Option 2: Traditional Server (cron)

**Pros:** Local control, no external dependencies

**Setup script** (`setup_cron.sh`):

```bash
#!/bin/bash
# Automated cron setup for daily updates

PROJECT_DIR=$(pwd)
PYTHON_PATH=$(which python3)

echo "Setting up automated daily updates..."
echo "Project directory: $PROJECT_DIR"
echo "Python path: $PYTHON_PATH"

# Create cron job entry
CRON_JOB="0 3 * * * cd $PROJECT_DIR && $PYTHON_PATH run_all_updates.py >> daily_update.log 2>&1"

# Add to crontab
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "✅ Cron job installed successfully!"
echo "Charts will update daily at 3:00 AM"
echo ""
echo "Verify installation:"
echo "  crontab -l"
echo ""
echo "Test manually:"
echo "  python3 run_all_updates.py"
```

Make executable: `chmod +x setup_cron.sh`

---

## 🎨 Datawrapper Best Practices

### Creating Charts in Datawrapper UI

1. **Start in Datawrapper interface:**
   - Log in to https://app.datawrapper.de/
   - Create new chart/map
   - Set up basic styling, colors, labels
   - Note the Chart ID (e.g., `AbC12` from URL)

2. **Get Chart ID:**
   - URL format: `https://app.datawrapper.de/chart/AbC12/visualize`
   - The 5-character code is your chart_id

3. **Initial data structure:**
   - Upload sample data with correct column names
   - Datawrapper will remember column mappings
   - Your pipeline will update data, keeping format

### Chart Metadata You Can Update via API

```python
dw.update_chart(chart_id,
    title="Your Chart Title",
    metadata={
        'describe': {
            'intro': 'Chart description/subtitle',
            'source-name': 'Data source attribution',
            'source-url': 'https://data-source.com',
            'byline': 'Chart by Your Name'
        },
        'visualize': {
            # Map-specific
            'tooltip': {'body': 'HTML template'},
            'marker-color': '#ff0000',
            
            # Chart-specific (varies by chart type)
            'custom-colors': {
                'Series 1': '#cf4236',
                'Series 2': '#ffd74c'
            }
        }
    }
)
```

### Map Tooltip Templates

Use Datawrapper's templating language in tooltip HTML:

```html
<div style="font-family:Arial,sans-serif;">
  <b>{{ title }}</b><br>
  
  <!-- Conditional formatting -->
  Status: <span style="color:{{ status == 'Open' ? 'red' : 'green' }}">
    {{ status }}
  </span><br>
  
  <!-- Text transformation -->
  Location: {{ PROPER(address) }}<br>
  
  <!-- Number formatting -->
  Value: {{ FORMAT(value, '0,0') }}<br>
  
  <!-- Date formatting -->
  Date: {{ FORMAT(date, 'MMM D, YYYY') }}
</div>
```

**Available functions:**
- `PROPER(text)` - Proper case
- `UPPER(text)` - Uppercase
- `LOWER(text)` - Lowercase
- `FORMAT(number, pattern)` - Number formatting
- Conditional: `{{ condition ? 'if true' : 'if false' }}`

---

## 🔄 Common Data Source Patterns

### Pattern 1: Socrata/DataSF APIs

```python
from sodapy import Socrata

# Initialize client
client = Socrata(
    "data.cityname.gov",
    app_token="YOUR_APP_TOKEN"
)

# Fetch with SoQL query
results = client.get(
    "dataset-id",
    select="column1, column2, COUNT(*) as count",
    where="date >= '2024-01-01'",
    group="column1",
    order="date DESC",
    limit=10000
)

# Convert to DataFrame
df = pd.DataFrame.from_records(results)
```

### Pattern 2: REST APIs

```python
import requests

def fetch_from_rest_api(endpoint, params=None):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(endpoint, params=params, headers=headers)
    response.raise_for_status()  # Raise error for bad status
    
    data = response.json()
    return pd.DataFrame(data['results'])
```

### Pattern 3: Database Query

```python
import sqlalchemy

def fetch_from_database(query):
    # Create database connection
    engine = sqlalchemy.create_engine(
        f"postgresql://{user}:{password}@{host}:{port}/{database}"
    )
    
    # Execute query and return DataFrame
    df = pd.read_sql(query, engine)
    return df
```

### Pattern 4: CSV Files (Local/Remote)

```python
# Remote CSV
df = pd.read_csv("https://example.com/data.csv")

# Local CSV
df = pd.read_csv("data_sources/raw/file.csv")
```

---

## 📊 Common Data Processing Patterns

### Time-based Filtering

```python
from datetime import datetime, timedelta

# Last 24 hours
yesterday = datetime.now() - timedelta(days=1)
df_recent = df[df['date'] >= yesterday]

# Last 7 days
week_ago = datetime.now() - timedelta(days=7)
df_week = df[df['date'] >= week_ago]

# Current month
df['date'] = pd.to_datetime(df['date'])
df_this_month = df[df['date'].dt.month == datetime.now().month]

# Date range (for historical charts)
start_date = "2020-01-01"
end_date = datetime.now().strftime("%Y-%m-%d")
df_range = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
```

### Aggregation for Charts

```python
# Monthly counts
df['month'] = pd.to_datetime(df['date']).dt.to_period('M')
monthly_counts = df.groupby('month').size().reset_index(name='count')
monthly_counts['month'] = monthly_counts['month'].astype(str)

# Category totals
category_totals = df.groupby('category').agg({
    'value': 'sum',
    'count': 'mean'
}).reset_index()

# Multiple aggregations
summary = df.groupby(['category', 'month']).agg({
    'incidents': 'count',
    'value': 'mean',
    'priority': lambda x: (x == 'High').sum()
}).reset_index()
```

### Data Cleaning

```python
# Remove nulls
df_clean = df.dropna(subset=['important_column'])

# Fill missing values
df['column'] = df['column'].fillna(0)
df['category'] = df['category'].fillna('Unknown')

# Remove duplicates
df_unique = df.drop_duplicates(subset=['id'])

# Type conversion
df['date'] = pd.to_datetime(df['date'])
df['value'] = pd.to_numeric(df['value'], errors='coerce')

# String cleaning
df['address'] = df['address'].str.strip()
df['category'] = df['category'].str.title()
```

### Preparing Map Data

```python
def prepare_map_data(df):
    """Standard map data preparation"""
    
    # Must have coordinates
    df = df.dropna(subset=['latitude', 'longitude'])
    
    # Rename for Datawrapper
    df = df.rename(columns={'latitude': 'lat', 'longitude': 'lng'})
    
    # Calculate time ago
    df['hours_ago'] = (
        (datetime.now() - pd.to_datetime(df['date']))
        .dt.total_seconds() / 3600
    ).round(1)
    
    # Clean address for tooltip
    df['address'] = df['address'].str.title()
    
    # Format date for display
    df['reported_datetime'] = pd.to_datetime(df['date']).dt.strftime('%b %d, %Y %I:%M %p')
    
    return df
```

---

## 🧪 Testing & Debugging

### Test Individual Components

```python
# Test data fetching
if __name__ == "__main__":
    data = fetch_data_from_api("https://api.example.com/data")
    print(f"Fetched {len(data)} records")
    print(data.head())

# Test data processing
if __name__ == "__main__":
    raw_data = fetch_data_from_api("...")
    processed = process_data_for_chart(raw_data, config)
    print(processed.head())
    
    # Save to CSV for inspection
    processed.to_csv("test_output.csv", index=False)
```

### Dry Run Mode

```python
DRY_RUN = True  # Set to False for production

def update_chart(chart_id, data_df, title=None):
    if DRY_RUN:
        logger.info(f"[DRY RUN] Would update chart {chart_id}")
        logger.info(f"Data preview:\n{data_df.head()}")
        return
    
    # Actual update code
    dw.add_data(chart_id, data_df)
    dw.publish_chart(chart_id)
```

### Validation Checks

```python
def validate_data(df, required_columns):
    """Validate DataFrame before upload"""
    
    # Check required columns exist
    missing = set(required_columns) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    
    # Check not empty
    if len(df) == 0:
        raise ValueError("DataFrame is empty")
    
    # Check for nulls in key columns
    null_counts = df[required_columns].isnull().sum()
    if null_counts.any():
        logger.warning(f"Null values found: {null_counts}")
    
    logger.info(f"✅ Data validation passed: {len(df)} rows")
```

---

## 📈 Monitoring & Maintenance

### Log File Analysis

```bash
# View recent errors
grep ERROR *.log

# Count successes
grep "✅" master_update.log | wc -l

# See today's runs
grep "$(date +%Y-%m-%d)" master_update.log

# Monitor in real-time
tail -f master_update.log
```

### Email Alerts (Optional)

```python
import smtplib
from email.message import EmailMessage

def send_alert(subject, body):
    """Send email alert for failures"""
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = "alerts@yourdomain.com"
    msg['To'] = "you@yourdomain.com"
    msg.set_content(body)
    
    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login(msg['From'], os.environ.get('EMAIL_PASSWORD'))
        smtp.send_message(msg)

# Usage in pipeline
try:
    update_all_charts()
except Exception as e:
    send_alert(
        "Pipeline Failed",
        f"Error updating charts: {e}"
    )
    raise
```

### Data Quality Checks

```python
def check_data_quality(df, chart_name):
    """Alert if data looks unusual"""
    
    # Check for sudden drops
    if len(df) < 10:
        logger.warning(f"⚠️  {chart_name}: Only {len(df)} records (unusually low)")
    
    # Check for old data
    if 'date' in df.columns:
        latest = pd.to_datetime(df['date']).max()
        age_hours = (datetime.now() - latest).total_seconds() / 3600
        
        if age_hours > 48:
            logger.warning(f"⚠️  {chart_name}: Latest data is {age_hours:.1f} hours old")
    
    # Check for duplicates
    duplicates = df.duplicated().sum()
    if duplicates > 0:
        logger.warning(f"⚠️  {chart_name}: {duplicates} duplicate rows found")
```

---

## 🎓 Lessons from Production

### Key Learnings from SF Examiner Project

1. **Separate maps and charts** - Different update frequencies and data needs
2. **Use environment variables** - Never hardcode API keys
3. **Comprehensive logging** - Essential for debugging remote failures
4. **Individual script logs** - Easier to troubleshoot specific pipelines
5. **Timeout handling** - Some APIs are slow, set reasonable timeouts
6. **Graceful degradation** - One pipeline failure shouldn't break others
7. **Test locally first** - Always verify before deploying to production
8. **Dynamic date ranges** - Hardcoded dates will break your charts
9. **Data validation** - Catch bad data before it breaks visualizations
10. **Keep it simple** - Complex pipelines are harder to maintain

### Common Pitfalls to Avoid

❌ **Don't:** Hardcode dates like "2024-01-01"  
✅ **Do:** Use `datetime.now() - timedelta(days=365)`

❌ **Don't:** Assume API data structure never changes  
✅ **Do:** Check for column existence before accessing

❌ **Don't:** Use one massive script for everything  
✅ **Do:** Modularize by data source and visualization type

❌ **Don't:** Forget to handle API rate limits  
✅ **Do:** Add retry logic and respectful delays

❌ **Don't:** Commit `.env` or log files to git  
✅ **Do:** Use `.gitignore` properly

❌ **Don't:** Deploy without testing individual scripts  
✅ **Do:** Test each pipeline independently first

---

## 📚 Project Checklist

### Initial Setup
- [ ] Create project directory and virtual environment
- [ ] Install dependencies (`pip install pandas datawrapper requests python-dotenv`)
- [ ] Create `requirements.txt`
- [ ] Set up `.gitignore`
- [ ] Create `.env` and `.env.example`

### Data Source Integration
- [ ] Identify data source(s) and API(s)
- [ ] Get API credentials
- [ ] Test data fetching locally
- [ ] Document data structure/schema
- [ ] Handle missing/null values appropriately

### Datawrapper Setup
- [ ] Create Datawrapper account
- [ ] Generate API token
- [ ] Create initial charts/maps in Datawrapper UI
- [ ] Note all chart IDs
- [ ] Test basic API connection

### Pipeline Development
- [ ] Write data fetching functions
- [ ] Write data processing functions
- [ ] Create chart/map update functions
- [ ] Implement error handling
- [ ] Add logging
- [ ] Test with sample data

### Configuration
- [ ] Set up chart/map configurations
- [ ] Configure update frequencies
- [ ] Set appropriate date ranges
- [ ] Customize tooltips/styling

### Testing
- [ ] Test each pipeline script individually
- [ ] Verify charts update correctly
- [ ] Check data accuracy
- [ ] Test error handling
- [ ] Run master script locally

### Deployment
- [ ] Choose deployment method (GitHub Actions recommended)
- [ ] Set up automation
- [ ] Configure secrets/environment variables
- [ ] Test automated run
- [ ] Set up monitoring/alerts

### Documentation
- [ ] Write README with project overview
- [ ] Document each data source
- [ ] List all chart IDs and purposes
- [ ] Create deployment guide
- [ ] Document troubleshooting steps

### Maintenance
- [ ] Set up log rotation
- [ ] Schedule regular checkups
- [ ] Monitor for API changes
- [ ] Keep dependencies updated
- [ ] Document any issues/solutions

---

## 🚀 Next Steps for Your Project

1. **Define your use case:**
   - What data sources will you use?
   - What visualizations do you need?
   - How often should they update?

2. **Set up infrastructure:**
   - Clone this template structure
   - Install dependencies
   - Get API credentials

3. **Build first pipeline:**
   - Start with ONE data source
   - Create ONE chart/map
   - Test thoroughly

4. **Expand gradually:**
   - Add more visualizations
   - Add more data sources
   - Refine processing logic

5. **Deploy to production:**
   - Choose GitHub Actions or server
   - Set up automation
   - Monitor and refine

---

## 📖 Additional Resources

### Datawrapper
- **API Documentation:** https://developer.datawrapper.de/
- **Python Library:** https://github.com/chekos/datawrapper
- **Academy:** https://academy.datawrapper.de/

### Data Sources
- **Socrata/OpenData:** https://dev.socrata.com/
- **Public APIs List:** https://github.com/public-apis/public-apis

### Python Libraries
- **Pandas Documentation:** https://pandas.pydata.org/docs/
- **Requests Documentation:** https://requests.readthedocs.io/
- **APScheduler:** https://apscheduler.readthedocs.io/ (for complex scheduling)

---

## 💡 Support & Community

This blueprint is based on a production system running successfully for the San Francisco Examiner, updating 25 visualizations daily.

**Need help?**
- Review the code templates above
- Check logs for specific error messages
- Test components individually
- Verify API credentials and chart IDs

**Best practices:**
- Start simple, add complexity gradually
- Log everything
- Test locally before deploying
- Keep dependencies updated
- Document as you go

---

## ✅ You're Ready!

Drop this document into your new project and follow the templates. You have everything you need to build a robust, automated data visualization pipeline.

**Good luck with your project!** 🚀

---

*This blueprint was created from a successful production system. Adapt it to your needs and build something amazing!*

