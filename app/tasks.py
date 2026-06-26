from crewai import Task
import logging

logger = logging.getLogger(__name__)

class JobSearchTasks:
    """Define all tasks for the job search system"""
    
    def create_job_search_task(self, agent, role: str, location: str):
        """Create the job search task"""
        return Task(
            description=(
                f"1. Search for job openings matching the role: '{role}'.\n"
                f"2. Focus on positions in '{location}' (remote allowed).\n"
                "3. Collect the following information for each job:\n"
                "   - Job title and company name\n"
                "   - Job description\n"
                "   - Required skills and qualifications\n"
                "   - Application deadline\n"
                "   - Company website and application link\n"
                "4. Prioritize jobs posted within the last 24 hours.\n"
                "5. Rank jobs by relevance to the candidate's profile."
            ),
            expected_output="A comprehensive list of job openings with all details ranked by relevance.",
            agent=agent
        )
    
    def create_resume_customization_task(self, agent, job: dict, resume_template: str):
        """Create the resume customization task"""
        job_title = job.get('title', '')
        job_company = job.get('company', '')
        
        return Task(
            description=(
                f"1. Customize the resume for the {job_title} position at {job_company}.\n"
                f"2. Review the job description and requirements:\n{job.get('description', '')}\n"
                f"3. Highlight relevant experience and skills.\n"
                "4. Optimize for ATS (Applicant Tracking Systems).\n"
                "5. Add relevant keywords from the job description.\n"
                "6. Emphasize achievements and quantifiable results."
            ),
            expected_output="A fully customized resume tailored for the specific job.",
            agent=agent
        )
    
    def create_email_drafting_task(self, agent, job: dict, customized_resume: str):
        """Create the email drafting task"""
        job_title = job.get('title', '')
        job_company = job.get('company', '')
        
        return Task(
            description=(
                f"1. Write a professional email application for the {job_title} position at {job_company}.\n"
                f"2. Include a personalized introduction referencing the role.\n"
                f"3. Highlight key qualifications from the customized resume.\n"
                "4. Express enthusiasm for the company and role.\n"
                "5. Include a call to action for an interview.\n"
                "6. Keep it concise and professional."
            ),
            expected_output="A professional email draft ready to send to the hiring manager.",
            agent=agent
        )