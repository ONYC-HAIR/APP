#!/usr/bin/env python3
"""
Simple test web app to verify Flask is working
"""

from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Profile Scraper Test</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                text-align: center; 
                padding: 50px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                background: white;
                color: #333;
                padding: 30px;
                border-radius: 15px;
                display: inline-block;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎉 Flask is Working!</h1>
            <p>Your Profile Scraper web server is running successfully.</p>
            <p>This confirms that the web application can serve pages.</p>
            <hr>
            <p><strong>Next:</strong> Try the full scraper app!</p>
        </div>
    </body>
    </html>
    '''

@app.route('/test')
def test():
    return {'status': 'success', 'message': 'API is working'}

if __name__ == '__main__':
    print("🌐 Starting Test Web Server")
    print("🔗 Visit: http://localhost:5000")
    print("🔗 API Test: http://localhost:5000/test")
    print("-" * 40)
    
    app.run(debug=True, host='0.0.0.0', port=5000)