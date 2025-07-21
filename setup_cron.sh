#!/bin/bash
# Setup script for SF Examiner data pipeline cron job

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}SF Examiner Data Pipeline Setup${NC}"
echo "=================================="

# Get the current directory
CURRENT_DIR=$(pwd)
PYTHON_PATH=$(which python3)

echo -e "\n${YELLOW}Configuration:${NC}"
echo "Project directory: $CURRENT_DIR"
echo "Python path: $PYTHON_PATH"

# Create the cron job entry
CRON_ENTRY="0 3 * * * cd $CURRENT_DIR && $PYTHON_PATH run_all_updates.py >> daily_update.log 2>&1"

echo -e "\n${YELLOW}Proposed cron job (runs daily at 3:00 AM):${NC}"
echo "$CRON_ENTRY"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "run_all_updates.py"; then
    echo -e "\n${YELLOW}Warning: A cron job for run_all_updates.py already exists.${NC}"
    echo "Current crontab:"
    crontab -l | grep "run_all_updates.py"
    echo ""
    read -p "Do you want to replace it? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 1
    fi
    # Remove existing cron job
    crontab -l | grep -v "run_all_updates.py" | crontab -
fi

# Add the new cron job
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ Cron job added successfully!${NC}"
    echo ""
    echo "The pipeline will now run daily at 3:00 AM."
    echo "Logs will be written to:"
    echo "  - daily_update.log (overall run log)"
    echo "  - master_update.log (detailed script execution)"
    echo "  - Individual script logs (sf_911_maps.log, etc.)"
    echo ""
    echo "To view current cron jobs: crontab -l"
    echo "To remove this cron job: crontab -e"
    echo ""
    echo -e "${YELLOW}Testing the setup...${NC}"
    
    # Make the script executable
    chmod +x run_all_updates.py
    
    # Test run (but don't actually execute to avoid interfering)
    echo "To test manually, run: python3 run_all_updates.py"
    
else
    echo -e "\n${RED}❌ Failed to add cron job${NC}"
    exit 1
fi 