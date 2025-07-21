# San Francisco Examiner Datawrapper Charts Automation

This project enables automatic daily updates of Datawrapper charts using data from the San Francisco open data portal (DataSF). It's designed for the San Francisco Examiner to maintain up-to-date visualizations of city data such as 311 requests and 911 calls.

## Setup

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Installation

1. Clone this repository
```
git clone [your-repository-url]
cd datawrapper-charts-api
```

2. Create a virtual environment (recommended)
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages
```
pip install pandas sodapy datawrapper-python apscheduler
```

4. Configure API keys
   - Create a Datawrapper account and generate an API token at https://app.datawrapper.de/account/api-tokens
   - (Optional) Create a DataSF account and generate an app token at https://dev.socrata.com/register

5. Set environment variables:
```
export DATAWRAPPER_API_KEY="your_datawrapper_api_key"
export DATASF_APP_TOKEN="your_datasf_app_token"  # Optional but recommended
```

## Configuration

Edit the `CHART_CONFIGS` dictionary in `datawrapper_sf_pipeline.py` to:

1. Add your Datawrapper chart IDs (create empty charts first in the Datawrapper UI)
2. Modify the queries to suit your needs
3. Adjust the chart titles or other parameters

## Usage

### Create Initial Charts

1. Log in to Datawrapper and create the charts you want to update automatically
2. Take note of the chart IDs (from the URL, e.g., `https://app.datawrapper.de/chart/CHART_ID`)
3. Add these chart IDs to the `CHART_CONFIGS` dictionary in the script

### Running Manually

To update all charts once:

```
python datawrapper_sf_pipeline.py
```

### Setting Up Automatic Updates

To enable automatic daily updates, uncomment the `setup_scheduler()` line at the bottom of the script:

```python
if __name__ == "__main__":
    # For testing, update all charts immediately
    update_all_charts()
    
    # Uncomment to enable scheduled updates
    setup_scheduler()
```

### Production Deployment

For production use, consider:

1. Using a service like systemd or supervisord to keep the script running
2. Storing API keys in a secure credential manager
3. Setting up email alerts for failed updates

## Available DataSF Datasets

Some useful datasets include:

- 311 Cases: `vw6y-z8j6`
- Police Calls for Service: `fjvx-qyt4`
- Crime Reports: `wg3w-h783`

Browse all available datasets at: https://data.sfgov.org/browse

## Customizing Charts

To create additional chart types beyond the basic examples:

1. Add a new entry to the `CHART_CONFIGS` dictionary
2. Create the corresponding chart in Datawrapper
3. Customize the query to extract the desired data

## Troubleshooting

Check the log file `datasf_to_datawrapper.log` for errors and information.

Common issues:
- API authentication errors: Verify your API keys are correct
- Dataset access issues: Ensure the dataset ID is correct and publicly accessible
- Query errors: Check your SQL syntax in the queries

## License

[Your License Here] 