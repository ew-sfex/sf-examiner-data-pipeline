# Datawrapper Charts Inventory - Monday.com Import

## Summary

A comprehensive CSV inventory of all 37 Datawrapper charts and maps has been generated for import into Monday.com.

**File**: `datawrapper_charts_inventory.csv`

## Statistics

- **Total Charts/Maps**: 37 (36 active + 1 wildfire placeholder)
- **Maps**: 18
- **Line Charts**: 19

### Breakdown by Category

| Category | Count | Priority |
|----------|-------|----------|
| 311 Service | 14 | High |
| 911 Crime | 10 | High |
| Real Estate | 6 | Medium |
| Building Permits | 4 | Medium |
| Business Activity | 2 | Medium |
| Wildfire | 1 | High (Pending) |

### Breakdown by Chart Type

| Chart Type | Count |
|------------|-------|
| Map | 18 |
| Line Chart | 19 |

## CSV Columns

The CSV includes 14 comprehensive tracking columns:

1. **Chart ID** - Datawrapper chart ID (e.g., "nB5JE")
2. **Chart Name/Title** - Display title of the chart
3. **Chart Type** - "Map" or "Line Chart"
4. **Category** - 311 Service, 911 Crime, Building Permits, Business Activity, Real Estate, or Wildfire
5. **Script Name** - Python file that updates this chart (e.g., "sf_311_maps.py")
6. **Data Source** - DataSF dataset ID or "Realtor.com RDC Metro Inventory"
7. **Update Frequency** - Daily or Monthly
8. **Time Range Displayed** - What date range the chart shows
9. **Public URL** - Direct link to published chart (https://datawrapper.dwcdn.net/CHART_ID/)
10. **Status** - "Active" or "Pending"
11. **Priority** - High, Medium, or Low based on category
12. **Owner/Responsible** - Blank for manual assignment
13. **Last Updated** - 2025-11-02 (current date)
14. **Notes** - Additional context about the chart

## Chart Details by Category

### 311 Service (14 charts)
**Update Frequency**: Daily  
**Scripts**: `sf_311_maps.py`, `sf_311_pipeline.py`  
**Data Source**: vw6y-z8j6 (311 Cases)

- 9 Maps showing geographic distribution of recent service requests
- 5 Line Charts showing monthly trends across years (2020-present)

Topics covered:
- Street/sidewalk cleaning
- Graffiti reports
- Encampment reports
- Tree maintenance
- Abandoned vehicles
- Sewage backups
- Infrastructure defects
- Human waste reports
- Noise complaints

### 911 Crime (10 charts)
**Update Frequency**: Daily  
**Scripts**: `sf_911_maps.py`, `sf_911_pipeline.py`  
**Data Source**: wg3w-h783 (Police Department Incident Reports)

- 5 Maps showing crime locations from last 7 days
- 5 Line Charts showing monthly trends across last 5 years

Topics covered:
- Violent crimes
- Property crimes
- Drug offenses
- Vehicle-related incidents
- Firearm-related incidents

### Building Permits (4 charts)
**Update Frequency**: Daily  
**Scripts**: `sf_building_permits_maps.py`, `sf_building_permits_pipeline.py`  
**Data Source**: i98e-djp9 (Building Permits)

- 2 Maps showing recent permit locations (last 7 days)
- 2 Line Charts showing monthly trends (2020-present)

Topics covered:
- Permits issued
- Permits completed

### Business Activity (2 charts)
**Update Frequency**: Daily  
**Scripts**: `sf_business_openings_maps.py`, `sf_business_openings_pipeline.py`  
**Data Source**: g8m3-pdis (Registered Business Locations)

- 1 Map showing recent business openings/relocations (last 7 days)
- 1 Line Chart showing monthly trends (2020-present)

### Real Estate (6 charts)
**Update Frequency**: Monthly  
**Scripts**: `sf_rdc_inventory_charts.py`, `sf_rdc_county_charts.py`  
**Data Source**: Realtor.com RDC Metro Inventory

4 San Francisco Metro charts:
- Median listing price per square foot
- Active for-sale listings
- Median listing price
- Median days on market

2 Bay Area County comparison charts:
- Listing price per square foot (9 counties)
- Median listing price (9 counties)

### Wildfire (1 map - Pending)
**Status**: Pending configuration  
**Chart ID**: TBD

Placeholder entry for wildfire map. Needs configuration details.

## How to Import to Monday.com

1. Go to your Monday.com board
2. Click the dropdown menu (⋮) next to the board name
3. Select "Import" → "Import from CSV"
4. Upload `datawrapper_charts_inventory.csv`
5. Map the CSV columns to Monday.com columns:
   - Chart ID → Text column
   - Chart Name/Title → Name/Item column
   - Chart Type → Dropdown/Tag column
   - Category → Dropdown/Tag column
   - Script Name → Text column
   - Data Source → Text column
   - Update Frequency → Dropdown column
   - Time Range Displayed → Text column
   - Public URL → Link column
   - Status → Status column
   - Priority → Priority column
   - Owner/Responsible → People column
   - Last Updated → Date column
   - Notes → Long Text column

## Automation & Maintenance

The inventory was generated using `generate_monday_csv.py`, which:
- Extracts all chart configurations from the 10 Python chart/map scripts
- Compiles metadata for each chart
- Generates a properly formatted CSV for Monday.com import

To regenerate the CSV (e.g., after adding new charts):
```bash
python3 generate_monday_csv.py
```

## Next Steps

1. ✅ Import the CSV into Monday.com
2. ⏳ Assign owners to each chart in the "Owner/Responsible" column
3. ⏳ Configure the wildfire map and update its entry
4. ⏳ Set up Monday.com automations (e.g., notifications when charts need attention)
5. ⏳ Add custom views/filters by Category, Priority, or Update Frequency

## Files Generated

- `datawrapper_charts_inventory.csv` - The Monday.com import file
- `generate_monday_csv.py` - Script to regenerate the inventory
- `CHART_INVENTORY_SUMMARY.md` - This documentation file

---

**Generated**: November 2, 2025  
**Total Charts**: 37 (36 active + 1 pending)

