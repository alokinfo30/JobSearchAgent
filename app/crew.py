from crewai import Crew
import os
import logging
from typing import List, Dict
from app.model_manager import model_manager

logger = logging.getLogger(__name__)

class JobSearchCrew:
    """Orchestrate the job search process with OpenRouter"""
    
    def __init__(self):
        try:
            from app.agents import JobSearchAgents
            from app.tasks import JobSearchTasks
            self.agents = JobSearchAgents()
            self.tasks = JobSearchTasks()
            self.verbose = os.getenv('DEBUG', 'False').lower() == 'true'
            self.model_manager = model_manager
            
            logger.info("JobSearchCrew initialized with OpenRouter")
            
            # Test models
            self._test_models()
            
        except Exception as e:
            logger.error(f"Failed to initialize JobSearchCrew: {str(e)}")
            raise
    
    def _test_models(self):
        """Test all configured models"""
        logger.info("Testing all configured models...")
        results = self.model_manager.test_providers()
        
        available_count = sum(1 for v in results.values() if v)
        total_count = len(results)
        logger.info(f"Models available: {available_count}/{total_count}")
        
        if available_count == 0:
            logger.warning("WARNING: No models are available! Check your OpenRouter API key.")
        else:
            logger.info(f"Available models: {[m for m, v in results.items() if v]}")
    
    def process_job_application(self, role: str, location: str, resume_content: str) -> Dict:
        """Process a complete job application workflow"""
        try:
            logger.info(f"Starting job application process for role: {role}")
            
            # Create agents
            job_searcher = self.agents.create_job_searcher()
            resume_customizer = self.agents.create_resume_customizer()
            email_drafter = self.agents.create_email_drafter()
            
            # Step 1: Search for jobs
            search_task = self.tasks.create_job_search_task(
                job_searcher, role, location
            )
            
            crew_search = Crew(
                agents=[job_searcher],
                tasks=[search_task],
                verbose=self.verbose
            )
            
            logger.info("Searching for jobs...")
            search_result = crew_search.kickoff(inputs={"role": role, "location": location})
            jobs = self._parse_search_result(search_result)
            
            if not jobs:
                logger.warning("No jobs found")
                return {"status": "no_jobs_found", "jobs": []}
            
            # Process top 3 jobs
            processed_jobs = []
            for job in jobs[:3]:
                logger.info(f"Processing job: {job.get('title')} at {job.get('company')}")
                
                # Step 2: Customize resume
                customization_task = self.tasks.create_resume_customization_task(
                    resume_customizer, job, resume_content
                )
                
                crew_customize = Crew(
                    agents=[resume_customizer],
                    tasks=[customization_task],
                    verbose=self.verbose
                )
                
                customized_resume = crew_customize.kickoff(
                    inputs={"job": job, "resume": resume_content}
                )
                
                # Step 3: Draft email
                email_task = self.tasks.create_email_drafting_task(
                    email_drafter, job, str(customized_resume)
                )
                
                crew_email = Crew(
                    agents=[email_drafter],
                    tasks=[email_task],
                    verbose=self.verbose
                )
                
                email_draft = crew_email.kickoff(
                    inputs={"job": job, "resume": customized_resume}
                )
                
                processed_jobs.append({
                    "job": job,
                    "customized_resume": str(customized_resume),
                    "email_draft": str(email_draft)
                })
            
            return {
                "status": "success",
                "total_jobs_found": len(jobs),
                "processed_jobs": processed_jobs
            }
            
        except Exception as e:
            logger.error(f"Job application processing failed: {str(e)}")
            raise
    
    def _parse_search_result(self, search_result: str) -> List[Dict]:
        """Parse the search result into a list of job dictionaries"""
        jobs = []
        
        # Simulate parsing - In reality, you'd parse the AI response structure
        for i in range(3):
            jobs.append({
                "id": f"job_{i}",
                "title": f"Senior Developer - Position {i+1}",
                "company": f"Company {chr(65+i)}",
                "location": "Remote",
                "description": f"This is a great opportunity for a developer with strong skills.",
                "requirements": "- Python\n- React\n- Cloud experience",
                "url": f"https://example.com/job/{i}"
            })
        
        return jobs