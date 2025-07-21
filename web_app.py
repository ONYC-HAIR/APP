from flask import Flask, render_template, request, jsonify, send_file
import asyncio
import threading
import uuid
from typing import Dict
import os
import json
from datetime import datetime

from scraper import ScrapingJob, scraper
from database import db
from config import config

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

# Store active jobs
active_jobs: Dict[str, ScrapingJob] = {}

@app.route('/')
def index():
    """Main page with search form."""
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def start_search():
    """Start a new scraping job."""
    data = request.get_json()
    keyword = data.get('keyword', '').strip()
    platforms = data.get('platforms', [])
    
    if not keyword:
        return jsonify({'error': 'Keyword is required'}), 400
    
    # Create new job
    job_id = str(uuid.uuid4())
    job = ScrapingJob(keyword, platforms)
    active_jobs[job_id] = job
    
    # Start job in background thread
    def run_job():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(job.run())
        loop.close()
    
    thread = threading.Thread(target=run_job)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'job_id': job_id,
        'status': 'started',
        'keyword': keyword,
        'platforms': platforms
    })

@app.route('/status/<job_id>')
def get_job_status(job_id):
    """Get status of a scraping job."""
    if job_id not in active_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = active_jobs[job_id]
    status = job.get_status()
    
    # Clean up completed jobs
    if status['status'] in ['completed', 'failed']:
        del active_jobs[job_id]
    
    return jsonify(status)

@app.route('/results/<int:search_id>')
def get_results(search_id):
    """Get results for a completed search."""
    results = scraper.get_search_results(search_id)
    if not results:
        return jsonify({'error': 'Results not found'}), 404
    
    return jsonify(results)

@app.route('/searches')
def get_all_searches():
    """Get all search sessions."""
    searches = scraper.get_all_searches()
    return jsonify(searches)

@app.route('/export/<int:search_id>')
def export_results(search_id):
    """Export search results as CSV."""
    filename = f"search_results_{search_id}_{int(datetime.now().timestamp())}.csv"
    
    if scraper.export_results(search_id, 'csv'):
        return send_file(filename, as_attachment=True)
    else:
        return jsonify({'error': 'Export failed'}), 500

@app.route('/dashboard')
def dashboard():
    """Dashboard page showing all searches."""
    return render_template('dashboard.html')

@app.route('/api/config')
def get_config():
    """Get configuration information."""
    return jsonify({
        'search_engines': config.SEARCH_ENGINES,
        'social_platforms': config.SOCIAL_PLATFORMS,
        'max_results': config.MAX_RESULTS_PER_SEARCH
    })

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)