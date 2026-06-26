import os
import logging
from typing import Dict, Optional
import markdown
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class ResumeCustomizer:
    """Customizes resume based on job requirements"""
    
    def __init__(self):
        self.template_path = os.getenv('RESUME_TEMPLATE_PATH', './data/resumes/template.md')
        self.output_path = os.getenv('RESUME_OUTPUT_PATH', './data/resumes/customized/')
        
        # Create directories
        os.makedirs(self.output_path, exist_ok=True)
        os.makedirs(os.path.dirname(self.template_path), exist_ok=True)
        
        # Create template if it doesn't exist
        if not os.path.exists(self.template_path):
            self._create_template()
    
    def _create_template(self):
        """Create a default resume template"""
        template = """# [Your Name]
## Contact Information
- **Email**: your.email@example.com
- **Phone**: (123) 456-7890
- **Location**: Remote/Anywhere
- **GitHub**: github.com/yourusername
- **LinkedIn**: linkedin.com/in/yourusername

## Professional Summary
[Write your professional summary here]

## Technical Skills
- **Programming Languages**: Python, JavaScript, Java, C++
- **Frameworks**: Django, Flask, React, Node.js
- **Tools**: Git, Docker, AWS, Linux
- **Other**: Team Leadership, Agile Development

## Work Experience

### [Company Name] - [Location]
**[Job Title]** | [Start Date] - [End Date]
- [Accomplishment 1]
- [Accomplishment 2]
- [Accomplishment 3]

### [Previous Company] - [Location]
**[Previous Job Title]** | [Start Date] - [End Date]
- [Accomplishment 1]
- [Accomplishment 2]

## Education

### [University Name] - [Location]
**[Degree]** | [Year]
- [Relevant coursework]
- [Achievements]

## Projects

### [Project Name]
- [Description]
- [Technologies used]
- [Link or result]

## Certifications
- [Certification 1] - [Year]
- [Certification 2] - [Year]

## Languages
- [Language 1]: [Proficiency]
- [Language 2]: [Proficiency]
"""
        
        with open(self.template_path, 'w') as f:
            f.write(template)
        
        logger.info(f"Created resume template at {self.template_path}")
    
    def customize_resume(self, job: Dict, resume_content: Optional[str] = None) -> str:
        """Customize resume for a specific job"""
        if resume_content is None:
            resume_content = self._load_template()
        
        # Customize based on job
        job_title = job.get('title', '')
        job_desc = job.get('description', '')
        job_company = job.get('company', '')
        job_requirements = job.get('requirements', '')
        
        # Create customized version
        customized = self._customize_content(resume_content, job_title, job_desc, job_requirements)
        
        # Save customized resume
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_path}resume_{job_company}_{timestamp}.md"
        
        with open(filename, 'w') as f:
            f.write(customized)
        
        logger.info(f"Customized resume saved to {filename}")
        
        return customized
    
    def _load_template(self) -> str:
        """Load the resume template"""
        try:
            with open(self.template_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            self._create_template()
            with open(self.template_path, 'r') as f:
                return f.read()
    
    def _customize_content(self, content: str, job_title: str, job_desc: str, requirements: str) -> str:
        """Customize the resume content for the job"""
        # This would be more sophisticated with proper AI integration
        # For now, we'll do basic customization
        
        lines = content.split('\n')
        customized_lines = []
        
        for line in lines:
            # Update professional summary
            if 'Professional Summary' in line and 'Write your professional summary' in line:
                customized_lines.append(f"Professional Summary")
                customized_lines.append(f"Experienced {job_title} with expertise in {job_desc[:100]}. {job_company if 'company' in locals() else ''}")
                continue
            
            # Update skills section
            if 'Technical Skills' in line:
                customized_lines.append(line)
                # Add requirements as skills
                if requirements:
                    req_skills = requirements.split('\n')
                    for req in req_skills:
                        if req.strip() and not req.strip().startswith('•'):
                            customized_lines.append(f"- {req.strip()}")
                continue
            
            customized_lines.append(line)
        
        return '\n'.join(customized_lines)
    
    def get_customized_resume(self, job_id: str) -> Optional[str]:
        """Get a customized resume by job ID"""
        import glob
        files = glob.glob(f"{self.output_path}*{job_id}*.md")
        if files:
            with open(files[0], 'r') as f:
                return f.read()
        return None