#!/usr/bin/env python
"""
Run the automated job search scheduler
Run: python run_scheduler.py
"""

import os
import sys
import logging
import time
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run the job scheduler"""
    try:
        from app.scheduler import JobScheduler
        
        logger.info("=" * 60)
        logger.info("Starting Automated Job Search Scheduler")
        logger.info("=" * 60)
        
        scheduler = JobScheduler()
        
        # Run immediately on startup
        logger.info("Running initial job search...")
        result = scheduler.run_job_search()
        logger.info(f"Initial search completed: {result}")
        
        # Keep the scheduler running
        logger.info("Scheduler is running. Press Ctrl+C to stop.")
        
        try:
            # Keep the script running
            while True:
                time.sleep(60)
                status = scheduler.get_last_run_status()
                logger.info(f"Last run: {status.get('timestamp', 'Never')}")
                
        except KeyboardInterrupt:
            logger.info("Stopping scheduler...")
            scheduler.stop()
            logger.info("Scheduler stopped.")
            
    except Exception as e:
        logger.error(f"Error running scheduler: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()