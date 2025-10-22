#!/usr/bin/env python3
"""
Simplified Profile Scraper Demo
A basic version that works without Selenium dependencies
"""

import asyncio
import aiohttp
import time
import re
import logging
from typing import List, Dict
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin
import requests
from fake_useragent import UserAgent

# Simple configuration
class SimpleConfig:
    REQUEST_DELAY = 2.0
    TIMEOUT = 10
    MAX_RESULTS = 10
    
    # Email and phone patterns
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    PHONE_PATTERNS = [
        r'\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',  # US
        r'\(\d{3}\)\s?\d{3}-\d{4}',  # (123) 456-7890
        r'\d{3}-\d{3}-\d{4}',  # 123-456-7890
    ]

config = SimpleConfig()

class SimpleExtractor:
    """Simple data extractor for emails and phones."""
    
    def __init__(self):
        self.email_pattern = re.compile(config.EMAIL_PATTERN, re.IGNORECASE)
        self.phone_patterns = [re.compile(pattern) for pattern in config.PHONE_PATTERNS]
    
    def extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from text."""
        emails = set()
        matches = self.email_pattern.findall(text)
        
        for email in matches:
            email = email.lower().strip()
            # Skip obvious false positives
            if not any(skip in email for skip in ['example.com', 'test.com', 'localhost']):
                emails.add(email)
        
        return list(emails)
    
    def extract_phones(self, text: str) -> List[str]:
        """Extract phone numbers from text."""
        phones = set()
        
        for pattern in self.phone_patterns:
            matches = pattern.findall(text)
            for match in matches:
                if isinstance(match, tuple):
                    phone = ''.join(match)
                else:
                    phone = match
                
                # Clean and validate
                phone_clean = re.sub(r'[^\d]', '', phone)
                if len(phone_clean) >= 10:
                    phones.add(phone)
        
        return list(phones)

class SimpleSearchEngine:
    """Simple search engine using requests."""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
    
    def search_duckduckgo(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search DuckDuckGo (more permissive than Google)."""
        results = []
        
        try:
            # DuckDuckGo HTML search
            url = "https://html.duckduckgo.com/html/"
            params = {'q': query}
            headers = {'User-Agent': self.ua.random}
            
            print(f"🔍 Searching DuckDuckGo for: {query}")
            
            response = self.session.get(url, params=params, headers=headers, timeout=config.TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract results
            result_containers = soup.find_all('div', class_='result')
            
            for container in result_containers[:max_results]:
                try:
                    link_element = container.find('a', class_='result__a')
                    if link_element and link_element.get('href'):
                        title = link_element.get_text(strip=True)
                        url = link_element['href']
                        
                        # Get description
                        desc_element = container.find('a', class_='result__snippet')
                        description = desc_element.get_text(strip=True) if desc_element else ''
                        
                        results.append({
                            'title': title,
                            'url': url,
                            'description': description,
                            'source': 'duckduckgo'
                        })
                except Exception as e:
                    continue
            
            print(f"✅ Found {len(results)} results")
            return results
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return []

class SimpleProfileScraper:
    """Simple profile scraper."""
    
    def __init__(self):
        self.search_engine = SimpleSearchEngine()
        self.extractor = SimpleExtractor()
        self.session = requests.Session()
        self.ua = UserAgent()
    
    def scrape_profiles(self, keyword: str) -> Dict:
        """Main scraping method."""
        print(f"\n🎯 Starting profile search for: '{keyword}'")
        
        # Step 1: Search for profile URLs
        queries = [
            f'site:linkedin.com/in {keyword}',
            f'site:github.com {keyword}',
            f'{keyword} email contact',
            f'{keyword} profile'
        ]
        
        all_results = []
        for query in queries:
            results = self.search_engine.search_duckduckgo(query, max_results=5)
            all_results.extend(results)
            time.sleep(config.REQUEST_DELAY)  # Rate limiting
        
        # Step 2: Filter unique profile URLs
        profile_urls = self._filter_profile_urls(all_results)
        print(f"📊 Found {len(profile_urls)} unique profile URLs")
        
        # Step 3: Scrape individual profiles
        scraped_profiles = []
        for i, url_data in enumerate(profile_urls[:config.MAX_RESULTS]):
            print(f"🔗 Scraping profile {i+1}/{len(profile_urls[:config.MAX_RESULTS])}: {url_data['url']}")
            
            profile = self._scrape_single_profile(url_data)
            if profile:
                scraped_profiles.append(profile)
            
            time.sleep(config.REQUEST_DELAY)  # Rate limiting
        
        return {
            'keyword': keyword,
            'total_profiles': len(scraped_profiles),
            'profiles': scraped_profiles
        }
    
    def _filter_profile_urls(self, results: List[Dict]) -> List[Dict]:
        """Filter and deduplicate profile URLs."""
        unique_urls = {}
        
        for result in results:
            url = result.get('url', '')
            
            # Check if it looks like a profile URL
            if self._is_profile_url(url) and url not in unique_urls:
                unique_urls[url] = result
        
        return list(unique_urls.values())
    
    def _is_profile_url(self, url: str) -> bool:
        """Check if URL looks like a profile."""
        if not url:
            return False
        
        url_lower = url.lower()
        
        # Profile indicators
        profile_indicators = [
            'linkedin.com/in/', 'github.com/', 'twitter.com/',
            'profile', 'about', 'contact'
        ]
        
        # Skip non-profile patterns
        skip_patterns = [
            '/search', '/login', '/help', '.pdf', '.jpg', '.png'
        ]
        
        if any(skip in url_lower for skip in skip_patterns):
            return False
        
        return any(indicator in url_lower for indicator in profile_indicators)
    
    def _scrape_single_profile(self, url_data: Dict) -> Dict:
        """Scrape a single profile URL."""
        url = url_data['url']
        
        try:
            headers = {'User-Agent': self.ua.random}
            response = self.session.get(url, headers=headers, timeout=config.TIMEOUT)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                text_content = soup.get_text()
                
                # Extract basic profile info
                profile = {
                    'name': self._extract_name(soup, url),
                    'url': url,
                    'title': url_data.get('title', ''),
                    'description': url_data.get('description', ''),
                    'platform': self._detect_platform(url),
                    'emails': self.extractor.extract_emails(text_content),
                    'phones': self.extractor.extract_phones(text_content)
                }
                
                return profile
            
        except Exception as e:
            print(f"⚠️  Failed to scrape {url}: {e}")
        
        return None
    
    def _extract_name(self, soup: BeautifulSoup, url: str) -> str:
        """Try to extract name from page."""
        # Try common name selectors
        selectors = ['h1', 'h2', '.name', '.profile-name', 'title']
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text and len(text) < 100:  # Reasonable name length
                    return text
        
        return "Unknown"
    
    def _detect_platform(self, url: str) -> str:
        """Detect social media platform."""
        url_lower = url.lower()
        
        if 'linkedin.com' in url_lower:
            return 'linkedin'
        elif 'github.com' in url_lower:
            return 'github'
        elif 'twitter.com' in url_lower:
            return 'twitter'
        else:
            return 'other'

def print_results(results: Dict):
    """Print search results in a nice format."""
    print(f"\n{'='*60}")
    print(f"🎉 SEARCH RESULTS FOR '{results['keyword'].upper()}'")
    print(f"{'='*60}")
    
    if not results['profiles']:
        print("❌ No profiles found.")
        return
    
    print(f"📊 Found {results['total_profiles']} profiles\n")
    
    for i, profile in enumerate(results['profiles'], 1):
        print(f"👤 Profile {i}")
        print(f"   Name: {profile['name']}")
        print(f"   Platform: {profile['platform']}")
        print(f"   URL: {profile['url']}")
        
        if profile['emails']:
            print(f"   📧 Emails: {', '.join(profile['emails'])}")
        
        if profile['phones']:
            print(f"   📞 Phones: {', '.join(profile['phones'])}")
        
        print()

def main():
    """Main demo function."""
    print("🔍 SIMPLE PROFILE SCRAPER DEMO")
    print("=" * 50)
    print("This is a simplified version that works without Selenium.")
    print("It searches for publicly available profile information.\n")
    
    # Get search keyword
    keyword = input("Enter a keyword to search for (e.g., 'John Smith developer'): ").strip()
    
    if not keyword:
        print("❌ Please provide a keyword.")
        return
    
    # Create scraper and run search
    scraper = SimpleProfileScraper()
    results = scraper.scrape_profiles(keyword)
    
    # Display results
    print_results(results)
    
    print("\n💡 Tips:")
    print("- Try specific keywords like 'John Smith software engineer'")
    print("- Results depend on what's publicly available")
    print("- Be respectful of rate limits and website terms")

if __name__ == '__main__':
    main()