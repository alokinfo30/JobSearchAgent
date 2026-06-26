# JobSearchAgent

Automated Job Search Agent using CrewAI with asynchronous operations. This system will run daily, find jobs, customize resumes, and draft emails.


JobSearchAgent/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── agents.py
│   ├── tasks.py
│   ├── crew.py
│   ├── job_scraper.py
│   ├── resume_customizer.py
│   ├── email_drafter.py
│   ├── scheduler.py
│   └── model_manager.py
├── templates/
│   └── dashboard.html
├── static/
│   ├── style.css
│   └── script.js
├── data/
│   └── resumes/
├── logs/
├── .env
├── .gitignore
├── requirements.txt
├── test_free_models.py
├── generate_secret.py
└── run_scheduler.py



# Automated Job Search Agent

An intelligent job search system powered by CrewAI multi-agent architecture that automatically finds jobs, customizes resumes, and drafts application emails.

## Features

- 🤖 **Multi-Agent System**: Three specialized AI agents work together
- 🔍 **Automated Job Search**: Searches for jobs matching your profile
- ✏️ **Resume Customization**: Tailors your resume for each job
- ✉️ **Email Drafting**: Creates professional application emails
- ⏰ **Scheduled Runs**: Automatically runs daily or at custom intervals
- 📊 **Dashboard**: Monitor job search progress in real-time
- 🔄 **Multi-Model Support**: Falls back to alternative models if needed

## Architecture

### Agents

1. **Job Search Specialist**: Finds relevant job opportunities
2. **Resume Customization Expert**: Customizes resumes for specific jobs
3. **Application Email Specialist**: Drafts professional application emails

### Workflow
Search Jobs → Customize Resume → Draft Email → Review


## Installation

### 1. Clone and Setup

```bash
git clone <repository-url>
cd JobSearchAgent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

2. Configuration
Create a .env file with your configuration:

Add your OpenAI API key

Configure job search keywords

Set email settings

3. Generate Secret Key
bash
python generate_secret.py
Copy the generated key to your .env file.

4. Test Models
bash
python test_models.py

Running the Application
Web Dashboard
bash
python -m app.main
Open your browser to http://localhost:5000


#  Run the Test: powershell
python test_free_models.py

Run the Complete System
powershell
# 1. Test free providers
python test_free_models.py

# 2. Run the application
python -m app.main

# 3. Open browser to http://localhost:5000
Summary of Free Provider Quotas
Provider	Daily Limit	Best For	Setup Difficulty
Google Gemini	1,500 requests	All tasks, long context	Easy - no credit card
Groq	~1,000 requests	Fast inference	Easy - no credit card
Cerebras	~1M tokens	Batch processing	Easy - no credit card 
GitHub Models	150-1,000	Frontier models	GitHub account needed 



Scheduled Job Scheduler
bash
python run_scheduler.py
API Endpoints
GET /api/health - Health check

POST /api/search_jobs - Search for jobs

POST /api/process_job - Process a job application

POST /api/run_scheduled_search - Run scheduled job search


Security Features
✅ Secure secret key generation

✅ Environment variables for sensitive data

✅ Input validation and sanitization

✅ Rate limiting

✅ CORS protection

✅ Logging for monitoring

How to Get FREE API Keys
1. Google Gemini (Recommended - 1,500 requests/day)
Go to https://ai.google.dev/

Click "Get API Key"

Sign in with Google account

Create new API key

Copy to .env as GEMINI_API_KEY

2. Groq (1,000 requests/day)
Go to https://console.groq.com/

Sign up (free)

Go to API Keys

Create new key

Copy to .env as GROQ_API_KEY

3. Cerebras API Key

Go to Cerebras Inference page → Visit cerebras.ai/inference

Click "Get API Key" button → You'll find it prominently on the inference page

Sign up / Create account → Follow the registration process (free)

Copy your API key → Save it for your .env file

4. GitHub Models API Key:
Go to GitHub → Visit github.com and sign in

Create Personal Access Token:

Click your profile picture → Settings

Scroll down → Developer settings → Personal access tokens → Tokens (classic)

Click "Generate new token (classic)"

Give it a name (e.g., models-access)

Under Scopes, check read:models (this is essential)

Click "Generate token"

COPY THE TOKEN IMMEDIATELY (you won't see it again!)

5. Cloudflare Workers AI

Sign up for Cloudflare → Go to cloudflare.com and create a free account

Go to Workers Dashboard → Navigate to Workers & Pages

Click "Create application" → Choose "Create Worker"

Name your Worker → Give it a name (e.g., my-ai-worker)

Click "Deploy" → This creates a Hello World worker

Enable Workers AI:

In the dashboard, go to "Workers & Pages" → "AI"

Enable Workers AI for your account (free tier is enough)

Add AI Binding to your Worker:

In your worker settings → "Settings" → "Variables"

Under "Bindings" , click "Add binding"

Choose "Workers AI" from the dropdown

Save and deploy


## Summary

This complete Automated Job  Search Agent system includes:

1. **Three specialized agents**: Job Searcher, Resume Customizer, Email Drafter
2. **Automated workflow**: Search → Customize → Draft
3. **Scheduler**: Runs daily or at custom intervals
4. **Web Dashboard**: Monitor and control the process
5. **Multi-model support**: Fallback models for reliability
6. **Complete file structure**: All necessary files and configurations
7. **Production ready**: Security, logging, and deployment configurations


 API Endpoints Summary
Endpoint	Method	Description
/	GET	Dashboard
/api/health	GET	Health check with provider status
/api/providers	GET	List all configured providers
/api/search_jobs	POST	Search for jobs
/api/process_job	POST	Process single job application
/api/process_multiple_jobs	POST	Process multiple jobs
/api/run_scheduled_search	POST	Run scheduled job search
/api/resume/template	GET	Get resume template
/api/resume/template	POST	Update resume template
/api/stats	GET	Application statistics




======================================================================
💡 Provider Recommendations:
   • Gemini: Best for search and analysis (1,500 req/day)
   • Groq: Best for fast processing (1,000 req/day, 30 RPM)
   • GitHub: Best for writing tasks (1,000 req/day)
   • Cerebras: Best for batch processing (1M tokens/day)
======================================================================