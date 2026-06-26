import os
import logging
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
import time

logger = logging.getLogger(__name__)

class JobScraper:
    """Scrapes job listings from various sources"""
    
    def __init__(self):
        self.keywords = os.getenv('JOB_SEARCH_KEYWORDS', 'Python Developer').split(',')
        self.location = os.getenv('JOB_LOCATION', 'Remote')
        self.jobs_data_path = './data/jobs/'
        
        # Create directories if they don't exist
        os.makedirs(self.jobs_data_path, exist_ok=True)
        
    def search_jobs(self, keywords: Optional[List[str]] = None) -> List[Dict]:
        """Search for jobs using configured keywords"""
        search_keywords = keywords if keywords else self.keywords
        all_jobs = []
        
        for keyword in search_keywords:
            keyword = keyword.strip()
            logger.info(f"Searching jobs for: {keyword}")
            
            try:
                # Simulated job search - In production, integrate with actual job APIs
                jobs = self._scrape_simulated_jobs(keyword)
                all_jobs.extend(jobs)
                logger.info(f"Found {len(jobs)} jobs for {keyword}")
            except Exception as e:
                logger.error(f"Error searching jobs for {keyword}: {str(e)}")
        
        # Remove duplicates based on job title and company
        unique_jobs = self._remove_duplicates(all_jobs)
        
        # Save to file
        self._save_jobs(unique_jobs)
        
        return unique_jobs
    
    def _scrape_simulated_jobs(self, keyword: str) -> List[Dict]:
        """Simulate job scraping - Replace with actual API calls"""
        # This is a simulation. In production, you would:
        # 1. Use Indeed API
        # 2. Use LinkedIn API
        # 3. Scrape job boards with proper authentication
        
        jobs = []
        
        # Simulated job data
        companies = ["Google", "Microsoft", "Amazon", "Facebook", "Apple", "Netflix", "Tesla", "SpaceX"]
        locations = ["Remote", "San Francisco", "New York", "Austin", "Seattle", "London", "Berlin"]
        
        for i in range(3):  # Generate 3 jobs per keyword
            job = {
                "id": f"{keyword}_{i}_{int(time.time())}",
                "title": f"{keyword} - {['Senior','Junior','Lead','Principal'][i]}",
                "company": companies[i % len(companies)],
                "location": locations[i % len(locations)],
                "description": f"We are looking for a {keyword} to join our team. Requires experience in {keyword} and related technologies.",
                "requirements": f"• 5+ years of experience\n• Strong {keyword} skills\n• Team player\n• Problem-solving skills",
                "salary_range": f"${80 + i*20}k - ${120 + i*20}k",
                "posted_date": datetime.now().strftime("%Y-%m-%d"),
                "url": f"https://example.com/jobs/{keyword}_{i}",
                "keywords": [keyword]
            }
            jobs.append(job)
        
        return jobs
    
    def _remove_duplicates(self, jobs: List[Dict]) -> List[Dict]:
        """Remove duplicate job listings"""
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            key = f"{job['title']}_{job['company']}"
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        return unique_jobs
    
    def _save_jobs(self, jobs: List[Dict]):
        """Save jobs to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.jobs_data_path}jobs_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(jobs, f, indent=2)
        
        logger.info(f"Saved {len(jobs)} jobs to {filename}")
        
        # Keep only last 5 files
        self._cleanup_old_files()
    
    def _cleanup_old_files(self, keep: int = 5):
        """Keep only the most recent files"""
        import glob
        files = glob.glob(f"{self.jobs_data_path}jobs_*.json")
        files.sort()
        
        if len(files) > keep:
            for file in files[:-keep]:
                os.remove(file)
                logger.info(f"Removed old file: {file}")
    
    def get_latest_jobs(self) -> List[Dict]:
        """Get the latest saved jobs"""
        import glob
        files = glob.glob(f"{self.jobs_data_path}jobs_*.json")
        
        if not files:
            return []
        
        latest_file = max(files)
        with open(latest_file, 'r') as f:
            return json.load(f)