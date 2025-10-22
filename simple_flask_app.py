#!/usr/bin/env python3
"""
Simple Flask Web App for Profile Scraper
Minimal version that should work without issues
"""

from flask import Flask, request, jsonify, render_template_string
import threading
from working_scraper import WorkingScraper

app = Flask(__name__)

# Store search results
search_results = {}

# Simple HTML template
TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Profile Scraper</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; }
        input, button { padding: 10px; margin: 5px; border: 1px solid #ddd; border-radius: 5px; }
        input { width: 300px; }
        button { background: #007bff; color: white; border: none; cursor: pointer; }
        button:hover { background: #0056b3; }
        .result { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; background: #f9f9f9; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .searching { background: #fff3cd; border: 1px solid #ffeaa7; }
        .success { background: #d4edda; border: 1px solid #c3e6cb; }
        .error { background: #f8d7da; border: 1px solid #f5c6cb; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Profile Scraper</h1>
        <form id="searchForm">
            <input type="text" id="keyword" placeholder="Enter search keyword (e.g., John Smith developer)" required>
            <button type="submit">Search</button>
        </form>
        <div id="status"></div>
        <div id="results"></div>
    </div>

    <script>
        document.getElementById('searchForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const keyword = document.getElementById('keyword').value.trim();
            if (!keyword) return;
            
            document.getElementById('status').innerHTML = '<div class="status searching">🔍 Searching for profiles...</div>';
            document.getElementById('results').innerHTML = '';
            
            fetch('/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ keyword: keyword })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displayResults(data.results);
                } else {
                    document.getElementById('status').innerHTML = '<div class="status error">❌ Error: ' + data.error + '</div>';
                }
            })
            .catch(error => {
                document.getElementById('status').innerHTML = '<div class="status error">❌ Error: ' + error + '</div>';
            });
        });
        
        function displayResults(results) {
            if (!results.profiles || results.profiles.length === 0) {
                document.getElementById('status').innerHTML = '<div class="status error">❌ No profiles found</div>';
                return;
            }
            
            document.getElementById('status').innerHTML = '<div class="status success">✅ Found ' + results.total_profiles + ' profiles!</div>';
            
            let html = '<h2>Search Results</h2>';
            results.profiles.forEach(function(profile, index) {
                html += '<div class="result">';
                html += '<h3>' + (profile.name || 'Unknown') + '</h3>';
                html += '<p><strong>Platform:</strong> ' + profile.platform + '</p>';
                html += '<p><strong>URL:</strong> <a href="' + profile.url + '" target="_blank">' + profile.url + '</a></p>';
                
                if (profile.emails && profile.emails.length > 0) {
                    html += '<p><strong>📧 Emails:</strong> ' + profile.emails.join(', ') + '</p>';
                }
                
                if (profile.phones && profile.phones.length > 0) {
                    html += '<p><strong>📞 Phones:</strong> ' + profile.phones.join(', ') + '</p>';
                }
                
                html += '</div>';
            });
            
            document.getElementById('results').innerHTML = html;
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(TEMPLATE)

@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        keyword = data.get('keyword', '').strip()
        
        if not keyword:
            return jsonify({'success': False, 'error': 'Keyword is required'})
        
        # Perform search
        scraper = WorkingScraper()
        results = scraper.search_profiles(keyword)
        
        return jsonify({'success': True, 'results': results})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("🌐 Starting Profile Scraper Web App")
    print("🔗 Open your browser and visit: http://localhost:5000")
    print("📝 Enter keywords like 'John Smith developer' to search")
    print("-" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=False)