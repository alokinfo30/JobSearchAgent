from crewai import Agent
import os
import logging
from app.model_manager import model_manager
from langchain_community.llms import OpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

class JobSearchAgents:
    """Define all agents with multi-provider support"""
    
    def __init__(self):
        self.model_manager = model_manager
    
    def _create_llm(self, config: dict):
        """Create LangChain LLM from provider config"""
        provider = config['provider']
        model = config['model']
        temperature = config.get('temperature', 0.5)
        
        try:
            if provider == 'gemini':
                return ChatGoogleGenerativeAI(
                    model=model,
                    google_api_key=os.getenv('GEMINI_API_KEY'),
                    temperature=temperature,
                    convert_system_message_to_human=True
                )
            elif provider == 'groq':
                return ChatGroq(
                    model=model,
                    api_key=os.getenv('GROQ_API_KEY'),
                    temperature=temperature
                )
            elif provider == 'github':
                return ChatOpenAI(
                    model=model,
                    base_url="https://models.github.ai/inference/chat/completions",
                    api_key=os.getenv('GITHUB_TOKEN'),
                    temperature=temperature
                )
            elif provider == 'cerebras':
                return ChatOpenAI(
                    model=model,
                    base_url="https://api.cerebras.ai/v1",
                    api_key=os.getenv('CEREBRAS_API_KEY'),
                    temperature=temperature
                )
            elif provider == 'openai':
                return ChatOpenAI(
                    model=model,
                    api_key=os.getenv('OPENAI_API_KEY'),
                    temperature=temperature
                )
            else:
                raise ValueError(f"Unknown provider: {provider}")
        except Exception as e:
            logger.error(f"Error creating LLM for {provider}: {str(e)}")
            # Fallback to OpenAI if available
            if os.getenv('OPENAI_API_KEY'):
                return ChatOpenAI(
                    model='gpt-3.5-turbo',
                    api_key=os.getenv('OPENAI_API_KEY'),
                    temperature=temperature
                )
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