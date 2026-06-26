from crewai import Agent
import os
import logging
from app.model_manager import model_manager
from langchain_openai import ChatOpenAI
from langchain_community.llms import OpenAI

logger = logging.getLogger(__name__)

class JobSearchAgents:
    """Define all agents with OpenRouter support"""
    
    def __init__(self):
        self.model_manager = model_manager
    
    def _create_llm(self, config: dict):
        """Create LangChain LLM from OpenRouter config"""
        model = config['model']
        temperature = config.get('temperature', 0.5)
        
        try:
            return ChatOpenAI(
                model=model,
                api_key=os.getenv('OPENROUTER_API_KEY'),
                base_url=os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1'),
                temperature=temperature,
                default_headers={
                    "HTTP-Referer": os.getenv('OPENROUTER_APP_URL', 'http://localhost:5000'),
                    "X-Title": os.getenv('OPENROUTER_APP_NAME', 'JobSearchAgent')
                }
            )
        except Exception as e:
            logger.error(f"Error creating LLM: {str(e)}")
            raise
    
    def create_job_searcher(self):
        """Create the job searcher agent"""
        config = self.model_manager.get_model_config('job_searcher')
        llm = self._create_llm(config)
        
        return Agent(
            role="Job Search Specialist",
            goal="Find the most relevant and recent job opportunities matching the target role",
            backstory="""You are an expert job searcher with years of experience in the tech industry. 
            You understand the job market deeply and know how to find the best opportunities. 
            You research job boards, company websites, and professional networks to find 
            positions that perfectly match the candidate's profile.""",
            allow_delegation=False,
            verbose=True,
            llm=llm
        )
    
    def create_resume_customizer(self):
        """Create the resume customizer agent"""
        config = self.model_manager.get_model_config('resume_customizer')
        llm = self._create_llm(config)
        
        return Agent(
            role="Resume Customization Expert",
            goal="Tailor the candidate's resume to match each job opportunity perfectly",
            backstory="""You are a professional resume writer and career coach. 
            You know how to highlight the right skills and experiences for each job. 
            You understand ATS (Applicant Tracking Systems) and how to optimize 
            resumes to pass through them. You emphasize achievements and quantifiable results.""",
            allow_delegation=False,
            verbose=True,
            llm=llm
        )
    
    def create_email_drafter(self):
        """Create the email drafter agent"""
        config = self.model_manager.get_model_config('email_drafter')
        llm = self._create_llm(config)
        
        return Agent(
            role="Application Email Specialist",
            goal="Craft compelling and professional email applications",
            backstory="""You are a professional communication specialist. 
            You write persuasive and professional emails that get noticed. 
            You know how to structure emails to make a strong impression 
            and increase the chances of getting an interview call. 
            You personalize each email for the specific company and role.""",
            allow_delegation=False,
            verbose=True,
            llm=llm
        )