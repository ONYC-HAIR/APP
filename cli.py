#!/usr/bin/env python3
"""
Command Line Interface for Profile Scraper
Usage: python cli.py [options] keyword
"""

import argparse
import asyncio
import json
import sys
import time
from typing import List
import logging

from scraper import ProfileScraper
from database import db
from config import config

def setup_logging(verbose: bool = False):
    """Setup logging for CLI."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def print_banner():
    """Print application banner."""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                      PROFILE SCRAPER                         ║
    ║          Find public profile information using keywords      ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_results_summary(results: dict):
    """Print a summary of scraping results."""
    if 'error' in results:
        print(f"❌ Error: {results['error']}")
        return
    
    total_profiles = results.get('total_profiles', 0)
    search_id = results.get('search_id')
    keyword = results.get('keyword')
    
    print(f"\n✅ Scraping completed for '{keyword}'")
    print(f"📊 Found {total_profiles} profiles")
    print(f"🆔 Search ID: {search_id}")
    
    if total_profiles > 0:
        print(f"\n📋 Profile Summary:")
        profiles = results.get('profiles', [])
        
        # Count by platform
        platform_counts = {}
        email_count = 0
        phone_count = 0
        
        for profile in profiles:
            platform = profile.get('platform', 'other')
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
            
            if profile.get('emails'):
                email_count += len(profile['emails'])
            if profile.get('phones'):
                phone_count += len(profile['phones'])
        
        for platform, count in platform_counts.items():
            print(f"  • {platform.title()}: {count} profiles")
        
        print(f"\n📧 Total emails found: {email_count}")
        print(f"📞 Total phones found: {phone_count}")

def print_detailed_results(results: dict, limit: int = None):
    """Print detailed results."""
    profiles = results.get('profiles', [])
    
    if not profiles:
        print("No profiles found.")
        return
    
    if limit:
        profiles = profiles[:limit]
        print(f"\nShowing first {len(profiles)} profiles:")
    
    for i, profile in enumerate(profiles, 1):
        print(f"\n--- Profile {i} ---")
        print(f"Name: {profile.get('name', 'Unknown')}")
        print(f"Platform: {profile.get('platform', 'Unknown')}")
        print(f"URL: {profile.get('url', 'N/A')}")
        
        if profile.get('title'):
            print(f"Title: {profile['title']}")
        if profile.get('company'):
            print(f"Company: {profile['company']}")
        if profile.get('location'):
            print(f"Location: {profile['location']}")
        
        emails = profile.get('emails', [])
        phones = profile.get('phones', [])
        
        if emails:
            print(f"Emails: {', '.join(emails)}")
        if phones:
            print(f"Phones: {', '.join(phones)}")

def export_results_cli(search_id: int, format: str = 'csv'):
    """Export results using CLI."""
    scraper = ProfileScraper()
    
    if scraper.export_results(search_id, format):
        filename = f"search_results_{search_id}_{int(time.time())}.{format}"
        print(f"✅ Results exported to: {filename}")
        return True
    else:
        print(f"❌ Failed to export results")
        return False

def list_searches():
    """List all previous searches."""
    searches = db.get_all_searches()
    
    if not searches:
        print("No previous searches found.")
        return
    
    print(f"\n📊 Found {len(searches)} previous searches:")
    print("-" * 80)
    print(f"{'ID':<4} {'Keyword':<20} {'Status':<12} {'Profiles':<8} {'Date':<20}")
    print("-" * 80)
    
    for search in searches:
        timestamp = search['timestamp'][:19] if search['timestamp'] else 'Unknown'
        print(f"{search['id']:<4} {search['keyword']:<20} {search['status']:<12} "
              f"{search['profile_count'] or 0:<8} {timestamp:<20}")

async def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description='Profile Scraper - Find public profile information using keywords',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py "John Smith software engineer"
  python cli.py --platforms linkedin github "Jane Doe data scientist"
  python cli.py --verbose --limit 10 "marketing manager"
  python cli.py --list-searches
  python cli.py --export 5 --format csv
        """
    )
    
    # Main arguments
    parser.add_argument('keyword', nargs='?', help='Search keyword or phrase')
    
    # Platform selection
    parser.add_argument('--platforms', '-p', nargs='+', 
                       choices=['linkedin', 'twitter', 'github', 'facebook', 'instagram'],
                       help='Target specific platforms (default: all)')
    
    # Output options
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--json', action='store_true',
                       help='Output results in JSON format')
    parser.add_argument('--limit', '-l', type=int,
                       help='Limit number of detailed results to show')
    
    # Database operations
    parser.add_argument('--list-searches', action='store_true',
                       help='List all previous searches')
    parser.add_argument('--view-results', type=int, metavar='SEARCH_ID',
                       help='View results from a previous search')
    parser.add_argument('--export', type=int, metavar='SEARCH_ID',
                       help='Export results from a previous search')
    parser.add_argument('--format', choices=['csv', 'json'], default='csv',
                       help='Export format (default: csv)')
    
    # Configuration
    parser.add_argument('--max-results', type=int, default=config.MAX_RESULTS_PER_SEARCH,
                       help=f'Maximum results per search (default: {config.MAX_RESULTS_PER_SEARCH})')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Print banner unless in JSON mode
    if not args.json:
        print_banner()
    
    # Handle database operations
    if args.list_searches:
        list_searches()
        return
    
    if args.view_results:
        scraper = ProfileScraper()
        results = scraper.get_search_results(args.view_results)
        if results:
            if args.json:
                print(json.dumps(results, indent=2))
            else:
                print_detailed_results(results, args.limit)
        else:
            print(f"❌ No results found for search ID {args.view_results}")
        return
    
    if args.export:
        export_results_cli(args.export, args.format)
        return
    
    # Validate keyword
    if not args.keyword:
        parser.error("Keyword is required unless using --list-searches, --view-results, or --export")
    
    # Update config if specified
    if args.max_results:
        config.MAX_RESULTS_PER_SEARCH = args.max_results
    
    # Start scraping
    try:
        scraper = ProfileScraper()
        
        if not args.json:
            print(f"🔍 Starting search for: '{args.keyword}'")
            print(f"🌐 Target platforms: {args.platforms or 'all'}")
            print(f"📊 Max results: {config.MAX_RESULTS_PER_SEARCH}")
            print("⏳ This may take a few minutes...\n")
        
        # Run the scraper
        results = await scraper.scrape_profiles(args.keyword, args.platforms)
        
        # Output results
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print_results_summary(results)
            
            if 'profiles' in results and results['profiles']:
                print_detailed_results(results, args.limit)
                
                # Offer to export
                if results.get('search_id'):
                    print(f"\n💾 To export these results, run:")
                    print(f"   python cli.py --export {results['search_id']} --format csv")
        
    except KeyboardInterrupt:
        print("\n❌ Search interrupted by user")
        sys.exit(1)
    except Exception as e:
        if args.json:
            print(json.dumps({'error': str(e)}))
        else:
            print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        try:
            scraper.cleanup()
        except:
            pass

if __name__ == '__main__':
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        sys.exit(1)
    
    # Run the main function
    asyncio.run(main())