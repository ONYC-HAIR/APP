#!/usr/bin/env python3
"""Quick test of the profile scraper"""

from working_scraper import WorkingScraper

def test_scraper():
    print("🔍 Testing Profile Scraper")
    print("=" * 30)
    
    scraper = WorkingScraper()
    
    # Test with a common search term
    keyword = "software engineer python"
    print(f"Searching for: {keyword}")
    
    results = scraper.search_profiles(keyword)
    
    print(f"\n📊 Results:")
    print(f"Total profiles found: {results['total_profiles']}")
    
    for i, profile in enumerate(results['profiles'][:3], 1):  # Show first 3
        print(f"\n👤 Profile {i}:")
        print(f"   Name: {profile['name']}")
        print(f"   Platform: {profile['platform']}")
        print(f"   URL: {profile['url']}")
        
        if profile['emails']:
            print(f"   📧 Emails: {', '.join(profile['emails'])}")
        
        if profile['phones']:
            print(f"   📞 Phones: {', '.join(profile['phones'])}")

if __name__ == '__main__':
    test_scraper()