# Profile Scraper

A comprehensive web scraping application that collects public user profile information (URLs, emails, and phone numbers) based on keyword searches. The scraper searches across multiple search engines and social media platforms to find publicly available contact information.

## 🌟 Features

- **Multi-Platform Search**: Searches across LinkedIn, Twitter, GitHub, Facebook, Instagram, and more
- **Multiple Search Engines**: Utilizes Google, Bing, and DuckDuckGo for comprehensive coverage
- **Contact Extraction**: Automatically extracts emails and phone numbers from profile pages
- **Web Interface**: Modern, responsive web UI for easy interaction
- **Command Line Interface**: Full CLI support for automation and scripting
- **Database Storage**: SQLite database for persistent storage and history
- **Export Functionality**: Export results to CSV format
- **Rate Limiting**: Respectful scraping with configurable delays
- **Async Processing**: High-performance asynchronous scraping
- **Selenium Fallback**: Handles JavaScript-heavy sites

## 🚀 Quick Start

### Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd profile-scraper
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment** (optional):
```bash
cp .env.example .env
# Edit .env with your preferred settings
```

### Web Interface

1. **Start the web application**:
```bash
python web_app.py
```

2. **Open your browser** and navigate to `http://localhost:5000`

3. **Enter a keyword** (e.g., "John Smith software engineer") and start scraping!

### Command Line Interface

```bash
# Basic search
python cli.py "Jane Doe data scientist"

# Target specific platforms
python cli.py --platforms linkedin github "software engineer Python"

# Limit results and export
python cli.py --limit 10 "marketing manager" --verbose

# View previous searches
python cli.py --list-searches

# Export results
python cli.py --export 1 --format csv
```

## 🔧 Configuration

The application can be configured through environment variables or the `config.py` file:

### Key Settings

- `REQUEST_DELAY`: Delay between requests (default: 2.0 seconds)
- `MAX_RESULTS_PER_SEARCH`: Maximum results per search (default: 50)
- `SEARCH_ENGINES`: Search engines to use (google, bing, duckduckgo)
- `HEADLESS_BROWSER`: Run browser in headless mode (default: true)
- `MAX_CONCURRENT_REQUESTS`: Concurrent request limit (default: 3)

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
SCRAPER_REQUEST_DELAY=2.0
SCRAPER_MAX_RESULTS=50
SCRAPER_HEADLESS=true
SCRAPER_DB_PATH=scraper_results.db
```

## 📊 Usage Examples

### Web Interface Examples

1. **Search for professionals**: "software engineer machine learning"
2. **Find company employees**: "Google software engineer"
3. **Target specific locations**: "data scientist San Francisco"
4. **Industry-specific searches**: "marketing manager fintech"

### CLI Examples

```bash
# Basic keyword search
python cli.py "John Smith"

# Platform-specific search
python cli.py --platforms linkedin "data scientist"

# Verbose output with limited results
python cli.py --verbose --limit 5 "marketing manager"

# JSON output for scripting
python cli.py --json "software engineer" > results.json

# Database operations
python cli.py --list-searches
python cli.py --view-results 1
python cli.py --export 1 --format csv
```

## 🗃️ Database Schema

The application uses SQLite with the following structure:

- **searches**: Search sessions and metadata
- **profiles**: Profile information (name, title, company, etc.)
- **contacts**: Contact information (emails and phone numbers)

## 📁 Project Structure

```
profile-scraper/
├── config.py              # Configuration settings
├── database.py             # Database operations
├── data_extractor.py       # Email/phone extraction logic
├── search_engines.py       # Search engine implementations
├── scraper.py             # Main scraper logic
├── web_app.py             # Flask web application
├── cli.py                 # Command line interface
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── templates/            # HTML templates
│   ├── index.html       # Main search interface
│   └── dashboard.html   # Results dashboard
└── README.md            # This file
```

## 🔍 How It Works

1. **Keyword Processing**: Takes user keywords and generates optimized search queries
2. **Multi-Engine Search**: Searches across Google, Bing, and DuckDuckGo simultaneously
3. **URL Filtering**: Identifies and filters profile URLs from search results
4. **Content Extraction**: Scrapes profile pages and extracts information
5. **Contact Detection**: Uses regex patterns and validation to find emails/phones
6. **Data Storage**: Stores results in SQLite database with confidence scores
7. **Result Presentation**: Displays results in web UI or CLI with export options

## ⚖️ Ethics and Legal Considerations

This tool is designed for legitimate research and networking purposes only:

- ✅ **Respects robots.txt** and rate limits
- ✅ **Only collects publicly available information**
- ✅ **Implements delays to avoid overwhelming servers**
- ✅ **No authentication bypass or private data access**

### Important Notes:

- Always comply with website terms of service
- Respect privacy and data protection laws (GDPR, CCPA, etc.)
- Use responsibly for legitimate business purposes
- Consider the ethical implications of your data collection

## 🔒 Privacy and Security

- No credentials or private data are accessed
- Only publicly available information is collected
- Local database storage (no cloud transmission)
- Configurable rate limiting to be respectful
- User-agent rotation to avoid blocking

## 🛠️ Advanced Usage

### Custom Search Queries

The application supports various search query types:

```python
# In config.py, modify SEARCH_TEMPLATES
SEARCH_TEMPLATES = {
    'linkedin': 'site:linkedin.com/in {keyword}',
    'custom': '{keyword} contact email phone',
    # Add your own templates
}
```

### Selenium Configuration

For JavaScript-heavy sites, configure Selenium options:

```python
# In search_engines.py
chrome_options.add_argument('--window-size=1920,1080')
chrome_options.add_argument('--disable-images')  # Faster loading
```

### Database Queries

Access the database directly for custom analysis:

```python
from database import db

# Get all profiles with emails
profiles = db.get_search_results(search_id)
emails = [p for p in profiles['profiles'] if p.get('contacts', {}).get('email')]
```

## 🚨 Troubleshooting

### Common Issues

1. **ChromeDriver errors**:
   ```bash
   # Install ChromeDriver automatically
   pip install webdriver-manager
   ```

2. **Rate limiting/IP blocking**:
   - Increase `REQUEST_DELAY` in config
   - Use VPN or proxy if necessary
   - Reduce concurrent requests

3. **No results found**:
   - Try different keywords
   - Check if target sites are accessible
   - Enable verbose logging for debugging

4. **Database errors**:
   ```bash
   # Delete and recreate database
   rm scraper_results.db
   python -c "from database import db; print('Database initialized')"
   ```

### Debug Mode

Enable verbose logging:

```bash
python cli.py --verbose "your search term"
```

Or in web mode, check `scraper.log` file.

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Code formatting
black *.py
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This tool is for educational and legitimate research purposes only. Users are responsible for ensuring their use complies with all applicable laws and website terms of service. The authors are not responsible for any misuse of this software.

---

**Happy Scraping! 🕷️**
