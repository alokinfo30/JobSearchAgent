import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import secrets
import bleach
from datetime import datetime
import traceback
import json

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, 
    template_folder='../templates',
    static_folder='../static'
)

app.secret_key = os.getenv('SECRET_KEY')
if not app.secret_key:
    app.secret_key = secrets.token_urlsafe(32)
    logger.warning(f"Generated temporary SECRET_KEY")

app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
app.config['SESSION_COOKIE_HTTPONLY'] = os.getenv('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
app.config['SESSION_COOKIE_SAMESITE'] = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')

CORS(app, resources={r"/api/*": {"origins": "*"}})

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[os.getenv('RATELIMIT_DEFAULT', '100/day')],
    enabled=os.getenv('RATELIMIT_ENABLED', 'False').lower() == 'true'
)

def validate_openrouter():
    """Validate OpenRouter configuration"""
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        logger.error("OPENROUTER_API_KEY not found")
        return False
    if not api_key.startswith('sk-or-'):
        logger.error("Invalid OpenRouter API key format")
        return False
    logger.info("✅ OpenRouter API key validated")
    return True

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        from app.model_manager import model_manager
        
        model_status = model_manager.test_providers()
        available = [m for m, v in model_status.items() if v]
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'openrouter_valid': validate_openrouter(),
            'python_version': sys.version,
            'providers': {
                'available': available,
                'total': len(model_status),
                'status': model_status
            },
            'free_models': model_manager.get_daily_limits()
        })
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/api/search_jobs', methods=['POST'])
@limiter.limit("10/hour")
def search_jobs():
    """Search for jobs based on criteria"""
    try:
        logger.info("=" * 50)
        logger.info("Received job search request")
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        role = bleach.clean(data.get('role', '').strip())
        location = bleach.clean(data.get('location', '').strip())
        
        if not role:
            role = os.getenv('JOB_SEARCH_KEYWORDS', 'Python Developer').split(',')[0].strip()
        if not location:
            location = os.getenv('JOB_LOCATION', 'Remote')
        
        if not validate_openrouter():
            return jsonify({
                'error': 'OpenRouter not configured',
                'status': 'error'
            }), 500
        
        from app.job_scraper import JobScraper
        scraper = JobScraper()
        jobs = scraper.search_jobs([role])
        
        return jsonify({
            'status': 'success',
            'jobs': jobs,
            'count': len(jobs),
            'search_criteria': {'role': role, 'location': location},
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error searching jobs: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/process_job', methods=['POST'])
@limiter.limit("50/day")
def process_job():
    """Process a job application"""
    try:
        data = request.get_json()
        job = data.get('job')
        resume_content = data.get('resume_content')
        
        if not job:
            return jsonify({'error': 'Missing job data'}), 400
        
        if not resume_content:
            template_path = os.getenv('RESUME_TEMPLATE_PATH', './data/resumes/template.md')
            try:
                with open(template_path, 'r') as f:
                    resume_content = f.read()
            except FileNotFoundError:
                return jsonify({'error': 'Resume not found'}), 400
        
        from app.crew import JobSearchCrew
        crew = JobSearchCrew()
        
        result = crew.process_job_application(
            job.get('title', ''),
            job.get('location', 'Remote'),
            resume_content
        )
        
        return jsonify({
            'status': 'success',
            'result': result,
            'job': job,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error processing job: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("🤖 JOB SEARCH AGENT (OpenRouter)")
    logger.info("=" * 60)
    
    if not validate_openrouter():
        logger.warning("⚠️ OpenRouter not configured. Get API key from: https://openrouter.ai/keys")
    
    try:
        from app.model_manager import model_manager
        model_status = model_manager.test_providers()
        available = [m for m, v in model_status.items() if v]
        if available:
            logger.info(f"✅ Available models: {available}")
        else:
            logger.warning("❌ No models available! Check your OpenRouter API key.")
    except Exception as e:
        logger.error(f"Error testing models: {str(e)}")
    
    port = int(os.environ.get('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)