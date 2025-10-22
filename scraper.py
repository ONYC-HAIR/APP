import asyncio
import aiohttp
import logging
import time
from typing import List, Dict, Set, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import concurrent.futures
from threading import Thread, Lock

from config import config
from database import db
from data_extractor import extractor
from search_engines import search_manager

class ProfileScraper:
    """Main scraper class that coordinates all scraping operations."""
    
    def __init__(self):
        self.visited_urls: Set[str] = set()
        self.results_lock = Lock()
        self.session = None
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging for the scraper."""
        logging.basicConfig(
            level=getattr(logging, config.LOG_LEVEL),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('scraper.log'),
                logging.StreamHandler()
            ]
        )
    
    async def scrape_profiles(self, keyword: str, platforms: List[str] = None) -> Dict:
        """Main method to scrape profiles based on keyword."""
        logging.info(f"Starting profile scraping for keyword: '{keyword}'")
        
        # Create search session in database
        search_engines = list(search_manager.engines.keys())
        search_id = db.create_search_session(keyword, search_engines)
        
        if not search_id:
            logging.error("Failed to create search session")
            return {'error': 'Failed to create search session'}
        
        try:
            # Update status to running
            db.update_search_status(search_id, 'running')
            
            # Step 1: Search for profile URLs
            search_results = await self._search_for_profiles(keyword, platforms)
            
            # Step 2: Extract unique URLs
            profile_urls = self._extract_unique_urls(search_results)
            logging.info(f"Found {len(profile_urls)} unique URLs to scrape")
            
            # Step 3: Scrape individual profiles
            scraped_profiles = await self._scrape_profile_urls(profile_urls, search_id)
            
            # Step 4: Update final status
            db.update_search_status(search_id, 'completed', len(scraped_profiles))
            
            logging.info(f"Completed scraping. Found {len(scraped_profiles)} profiles")
            
            return {
                'search_id': search_id,
                'keyword': keyword,
                'total_profiles': len(scraped_profiles),
                'profiles': scraped_profiles
            }
            
        except Exception as e:
            logging.error(f"Scraping failed: {e}")
            db.update_search_status(search_id, 'failed')
            return {'error': str(e)}
    
    async def _search_for_profiles(self, keyword: str, platforms: List[str] = None) -> Dict[str, List[Dict]]:
        """Search for profile URLs using multiple search engines."""
        logging.info("Searching for profile URLs...")
        
        # Use asyncio to run search engines concurrently
        search_tasks = []
        
        for engine_name, engine in search_manager.engines.items():
            task = asyncio.create_task(
                self._run_search_engine(engine, keyword, platforms)
            )
            search_tasks.append((engine_name, task))
        
        # Wait for all searches to complete
        results = {}
        for engine_name, task in search_tasks:
            try:
                engine_results = await task
                results[engine_name] = engine_results
            except Exception as e:
                logging.error(f"Search engine {engine_name} failed: {e}")
                results[engine_name] = []
        
        return results
    
    async def _run_search_engine(self, engine, keyword: str, platforms: List[str] = None) -> List[Dict]:
        """Run a single search engine in async context."""
        loop = asyncio.get_event_loop()
        
        # Run search engine in thread pool since it's not async
        with concurrent.futures.ThreadPoolExecutor() as executor:
            queries = search_manager._generate_search_queries(keyword, platforms)
            
            tasks = []
            for query in queries:
                task = loop.run_in_executor(
                    executor, 
                    lambda q=query: engine.search(q, config.MAX_RESULTS_PER_SEARCH // len(queries))
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Flatten results
            all_results = []
            for result in results:
                if isinstance(result, list):
                    all_results.extend(result)
                elif isinstance(result, Exception):
                    logging.error(f"Search query failed: {result}")
            
            return all_results
    
    def _extract_unique_urls(self, search_results: Dict[str, List[Dict]]) -> List[Dict]:
        """Extract unique URLs from search results."""
        unique_urls = {}
        
        for engine, results in search_results.items():
            for result in results:
                url = result.get('url')
                if url and self._is_valid_profile_url(url):
                    # Use URL as key to avoid duplicates
                    if url not in unique_urls:
                        unique_urls[url] = {
                            'url': url,
                            'title': result.get('title', ''),
                            'description': result.get('description', ''),
                            'source_engine': engine,
                            'platform': extractor._detect_platform(url)
                        }
        
        return list(unique_urls.values())
    
    def _is_valid_profile_url(self, url: str) -> bool:
        """Check if URL is likely a profile page."""
        if not url or url in self.visited_urls:
            return False
        
        # Skip common non-profile URLs
        skip_patterns = [
            '/search', '/login', '/register', '/privacy', '/terms',
            '/help', '/support', '/about', '/careers', '/blog',
            '.pdf', '.doc', '.jpg', '.png', '.gif', '.mp4',
            'javascript:', 'mailto:', 'tel:'
        ]
        
        url_lower = url.lower()
        for pattern in skip_patterns:
            if pattern in url_lower:
                return False
        
        # Check for profile indicators
        profile_indicators = [
            'linkedin.com/in/', 'twitter.com/', 'github.com/',
            'facebook.com/', 'instagram.com/', 'profile',
            'user', 'people', 'member'
        ]
        
        for indicator in profile_indicators:
            if indicator in url_lower:
                return True
        
        return False
    
    async def _scrape_profile_urls(self, urls: List[Dict], search_id: int) -> List[Dict]:
        """Scrape individual profile URLs."""
        logging.info(f"Scraping {len(urls)} profile URLs...")
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=config.TIMEOUT),
            headers=config.DEFAULT_HEADERS
        ) as session:
            self.session = session
            
            # Process URLs in batches to avoid overwhelming servers
            batch_size = config.MAX_CONCURRENT_REQUESTS
            scraped_profiles = []
            
            for i in range(0, len(urls), batch_size):
                batch = urls[i:i + batch_size]
                
                # Process batch concurrently
                batch_tasks = [
                    self._scrape_single_profile(url_data, search_id)
                    for url_data in batch
                ]
                
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Collect successful results
                for result in batch_results:
                    if isinstance(result, dict) and not isinstance(result, Exception):
                        scraped_profiles.append(result)
                    elif isinstance(result, Exception):
                        logging.error(f"Profile scraping failed: {result}")
                
                # Rate limiting between batches
                await asyncio.sleep(config.REQUEST_DELAY)
            
            return scraped_profiles
    
    async def _scrape_single_profile(self, url_data: Dict, search_id: int) -> Optional[Dict]:
        """Scrape a single profile URL."""
        url = url_data['url']
        
        if url in self.visited_urls:
            return None
        
        self.visited_urls.add(url)
        
        try:
            # Fetch page content
            soup = await self._fetch_page_content(url)
            if not soup:
                return None
            
            # Extract profile information
            profile_info = extractor.extract_profile_info(soup, url)
            profile_info.update({
                'title': url_data.get('title'),
                'description': profile_info.get('description') or url_data.get('description')
            })
            
            # Save profile to database
            profile_id = db.add_profile(search_id, profile_info)
            if not profile_id:
                return None
            
            # Extract contact information from page content
            page_text = soup.get_text()
            
            # Extract emails
            emails = extractor.extract_emails(page_text, url)
            for email_data in emails[:3]:  # Limit to top 3 emails
                db.add_contact(
                    profile_id, 'email', email_data['value'],
                    email_data['confidence'], email_data.get('source_url')
                )
            
            # Extract phone numbers
            phones = extractor.extract_phones(page_text, url)
            for phone_data in phones[:3]:  # Limit to top 3 phones
                db.add_contact(
                    profile_id, 'phone', phone_data['value'],
                    phone_data['confidence'], phone_data.get('source_url')
                )
            
            # Add contact data to profile info for return
            profile_info['emails'] = [e['value'] for e in emails]
            profile_info['phones'] = [p['value'] for p in phones]
            profile_info['profile_id'] = profile_id
            
            logging.info(f"Scraped profile: {profile_info.get('name', 'Unknown')} - {url}")
            return profile_info
            
        except Exception as e:
            logging.error(f"Failed to scrape {url}: {e}")
            return None
    
    async def _fetch_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse page content."""
        try:
            # First try with aiohttp
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    return BeautifulSoup(content, 'html.parser')
                else:
                    logging.warning(f"HTTP {response.status} for {url}")
                    return None
                    
        except Exception as e:
            logging.debug(f"aiohttp failed for {url}, trying Selenium: {e}")
            
            # Fallback to Selenium for JavaScript-heavy sites
            try:
                selenium_engine = search_manager.get_selenium_engine()
                if selenium_engine:
                    return selenium_engine.search_with_selenium(url)
            except Exception as selenium_error:
                logging.error(f"Selenium also failed for {url}: {selenium_error}")
            
            return None
    
    def get_search_results(self, search_id: int) -> Dict:
        """Get results for a specific search."""
        return db.get_search_results(search_id)
    
    def get_all_searches(self) -> List[Dict]:
        """Get all search sessions."""
        return db.get_all_searches()
    
    def export_results(self, search_id: int, format: str = 'csv') -> bool:
        """Export search results to file."""
        if format == 'csv':
            filename = f"search_results_{search_id}_{int(time.time())}.csv"
            return db.export_to_csv(search_id, filename)
        else:
            logging.error(f"Unsupported export format: {format}")
            return False
    
    def cleanup(self):
        """Cleanup resources."""
        search_manager.cleanup()

class ScrapingJob:
    """Represents a scraping job that can be run asynchronously."""
    
    def __init__(self, keyword: str, platforms: List[str] = None):
        self.keyword = keyword
        self.platforms = platforms
        self.scraper = ProfileScraper()
        self.result = None
        self.status = 'pending'
        self.error = None
    
    async def run(self):
        """Run the scraping job."""
        try:
            self.status = 'running'
            self.result = await self.scraper.scrape_profiles(self.keyword, self.platforms)
            self.status = 'completed'
        except Exception as e:
            self.status = 'failed'
            self.error = str(e)
            logging.error(f"Scraping job failed: {e}")
        finally:
            self.scraper.cleanup()
    
    def get_status(self) -> Dict:
        """Get current status of the job."""
        return {
            'keyword': self.keyword,
            'platforms': self.platforms,
            'status': self.status,
            'result': self.result,
            'error': self.error
        }

# Global scraper instance
scraper = ProfileScraper()