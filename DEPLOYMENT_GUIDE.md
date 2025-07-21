# SF Examiner Data Pipeline - Deployment Guide

*Updated: July 21, 2025*

## 🎯 Overview

This system automatically updates Datawrapper charts and maps daily with the latest San Francisco open data. The pipeline includes:

- **911 Emergency Data**: 5 maps + 5 charts showing crime incidents
- **311 Service Requests**: 10 maps + 5 charts showing city service calls

**Total: 15 maps + 10 charts = 25 visualizations updated nightly**

## ✅ System Status (July 21, 2025)

- ✅ All 25 visualizations working perfectly
- ✅ Dynamic date ranges (auto-updates monthly)
- ✅ Robust error handling and logging
- ✅ ~2 minute runtime for full update

## 🚀 Quick Deployment

### Option 1: Automated Setup (Recommended)

```bash
# 1. Navigate to project directory
cd /path/to/datawrapper-charts-api

# 2. Run the setup script
./setup_cron.sh
```

This sets up a cron job to run daily at 3:00 AM.

### Option 2: Manual Setup

```bash
# 1. Make the main script executable
chmod +x run_all_updates.py

# 2. Add to crontab manually
crontab -e

# 3. Add this line:
0 3 * * * cd /path/to/datawrapper-charts-api && python3 run_all_updates.py >> daily_update.log 2>&1
```

## 📊 What Gets Updated

### 911 Emergency Data (Police Reports)
**Maps (Last 7 days):**
- Violent crimes (TX5ff)
- Property crimes (AbO6X) 
- Drug offenses (h8x3T)
- Vehicle-related incidents (y8sSh)
- Firearm-related incidents (YiMUb)

**Charts (Monthly trends 2020-present):**
- Violent crimes (1DNOm)
- Property crimes (MRgFo)
- Drug offenses (ZquUz)
- Vehicle-related incidents (Z9xal)
- Firearm-related incidents (DgPPX)

### 311 Service Requests
**Maps (Last day):**
- Street cleaning (nB5JE)
- Graffiti reports (0xtQT)
- Encampments (os0dX)
- Tree maintenance (9JMgr)
- Abandoned vehicles (V5s4q)
- Sewage backups (Lu3TG)
- Street/sidewalk defects (acPZT)
- Human waste (XDoKW)
- Noise complaints (AJzUh)

**Charts (Monthly trends 2020-present):**
- Street cleaning (Fgte7)
- Graffiti reports (aswDZ)
- Encampments (BJfSt)
- Tree maintenance (dQte4)
- Abandoned vehicles (R3cXx)

## 🏗️ Server Deployment Options

### Option A: Your Current Server
If you have a server running 24/7:

1. Upload the project files
2. Install Python dependencies: `pip install -r requirements.txt`
3. Run `./setup_cron.sh`

### Option B: Cloud Solutions

#### AWS EC2 (Recommended)
- **t3.micro** instance (~$8/month)
- Ubuntu 22.04 LTS
- Perfect for this lightweight task

#### DigitalOcean Droplet
- **Basic Droplet** ($4-6/month)
- Ubuntu 22.04
- Easy setup and management

#### Google Cloud Compute Engine
- **e2-micro** instance (free tier eligible)
- Can run within free tier limits

### Option C: Raspberry Pi
- Perfect for this lightweight task
- One-time cost (~$75)
- Runs 24/7 from your location

## 🔧 Server Setup Process

### 1. Server Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and git
sudo apt install python3 python3-pip git cron -y

# Clone your repository
git clone <your-repo-url>
cd datawrapper-charts-api
```

### 2. Python Environment
```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Deploy and Schedule
```bash
# Set up automated updates
./setup_cron.sh

# Test the system
python3 run_all_updates.py
```

## 📋 Monitoring & Maintenance

### Log Files
The system creates several log files:
- `daily_update.log` - Overall execution log
- `master_update.log` - Detailed script execution
- `sf_911_maps.log` - 911 maps specific
- `sf_911_pipeline.log` - 911 charts specific  
- `sf_311_maps.log` - 311 maps specific
- `sf_311_pipeline.log` - 311 charts specific

### Check Status
```bash
# View recent runs
tail -f daily_update.log

# Check if cron job is active
crontab -l

# View detailed logs
tail -f master_update.log
```

### Troubleshooting
```bash
# Test individual components
python3 sf_911_maps.py
python3 sf_911_pipeline.py
python3 sf_311_maps.py
python3 sf_311_pipeline.py

# Run full update manually
python3 run_all_updates.py
```

## ⚙️ Configuration

### Timing
Current schedule: **3:00 AM daily**

To change timing, edit crontab:
```bash
crontab -e

# Examples:
# 0 2 * * * = 2:00 AM daily
# 0 */6 * * * = Every 6 hours
# 0 1 * * 1 = 1:00 AM every Monday
```

### API Limits
- **DataSF**: No strict limits with app token
- **Datawrapper**: 100 API calls/hour (we use ~25/day)

## 🔒 Security Notes

- API keys are currently hardcoded (consider environment variables)
- Server should have basic firewall protection
- Consider automated backups of configuration

## 📈 Performance

**Current metrics:**
- Runtime: ~2 minutes for all updates
- Data volume: ~500KB per run
- Server requirements: Minimal (512MB RAM sufficient)
- Network usage: <10MB per day

## 🆘 Support

If something breaks:

1. **Check logs** for error messages
2. **Test individual scripts** to isolate issues
3. **Verify API credentials** are still valid
4. **Check DataSF/Datawrapper service status**

The system is designed to be robust - individual component failures won't break the entire pipeline.

---

## Ready to Deploy? 

Run this command to set up automated daily updates:

```bash
./setup_cron.sh
```

Your SF Examiner data pipeline will then update all 25 visualizations automatically every night! 🚀 