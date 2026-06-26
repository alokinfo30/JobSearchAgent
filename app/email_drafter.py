import os
import logging
from typing import Dict, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class EmailDrafter:
    """Drafts customized emails for job applications"""
    
    def __init__(self):
        self.email_from = os.getenv('EMAIL_FROM', 'your.email@gmail.com')
        self.email_template_path = './data/resumes/email_templates/'
        os.makedirs(self.email_template_path, exist_ok=True)
    
    def draft_email(self, job: Dict, resume_content: str) -> Dict:
        """Draft a customized email for the job application"""
        job_title = job.get('title', '')
        job_company = job.get('company', '')
        
        # Create email parts
        subject = f"Application for {job_title} position at {job_company}"
        
        body = self._generate_email_body(job, resume_content)
        
        email = {
            "to": self._extract_company_email(job),
            "from": self.email_from,
            "subject": subject,
            "body": body,
            "attachments": [f"Resume_{job_company}.pdf"]
        }
        
        # Save email draft
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.email_template_path}email_{job_company}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(email, f, indent=2)
        
        logger.info(f"Email draft saved to {filename}")
        
        return email
    
    def _generate_email_body(self, job: Dict, resume_content: str) -> str:
        """Generate the email body content"""
        job_title = job.get('title', '')
        job_company = job.get('company', '')
        job_desc = job.get('description', '')
        
        # Extract key skills from resume
        resume_skills = self._extract_skills(resume_content)
        
        body = f"""
Dear Hiring Manager,

I am writing to express my strong interest in the {job_title} position at {job_company}. With my background in {', '.join(resume_skills[:3])} and passion for technology, I believe I would be an excellent fit for your team.

{job_desc[:200]}...

Throughout my career, I have developed skills that align perfectly with your requirements:
- {resume_skills[0] if resume_skills else 'Strong technical skills'}
- Experience with modern technologies and best practices
- Proven track record of delivering results

I have attached my resume for your review and would welcome the opportunity to discuss how my experience and skills can contribute to {job_company}'s continued success.

Thank you for your time and consideration.

Best regards,
[Your Name]
[Your LinkedIn Profile URL]
[Your Portfolio/Website URL]
"""
        
        return body
    
    def _extract_skills(self, resume_content: str) -> list:
        """Extract skills from resume content"""
        skills = []
        lines = resume_content.split('\n')
        
        for line in lines:
            if '•' in line and ('experience' in line.lower() or 'skill' in line.lower()):
                skill = line.strip('• ').strip()
                if skill:
                    skills.append(skill)
        
        # If no skills found, add default ones
        if not skills:
            skills = [
                "Python Programming",
                "Web Development",
                "Problem Solving",
                "Team Collaboration",
                "Agile Methodologies"
            ]
        
        return skills[:5]  # Return top 5 skills
    
    def _extract_company_email(self, job: Dict) -> str:
        """Extract or generate company email"""
        # In production, you would extract this from the job listing
        company = job.get('company', '').lower().replace(' ', '')
        return f"careers@{company}.com" if company else "careers@company.com"
    
    def get_email_draft(self, job_id: str) -> Optional[Dict]:
        """Get an email draft by job ID"""
        import glob
        files = glob.glob(f"{self.email_template_path}*{job_id}*.json")
        if files:
            with open(files[0], 'r') as f:
                return json.load(f)
        return None