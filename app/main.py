import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from flask import Flask, render_template, request, jsonify, session, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import secrets
import bleach
from datetime import datetime
import traceback
import json
import threading
import time

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, 
    template_folder='../templates',
    static_folder='../static'
)

# ============================================
# SECURITY CONFIGURATION
# ============================================

app.secret_key = os.getenv('SECRET_KEY')
if not app.secret_key:
    logger.error("SECRET_KEY not found in environment variables!")
    app.secret_key = secrets.token_urlsafe(32)
    logger.warning(f"Generated temporary SECRET_KEY: {app.secret_key}")
    logger.warning("Please set SECRET_KEY in your .env file for production use!")

# Validate secret key length
if len(app.secret_key) < 32:
    logger.warning("SECRET_KEY is less than 32 characters. Please use a stronger key!")

app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
app.config['SESSION_COOKIE_HTTPONLY'] = os.getenv('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
app.config['SESSION_COOKIE_SAMESITE'] = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

# ============================================
# CORS CONFIGURATION
# ============================================

CORS(app, resources={
    r"/api/*": {
        "origins": os.getenv('CORS_ALLOWED_ORIGINS', '*').split(','),
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# ============================================
# RATE LIMITING
# ============================================

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[os.getenv('RATELIMIT_DEFAULT', '100/day')],
    enabled=os.getenv('RATELIMIT_ENABLED', 'False').lower() == 'true',
    storage_uri="memory://"
)

# ============================================
# VALIDATION FUNCTIONS
# ============================================

def validate_api_keys():
    """Validate all configured API keys"""
    results = {
        'github': bool(os.getenv('GITHUB_TOKEN')),
        'gemini': bool(os.getenv('GEMINI_API_KEY')),
        'groq': bool(os.getenv('GROQ_API_KEY')),
        'cerebras': bool(os.getenv('CEREBRAS_API_KEY')),
        'openai': bool(os.getenv('OPENAI_API_KEY'))
    }
    
    available = sum(1 for v in results.values() if v)
    logger.info(f"API keys available: {available}/5")
    
    if available == 0:
        logger.error("No API keys found! Please configure at least one provider.")
        return False
    
    return True

def get_provider_status():
    """Get detailed provider status"""
    from app.model_manager import model_manager
    return {
        'available_providers': model_manager.get_available_providers(),
        'daily_limits': model_manager.get_daily_limits(),
        'total_providers': len(model_manager.providers)
    }

# ============================================
# ROUTES
# ============================================

@app.route('/')
def index():
    """Render the main dashboard"""
    return render_template('dashboard.html')

@app.route('/favicon.ico')
def favicon():
    """Return empty favicon to avoid 404 errors"""
    return '', 204

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint with detailed status"""
    try:
        from app.model_manager import model_manager
        
        # Test all providers
        provider_status = model_manager.test_providers()
        available = [p for p, v in provider_status.items() if v]
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'api_keys_valid': validate_api_keys(),
            'python_version': sys.version,
            'secret_key_valid': len(app.secret_key) >= 32,
            'providers': {
                'available': available,
                'total': len(provider_status),
                'status': provider_status,
                'limits': model_manager.get_daily_limits()
            },
            'server': {
                'host': os.getenv('HOST', 'localhost'),
                'port': int(os.environ.get('PORT', 5000))
            }
        })
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/api/providers', methods=['GET'])
def get_providers():
    """Get list of all configured providers"""
    try:
        from app.model_manager import model_manager
        
        # Test providers
        provider_status = model_manager.test_providers()
        limits = model_manager.get_daily_limits()
        
        providers = []
        for name, available in provider_status.items():
            info = model_manager.providers.get(name, {})
            limit_info = limits.get(name, {})
            providers.append({
                'name': name,
                'provider_name': info.get('provider_name', name),
                'model': info.get('model', 'N/A'),
                'available': available,
                'daily_limit': limit_info.get('daily_limit', 'Unknown'),
                'rpm': limit_info.get('rpm', 'Unknown')
            })
        
        return jsonify({
            'status': 'success',
            'providers': providers,
            'available_count': sum(1 for p in providers if p['available']),
            'total_count': len(providers),
            'strategy': os.getenv('MODEL_FALLBACK_STRATEGY', 'sequential')
        })
        
    except Exception as e:
        logger.error(f"Error getting providers: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/search_jobs', methods=['POST'])
@limiter.limit("10/hour")
def search_jobs():
    """Search for jobs based on criteria"""
    try:
        logger.info("=" * 50)
        logger.info("Received job search request")
        
        # Get and validate input
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'No data provided',
                'status': 'error'
            }), 400
        
        role = bleach.clean(data.get('role', '').strip())
        location = bleach.clean(data.get('location', '').strip())
        
        if not role:
            role = os.getenv('JOB_SEARCH_KEYWORDS', 'Python Developer').split(',')[0].strip()
        
        if not location:
            location = os.getenv('JOB_LOCATION', 'Remote')
        
        logger.info(f"Searching for: {role} in {location}")
        
        # Validate API keys
        if not validate_api_keys():
            return jsonify({
                'error': 'No API keys configured. Please add at least one provider.',
                'status': 'error'
            }), 500
        
        # Search for jobs
        from app.job_scraper import JobScraper
        scraper = JobScraper()
        jobs = scraper.search_jobs([role])
        
        # Filter by location if specified
        if location and location.lower() != 'remote':
            jobs = [j for j in jobs if location.lower() in j.get('location', '').lower()]
        
        logger.info(f"Found {len(jobs)} jobs")
        
        return jsonify({
            'status': 'success',
            'jobs': jobs,
            'count': len(jobs),
            'search_criteria': {
                'role': role,
                'location': location
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error searching jobs: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': f'Error searching jobs: {str(e)}',
            'status': 'error'
        }), 500

@app.route('/api/process_job', methods=['POST'])
@limiter.limit("50/day")
def process_job():
    """Process a job application (customize resume + draft email)"""
    try:
        logger.info("=" * 50)
        logger.info("Received job processing request")
        
        # Get and validate input
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'No data provided',
                'status': 'error'
            }), 400
        
        job = data.get('job')
        resume_content = data.get('resume_content')
        
        if not job:
            return jsonify({
                'error': 'Missing job data',
                'status': 'error'
            }), 400
        
        if not resume_content:
            # Try to load from template
            template_path = os.getenv('RESUME_TEMPLATE_PATH', './data/resumes/template.md')
            try:
                with open(template_path, 'r') as f:
                    resume_content = f.read()
                logger.info("Loaded resume from template")
            except FileNotFoundError:
                return jsonify({
                    'error': 'Resume content not provided and template not found',
                    'status': 'error'
                }), 400
        
        logger.info(f"Processing job: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")
        
        # Validate API keys
        if not validate_api_keys():
            return jsonify({
                'error': 'No API keys configured',
                'status': 'error'
            }), 500
        
        # Process the job using CrewAI
        from app.crew import JobSearchCrew
        crew = JobSearchCrew()
        
        result = crew.process_job_application(
            job.get('title', ''),
            job.get('location', 'Remote'),
            resume_content
        )
        
        logger.info("Job processing completed successfully")
        
        return jsonify({
            'status': 'success',
            'result': result,
            'job': job,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error processing job: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': f'Error processing job: {str(e)}',
            'status': 'error'
        }), 500

@app.route('/api/process_multiple_jobs', methods=['POST'])
@limiter.limit("20/day")
def process_multiple_jobs():
    """Process multiple job applications"""
    try:
        logger.info("=" * 50)
        logger.info("Received multiple job processing request")
        
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'No data provided',
                'status': 'error'
            }), 400
        
        jobs = data.get('jobs', [])
        resume_content = data.get('resume_content')
        
        if not jobs:
            return jsonify({
                'error': 'No jobs provided',
                'status': 'error'
            }), 400
        
        # Limit to 5 jobs at a time to avoid rate limits
        if len(jobs) > 5:
            jobs = jobs[:5]
            logger.warning(f"Limiting to first 5 jobs")
        
        # Load resume if not provided
        if not resume_content:
            template_path = os.getenv('RESUME_TEMPLATE_PATH', './data/resumes/template.md')
            try:
                with open(template_path, 'r') as f:
                    resume_content = f.read()
            except FileNotFoundError:
                return jsonify({
                    'error': 'Resume content not provided and template not found',
                    'status': 'error'
                }), 400
        
        # Process each job
        from app.crew import JobSearchCrew
        crew = JobSearchCrew()
        
        results = []
        for job in jobs:
            try:
                logger.info(f"Processing job: {job.get('title', 'Unknown')}")
                result = crew.process_job_application(
                    job.get('title', ''),
                    job.get('location', 'Remote'),
                    resume_content
                )
                results.append({
                    'job': job,
                    'status': 'success',
                    'result': result
                })
            except Exception as e:
                logger.error(f"Error processing job {job.get('title', 'Unknown')}: {str(e)}")
                results.append({
                    'job': job,
                    'status': 'failed',
                    'error': str(e)
                })
        
        return jsonify({
            'status': 'success',
            'results': results,
            'total': len(results),
            'successful': sum(1 for r in results if r['status'] == 'success'),
            'failed': sum(1 for r in results if r['status'] == 'failed'),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error processing multiple jobs: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/run_scheduled_search', methods=['POST'])
def run_scheduled_search():
    """Run the scheduled job search (for cron/automation)"""
    try:
        logger.info("Running scheduled job search...")
        
        # Run the scheduler
        from app.scheduler import JobScheduler
        scheduler = JobScheduler()
        result = scheduler.run_job_search()
        
        return jsonify({
            'status': 'success',
            'result': result,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error running scheduled search: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/resume/template', methods=['GET'])
def get_resume_template():
    """Get the current resume template"""
    try:
        template_path = os.getenv('RESUME_TEMPLATE_PATH', './data/resumes/template.md')
        
        # Create template if it doesn't exist
        os.makedirs(os.path.dirname(template_path), exist_ok=True)
        
        if not os.path.exists(template_path):
            # Create default template
            default_template = """# [Your Name]
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

## Education

### [University Name] - [Location]
**[Degree]** | [Year]
- [Relevant coursework]

## Projects

### [Project Name]
- [Description]
- [Technologies used]"""
            
            with open(template_path, 'w') as f:
                f.write(default_template)
            logger.info("Created default resume template")
        
        with open(template_path, 'r') as f:
            content = f.read()
        
        return jsonify({
            'status': 'success',
            'content': content,
            'path': template_path
        })
        
    except Exception as e:
        logger.error(f"Error getting resume template: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/resume/template', methods=['POST'])
def update_resume_template():
    """Update the resume template"""
    try:
        data = request.get_json()
        content = data.get('content')
        
        if not content:
            return jsonify({
                'error': 'No content provided',
                'status': 'error'
            }), 400
        
        template_path = os.getenv('RESUME_TEMPLATE_PATH', './data/resumes/template.md')
        os.makedirs(os.path.dirname(template_path), exist_ok=True)
        
        with open(template_path, 'w') as f:
            f.write(content)
        
        logger.info("Resume template updated")
        
        return jsonify({
            'status': 'success',
            'message': 'Template updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating resume template: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get application statistics"""
    try:
        from app.model_manager import model_manager
        
        # Get provider status
        provider_status = model_manager.test_providers()
        available = [p for p, v in provider_status.items() if v]
        
        # Get last run status
        last_run = None
        try:
            with open('./data/last_run.json', 'r') as f:
                last_run = json.load(f)
        except FileNotFoundError:
            pass
        
        return jsonify({
            'status': 'success',
            'stats': {
                'providers': {
                    'available': available,
                    'total': len(provider_status),
                    'status': provider_status
                },
                'last_run': last_run,
                'server_start': datetime.utcnow().isoformat(),
                'job_search_interval': os.getenv('JOB_SEARCH_INTERVAL', '24') + ' hours'
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Resource not found',
        'status': 'error'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'error': 'Internal server error',
        'status': 'error'
    }), 500

@app.errorhandler(429)
def rate_limit_error(error):
    """Handle rate limit errors"""
    return jsonify({
        'error': 'Rate limit exceeded. Please try again later.',
        'status': 'error'
    }), 429

# ============================================
# BACKGROUND TASKS
# ============================================

def start_scheduler():
    """Start the background scheduler"""
    try:
        from app.scheduler import JobScheduler
        scheduler = JobScheduler()
        logger.info("Background scheduler started")
        return scheduler
    except Exception as e:
        logger.error(f"Failed to start scheduler: {str(e)}")
        return None

# ============================================
# APPLICATION STARTUP
# ============================================

if __name__ == '__main__':
    logger.info("=" * 70)
    logger.info("🤖 AUTOMATED JOB SEARCH AGENT")
    logger.info("=" * 70)
    logger.info(f"Current directory: {os.getcwd()}")
    
    # Check SECRET_KEY
    if app.secret_key:
        logger.info(f"SECRET_KEY length: {len(app.secret_key)} characters")
        if len(app.secret_key) >= 32:
            logger.info("✅ SECRET_KEY is properly configured")
        else:
            logger.warning("⚠️ SECRET_KEY is less than 32 characters")
    else:
        logger.error("❌ SECRET_KEY is not configured!")
    
    # Validate API keys
    if not validate_api_keys():
        logger.warning("⚠️ No API keys configured! Please add at least one provider.")
        logger.warning("Available providers: Gemini, Groq, GitHub Models, Cerebras")
    
    # Test provider availability
    try:
        from app.model_manager import model_manager
        
        logger.info("\n📊 Testing provider availability...")
        provider_status = model_manager.test_providers()
        
        available = [p for p, v in provider_status.items() if v]
        unavailable = [p for p, v in provider_status.items() if not v]
        
        if available:
            logger.info(f"✅ Available providers: {', '.join(available)}")
        else:
            logger.warning("❌ No providers available! Please check your API keys.")
        
        if unavailable:
            logger.warning(f"⚠️ Unavailable providers: {', '.join(unavailable)}")
            
        # Show daily limits
        limits = model_manager.get_daily_limits()
        logger.info("\n📊 Daily Limits:")
        for provider, info in limits.items():
            if provider in available:
                logger.info(f"  ✅ {info.get('provider', provider)}: {info.get('daily_limit', 'Unknown')} req/day")
        
    except Exception as e:
        logger.error(f"Error testing providers: {str(e)}")
    
    # Start background scheduler
    scheduler = start_scheduler()
    
    # Server configuration
    port = int(os.environ.get('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    host = os.getenv('HOST', '0.0.0.0')
    
    logger.info(f"\n🚀 Starting server on {host}:{port} (debug={debug})")
    logger.info("=" * 70)
    logger.info("📊 Dashboard: http://localhost:5000")
    logger.info("📋 Health Check: http://localhost:5000/api/health")
    logger.info("🔍 Providers: http://localhost:5000/api/providers")
    logger.info("=" * 70)
    
    # Run the application
    app.run(host=host, port=port, debug=debug)