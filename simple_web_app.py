#!/usr/bin/env python3
"""
Simple Web Interface for Profile Scraper
Works with available dependencies (no Selenium required)
"""

from flask import Flask, render_template_string, request, jsonify
import threading
import time
from simple_demo import SimpleProfileScraper

app = Flask(__name__)

# Store active searches
active_searches = {}

# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simple Profile Scraper</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        
        h1 {
            text-align: center;
            color: #667eea;
            margin-bottom: 30px;
        }
        
        .search-form {
            margin-bottom: 30px;
        }
        
        input[type="text"] {
            width: 70%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
        }
        
        button {
            width: 25%;
            padding: 12px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            margin-left: 10px;
        }
        
        button:hover {
            opacity: 0.9;
        }
        
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .status {
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            font-weight: bold;
        }
        
        .status.searching {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }
        
        .status.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .status.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .results {
            margin-top: 20px;
        }
        
        .profile {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
            background: #f8f9fa;
        }
        
        .profile h3 {
            margin: 0 0 10px 0;
            color: #667eea;
        }
        
        .profile-info {
            margin: 5px 0;
        }
        
        .contacts {
            margin-top: 10px;
            padding: 10px;
            background: #e9ecef;
            border-radius: 5px;
        }
        
        .contact-item {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            margin: 2px;
            font-size: 12px;
        }
        
        .loading {
            text-align: center;
            padding: 20px;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .warning {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Simple Profile Scraper</h1>
        
        <div class="warning">
            <strong>Demo Version:</strong> This is a simplified version that searches publicly available information. 
            Please use responsibly and respect website terms of service.
        </div>
        
        <form class="search-form" onsubmit="startSearch(event)">
            <input type="text" id="keyword" placeholder="Enter search keyword (e.g., 'John Smith developer')" required>
            <button type="submit" id="searchBtn">Search</button>
        </form>
        
        <div id="status"></div>
        <div id="results"></div>
    </div>

    <script>
        let searchInterval = null;
        
        function startSearch(event) {
            event.preventDefault();
            
            const keyword = document.getElementById('keyword').value.trim();
            if (!keyword) return;
            
            // Update UI
            document.getElementById('searchBtn').disabled = true;
            document.getElementById('results').innerHTML = '';
            showStatus('Searching for profiles...', 'searching');
            
            // Start search
            fetch('/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ keyword: keyword })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const searchId = data.search_id;
                    pollSearchStatus(searchId);
                } else {
                    showStatus('Search failed: ' + data.error, 'error');
                    document.getElementById('searchBtn').disabled = false;
                }
            })
            .catch(error => {
                showStatus('Error starting search: ' + error, 'error');
                document.getElementById('searchBtn').disabled = false;
            });
        }
        
        function pollSearchStatus(searchId) {
            searchInterval = setInterval(() => {
                fetch(`/status/${searchId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'completed') {
                        clearInterval(searchInterval);
                        showResults(data.results);
                        document.getElementById('searchBtn').disabled = false;
                    } else if (data.status === 'failed') {
                        clearInterval(searchInterval);
                        showStatus('Search failed: ' + data.error, 'error');
                        document.getElementById('searchBtn').disabled = false;
                    } else {
                        showStatus('Searching... Found ' + (data.progress || 0) + ' profiles so far', 'searching');
                    }
                })
                .catch(error => {
                    clearInterval(searchInterval);
                    showStatus('Error checking status: ' + error, 'error');
                    document.getElementById('searchBtn').disabled = false;
                });
            }, 2000);
        }
        
        function showStatus(message, type) {
            const statusDiv = document.getElementById('status');
            statusDiv.innerHTML = `<div class="status ${type}">${message}</div>`;
        }
        
        function showResults(results) {
            if (!results || !results.profiles || results.profiles.length === 0) {
                showStatus('No profiles found. Try a different keyword.', 'error');
                return;
            }
            
            showStatus(`Found ${results.total_profiles} profiles!`, 'success');
            
            let html = '<div class="results"><h2>Search Results</h2>';
            
            results.profiles.forEach((profile, index) => {
                html += `
                    <div class="profile">
                        <h3>${profile.name || 'Unknown Name'}</h3>
                        <div class="profile-info"><strong>Platform:</strong> ${profile.platform}</div>
                        <div class="profile-info"><strong>URL:</strong> <a href="${profile.url}" target="_blank">${profile.url}</a></div>
                        ${profile.title ? `<div class="profile-info"><strong>Title:</strong> ${profile.title}</div>` : ''}
                        ${profile.description ? `<div class="profile-info"><strong>Description:</strong> ${profile.description.substring(0, 200)}...</div>` : ''}
                        
                        ${profile.emails && profile.emails.length > 0 || profile.phones && profile.phones.length > 0 ? `
                            <div class="contacts">
                                <strong>Contact Information:</strong><br>
                                ${profile.emails ? profile.emails.map(email => `<span class="contact-item">📧 ${email}</span>`).join('') : ''}
                                ${profile.phones ? profile.phones.map(phone => `<span class="contact-item">📞 ${phone}</span>`).join('') : ''}
                            </div>
                        ` : ''}
                    </div>
                `;
            });
            
            html += '</div>';
            document.getElementById('results').innerHTML = html;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Main page."""
    return render_template_string(HTML_TEMPLATE)

@app.route('/search', methods=['POST'])
def start_search():
    """Start a new search."""
    try:
        data = request.get_json()
        keyword = data.get('keyword', '').strip()
        
        if not keyword:
            return jsonify({'success': False, 'error': 'Keyword is required'})
        
        # Generate search ID
        search_id = f"search_{int(time.time())}"
        
        # Initialize search status
        active_searches[search_id] = {
            'status': 'running',
            'keyword': keyword,
            'results': None,
            'error': None,
            'progress': 0
        }
        
        # Start search in background thread
        def run_search():
            try:
                scraper = SimpleProfileScraper()
                results = scraper.scrape_profiles(keyword)
                
                active_searches[search_id]['status'] = 'completed'
                active_searches[search_id]['results'] = results
                
            except Exception as e:
                active_searches[search_id]['status'] = 'failed'
                active_searches[search_id]['error'] = str(e)
        
        thread = threading.Thread(target=run_search)
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True, 'search_id': search_id})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/status/<search_id>')
def get_search_status(search_id):
    """Get search status."""
    if search_id not in active_searches:
        return jsonify({'status': 'not_found', 'error': 'Search not found'})
    
    search_data = active_searches[search_id]
    
    response = {
        'status': search_data['status'],
        'keyword': search_data['keyword'],
        'progress': search_data['progress']
    }
    
    if search_data['status'] == 'completed':
        response['results'] = search_data['results']
        # Clean up completed search
        del active_searches[search_id]
    elif search_data['status'] == 'failed':
        response['error'] = search_data['error']
        # Clean up failed search
        del active_searches[search_id]
    
    return jsonify(response)

if __name__ == '__main__':
    print("🌐 Starting Simple Profile Scraper Web App")
    print("🔗 Open your browser and go to: http://localhost:5000")
    print("⚠️  This is a demo version - use responsibly!")
    print("-" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)