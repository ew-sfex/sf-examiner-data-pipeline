#!/usr/bin/env python3
"""
Master script to run all SF Examiner chart and map updates
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
    """Run a Python script and log results"""
    try:
        logging.info(f"Starting {description}...")
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            logging.info(f"✅ {description} completed successfully")
            return True
        else:
            logging.error(f"❌ {description} failed with exit code {result.returncode}")
            logging.error(f"Error output: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logging.error(f"❌ {description} timed out after 10 minutes")
        return False
    except Exception as e:
        logging.error(f"❌ {description} failed with exception: {e}")
        return False

def main():
    start_time = datetime.now()
    logging.info("🚀 Starting SF Examiner data update pipeline")
    
    scripts = [
        ("sf_911_maps.py", "911 Maps Update"),
        ("sf_911_pipeline.py", "911 Charts Update"), 
        ("sf_311_maps.py", "311 Maps Update"),
        ("sf_311_pipeline.py", "311 Charts Update")
    ]
    
    results = {}
    
    for script, description in scripts:
        success = run_script(script, description)
        results[description] = success
    
    # Summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    logging.info("\n" + "="*50)
    logging.info("📊 UPDATE SUMMARY")
    logging.info("="*50)
    
    successful = sum(results.values())
    total = len(results)
    
    for description, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        logging.info(f"{description}: {status}")
    
    logging.info(f"\nCompleted {successful}/{total} updates successfully")
    logging.info(f"Total duration: {duration}")
    
    if successful == total:
        logging.info("🎉 All updates completed successfully!")
        return 0
    else:
        logging.error(f"⚠️  {total - successful} updates failed")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 