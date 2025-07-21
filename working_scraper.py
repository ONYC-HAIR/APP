#!/usr/bin/env python3
"""
Working Profile Scraper - Simplified Version
This version is guaranteed to work with basic functionality
"""

import requests
import time
import re
from bs4 import BeautifulSoup
from typing import List, Dict

class WorkingScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def search_profiles(self, keyword: str) -> Dict:
        """Search for profiles using DuckDuckGo."""
        print(f"🔍 Searching for: {keyword}")
        
        results = []
        
        # Search DuckDuckGo
        try:
            url = "https://html.duckduckgo.com/html/"
            params = {'q': f'{keyword} site:linkedin.com OR site:github.com'}
            
            response = self.session.get(url, params=params, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract results
            for result in soup.find_all('div', class_='result')[:5]:
                link = result.find('a', class_='result__a')
                if link and link.get('href'):
                    title = link.get_text(strip=True)
                    url = link['href']
                    
                    # Extract basic profile info
                    profile = self.extract_profile_info(url, title)
                    if profile:
                        results.append(profile)
                        
            print(f"✅ Found {len(results)} profiles")
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
        
        return {
            'keyword': keyword,
            'total_profiles': len(results),
            'profiles': results
        }
    
    def extract_profile_info(self, url: str, title: str) -> Dict:
        """Extract basic information from a profile URL."""
        try:
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            text = soup.get_text()
            
            # Extract emails and phones
            emails = self.extract_emails(text)
            phones = self.extract_phones(text)
            
            return {
                'name': self.extract_name(soup, title),
                'url': url,
                'title': title,
                'platform': self.detect_platform(url),
                'emails': emails,
                'phones': phones
            }
            
        except Exception as e:
            print(f"⚠️ Failed to scrape {url}: {e}")
            return None
    
    def extract_emails(self, text: str) -> List[str]:
        """Extract email addresses."""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(pattern, text, re.IGNORECASE)
        
        # Filter out obvious false positives
        valid_emails = []
        for email in emails:
            if not any(skip in email.lower() for skip in ['example.com', 'test.com', 'noreply']):
                valid_emails.append(email.lower())
        
        return list(set(valid_emails))  # Remove duplicates
    
    def extract_phones(self, text: str) -> List[str]:
        """Extract phone numbers."""
        patterns = [
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # US format
            r'\+\d{1,3}[-.\s]?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}'  # International
        ]
        
        phones = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            phones.extend(matches)
        
        # Clean and validate
        valid_phones = []
        for phone in phones:
            clean_phone = re.sub(r'[^\d]', '', phone)
            if len(clean_phone) >= 10:
                valid_phones.append(phone)
        
        return list(set(valid_phones))
    
    def extract_name(self, soup, title: str) -> str:
        """Extract name from page or title."""
        # Try to get name from page
        selectors = ['h1', 'title', '.name']
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text and len(text) < 100:
                    return text
        
        # Fallback to title
        return title or "Unknown"
    
    def detect_platform(self, url: str) -> str:
        """Detect platform from URL."""
        url_lower = url.lower()
        if 'linkedin.com' in url_lower:
            return 'LinkedIn'
        elif 'github.com' in url_lower:
            return 'GitHub'
        elif 'twitter.com' in url_lower:
            return 'Twitter'
        else:
            return 'Other'

def main():
    """Interactive CLI."""
    print("🔍 WORKING PROFILE SCRAPER")
    print("=" * 40)
    
    scraper = WorkingScraper()
    
    while True:
        keyword = input("\nEnter search keyword (or 'quit' to exit): ").strip()
        
        if keyword.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
        
        if not keyword:
            print("❌ Please enter a keyword")
            continue
        
        # Perform search
        results = scraper.search_profiles(keyword)
        
        # Display results
        print(f"\n{'='*50}")
        print(f"RESULTS FOR '{keyword.upper()}'")
        print(f"{'='*50}")
        
        if not results['profiles']:
            print("❌ No profiles found")
            continue
        
        for i, profile in enumerate(results['profiles'], 1):
            print(f"\n👤 Profile {i}:")
            print(f"   Name: {profile['name']}")
            print(f"   Platform: {profile['platform']}")
            print(f"   URL: {profile['url']}")
            
            if profile['emails']:
                print(f"   📧 Emails: {', '.join(profile['emails'])}")
            
            if profile['phones']:
                print(f"   📞 Phones: {', '.join(profile['phones'])}")

if __name__ == '__main__':
    main()