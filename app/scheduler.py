import os
import logging
import time
from typing import Dict, Any
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import json

logger = logging.getLogger(__name__)

class JobScheduler:
    """Schedules and runs automated job searches"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.search_interval = int(os.getenv('JOB_SEARCH_INTERVAL', 24))
        self.last_run_file = './data/last_run.json'
        
        # Create data directory
        os.makedirs('./data', exist_ok=True)
        
        # Schedule the job
        self._setup_schedule()
        
        # Start the scheduler
        self.scheduler.start()
        logger.info(f"Job scheduler started with interval of {self.search_interval} hours")
    
    def _setup_schedule(self):
        """Set up the schedule for job searches"""
        # Run every N hours
        self.scheduler.add_job(
            func=self.run_job_search,
            trigger=IntervalTrigger(hours=self.search_interval),
            id='job_search',
            name='Search for new jobs',
            replace_existing=True
        )
        
        # Also run at 8:00 AM daily
        self.scheduler.add_job(
            func=self.run_job_search,
            trigger=CronTrigger(hour=8, minute=0),
            id='job_search_daily',
            name='Daily job search at 8 AM',
            replace_existing=True
        )
        
        logger.info("Job search schedules configured")
    
    def run_job_search(self) -> Dict:
        """Run the complete job search process"""
        logger.info("=" * 60)
        logger.info(f"Running scheduled job search at {datetime.now()}")
        logger.info("=" * 60)
        
        try:
            # Get the target role
            role = os.getenv('JOB_SEARCH_KEYWORDS', 'Python Developer').split(',')[0].strip()
            location = os.getenv('JOB_LOCATION', 'Remote')
            
            # Step 1: Search for jobs
            from app.job_scraper import JobScraper
            scraper = JobScraper()
            jobs = scraper.search_jobs([role])
            
            logger.info(f"Found {len(jobs)} jobs for {role}")
            
            # Step 2: Process top jobs
            processed_results = []
            if jobs:
                from app.crew import JobSearchCrew
                crew = JobSearchCrew()
                
                # Load resume template
                resume_path = os.getenv('RESUME_TEMPLATE_PATH', './data/resumes/template.md')
                with open(resume_path, 'r') as f:
                    resume_content = f.read()
                
                # Process up to 3 jobs
                for job in jobs[:3]:
                    try:
                        result = crew.process_job_application(
                            job.get('title', ''),
                            job.get('location', 'Remote'),
                            resume_content
                        )
                        processed_results.append({
                            'job': job,
                            'status': 'processed',
                            'result': result
                        })
                        logger.info(f"Processed job: {job.get('title')} at {job.get('company')}")
                    except Exception as e:
                        logger.error(f"Error processing job {job.get('id', 'unknown')}: {str(e)}")
                        processed_results.append({
                            'job': job,
                            'status': 'failed',
                            'error': str(e)
                        })
            
            # Save results
            result_data = {
                'timestamp': datetime.now().isoformat(),
                'jobs_found': len(jobs),
                'jobs_processed': len(processed_results),
                'processed_jobs': processed_results
            }
            
            with open(self.last_run_file, 'w') as f:
                json.dump(result_data, f, indent=2)
            
            logger.info(f"Job search completed. Processed {len(processed_results)} jobs")
            
            return result_data
            
        except Exception as e:
            logger.error(f"Error in scheduled job search: {str(e)}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'status': 'failed'
            }
    
    def get_last_run_status(self) -> Dict:
        """Get the status of the last job search run"""
        try:
            with open(self.last_run_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'timestamp': None,
                'status': 'no_run',
                'message': 'No job search has been run yet'
            }
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Job scheduler stopped")