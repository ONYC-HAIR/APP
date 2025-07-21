import os
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class ScraperConfig:
    """Configuration class for the scraper application."""
    
    # Rate limiting
    REQUEST_DELAY = 2.0  # Seconds between requests
    MAX_CONCURRENT_REQUESTS = 3
    TIMEOUT = 30
    
    # Search settings
    MAX_RESULTS_PER_SEARCH = 50
    MAX_PAGES_TO_SCRAPE = 5
    
    # User agents rotation
    USE_RANDOM_USER_AGENT = True
    
    # Database settings
    DATABASE_PATH = "scraper_results.db"
    
    # Search engines to use
    SEARCH_ENGINES = ["google", "bing", "duckduckgo"]
    
    # Social media platforms to scrape
    SOCIAL_PLATFORMS = ["linkedin", "twitter", "github", "facebook", "instagram"]
    
    # File export formats
    EXPORT_FORMATS = ["csv", "json", "xlsx"]
    
    # Regex patterns for data extraction
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    PHONE_PATTERNS = [
        r'\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',  # US
        r'\+?[1-9]\d{1,14}',  # International
        r'\(\d{3}\)\s?\d{3}-\d{4}',  # (123) 456-7890
        r'\d{3}-\d{3}-\d{4}',  # 123-456-7890
        r'\d{10}',  # 1234567890
    ]
    
    # Headers for requests
    DEFAULT_HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    # Search query templates
    SEARCH_TEMPLATES = {
        'linkedin': 'site:linkedin.com/in {keyword}',
        'twitter': 'site:twitter.com {keyword}',
        'github': 'site:github.com {keyword}',
        'facebook': 'site:facebook.com {keyword}',
        'email': '"{keyword}" email contact',
        'phone': '"{keyword}" phone contact',
        'general': '{keyword} profile contact information'
    }
    
    # Selenium settings
    SELENIUM_TIMEOUT = 10
    HEADLESS_BROWSER = True
    
    # Output settings
    OUTPUT_DIR = "scraped_data"
    LOG_LEVEL = "INFO"
    
    @classmethod
    def load_from_env(cls):
        """Load configuration from environment variables."""
        config = cls()
        
        # Override with environment variables if they exist
        config.REQUEST_DELAY = float(os.getenv('SCRAPER_REQUEST_DELAY', config.REQUEST_DELAY))
        config.MAX_RESULTS_PER_SEARCH = int(os.getenv('SCRAPER_MAX_RESULTS', config.MAX_RESULTS_PER_SEARCH))
        config.HEADLESS_BROWSER = os.getenv('SCRAPER_HEADLESS', 'true').lower() == 'true'
        config.DATABASE_PATH = os.getenv('SCRAPER_DB_PATH', config.DATABASE_PATH)
        
        return config

# Create global config instance
config = ScraperConfig.load_from_env()