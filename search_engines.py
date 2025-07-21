import requests
import time
import logging
import random
from typing import List, Dict, Optional
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from config import config

class SearchEngine:
    """Base class for search engines."""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.session.headers.update(config.DEFAULT_HEADERS)
    
    def get_random_user_agent(self) -> str:
        """Get a random user agent."""
        if config.USE_RANDOM_USER_AGENT:
            return self.ua.random
        return self.session.headers.get('User-Agent', '')
    
    def search(self, query: str, max_results: int = 50) -> List[Dict]:
        """Search for a query and return results."""
        raise NotImplementedError
    
    def _make_request(self, url: str, params: dict = None) -> Optional[requests.Response]:
        """Make a request with rate limiting and error handling."""
        try:
            # Rate limiting
            time.sleep(config.REQUEST_DELAY + random.uniform(0, 1))
            
            # Random user agent
            headers = {'User-Agent': self.get_random_user_agent()}
            
            response = self.session.get(
                url,
                params=params,
                headers=headers,
                timeout=config.TIMEOUT
            )
            
            response.raise_for_status()
            return response
            
        except requests.RequestException as e:
            logging.error(f"Request failed for {url}: {e}")
            return None

class GoogleSearch(SearchEngine):
    """Google search implementation."""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.google.com/search"
    
    def search(self, query: str, max_results: int = 50) -> List[Dict]:
        """Search Google and extract results."""
        results = []
        page = 0
        
        while len(results) < max_results and page < config.MAX_PAGES_TO_SCRAPE:
            params = {
                'q': query,
                'start': page * 10,
                'num': 10,
                'hl': 'en'
            }
            
            response = self._make_request(self.base_url, params)
            if not response:
                break
            
            soup = BeautifulSoup(response.content, 'html.parser')
            page_results = self._extract_google_results(soup)
            
            if not page_results:
                break
            
            results.extend(page_results)
            page += 1
        
        return results[:max_results]
    
    def _extract_google_results(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract search results from Google page."""
        results = []
        
        # Google search result selectors
        result_containers = soup.find_all('div', class_='g')
        
        for container in result_containers:
            try:
                # Title and URL
                title_element = container.find('h3')
                if not title_element:
                    continue
                
                link_element = container.find('a')
                if not link_element or not link_element.get('href'):
                    continue
                
                url = link_element['href']
                if url.startswith('/url?q='):
                    # Clean Google redirect URL
                    url = url.split('/url?q=')[1].split('&')[0]
                
                title = title_element.get_text(strip=True)
                
                # Description
                desc_element = container.find('span', class_='aCOpRe') or \
                              container.find('div', class_='VwiC3b')
                description = desc_element.get_text(strip=True) if desc_element else ''
                
                results.append({
                    'title': title,
                    'url': url,
                    'description': description,
                    'source': 'google'
                })
                
            except Exception as e:
                logging.debug(f"Error parsing Google result: {e}")
                continue
        
        return results

class BingSearch(SearchEngine):
    """Bing search implementation."""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.bing.com/search"
    
    def search(self, query: str, max_results: int = 50) -> List[Dict]:
        """Search Bing and extract results."""
        results = []
        page = 1
        
        while len(results) < max_results and page <= config.MAX_PAGES_TO_SCRAPE:
            params = {
                'q': query,
                'first': (page - 1) * 10 + 1,
                'count': 10
            }
            
            response = self._make_request(self.base_url, params)
            if not response:
                break
            
            soup = BeautifulSoup(response.content, 'html.parser')
            page_results = self._extract_bing_results(soup)
            
            if not page_results:
                break
            
            results.extend(page_results)
            page += 1
        
        return results[:max_results]
    
    def _extract_bing_results(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract search results from Bing page."""
        results = []
        
        # Bing search result selectors
        result_containers = soup.find_all('li', class_='b_algo')
        
        for container in result_containers:
            try:
                # Title and URL
                title_element = container.find('h2')
                if not title_element:
                    continue
                
                link_element = title_element.find('a')
                if not link_element or not link_element.get('href'):
                    continue
                
                url = link_element['href']
                title = link_element.get_text(strip=True)
                
                # Description
                desc_element = container.find('p') or container.find('div', class_='b_caption')
                description = desc_element.get_text(strip=True) if desc_element else ''
                
                results.append({
                    'title': title,
                    'url': url,
                    'description': description,
                    'source': 'bing'
                })
                
            except Exception as e:
                logging.debug(f"Error parsing Bing result: {e}")
                continue
        
        return results

class DuckDuckGoSearch(SearchEngine):
    """DuckDuckGo search implementation."""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://html.duckduckgo.com/html/"
    
    def search(self, query: str, max_results: int = 50) -> List[Dict]:
        """Search DuckDuckGo and extract results."""
        results = []
        page = 0
        
        # DuckDuckGo pagination is different
        while len(results) < max_results and page < config.MAX_PAGES_TO_SCRAPE:
            params = {
                'q': query,
                's': page * 30,  # DuckDuckGo uses 30 results per page
            }
            
            response = self._make_request(self.base_url, params)
            if not response:
                break
            
            soup = BeautifulSoup(response.content, 'html.parser')
            page_results = self._extract_duckduckgo_results(soup)
            
            if not page_results:
                break
            
            results.extend(page_results)
            page += 1
        
        return results[:max_results]
    
    def _extract_duckduckgo_results(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract search results from DuckDuckGo page."""
        results = []
        
        # DuckDuckGo search result selectors
        result_containers = soup.find_all('div', class_='result')
        
        for container in result_containers:
            try:
                # Title and URL
                title_element = container.find('a', class_='result__a')
                if not title_element or not title_element.get('href'):
                    continue
                
                url = title_element['href']
                title = title_element.get_text(strip=True)
                
                # Description
                desc_element = container.find('a', class_='result__snippet')
                description = desc_element.get_text(strip=True) if desc_element else ''
                
                results.append({
                    'title': title,
                    'url': url,
                    'description': description,
                    'source': 'duckduckgo'
                })
                
            except Exception as e:
                logging.debug(f"Error parsing DuckDuckGo result: {e}")
                continue
        
        return results

class SeleniumSearchEngine:
    """Selenium-based search engine for JavaScript-heavy sites."""
    
    def __init__(self):
        self.driver = None
        self._setup_driver()
    
    def _setup_driver(self):
        """Setup Chrome WebDriver with options."""
        try:
            chrome_options = Options()
            
            if config.HEADLESS_BROWSER:
                chrome_options.add_argument('--headless')
            
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--disable-javascript')  # For basic scraping
            
            # Random user agent
            ua = UserAgent()
            chrome_options.add_argument(f'--user-agent={ua.random}')
            
            # Install and setup ChromeDriver
            driver_path = ChromeDriverManager().install()
            self.driver = webdriver.Chrome(driver_path, options=chrome_options)
            self.driver.set_page_load_timeout(config.SELENIUM_TIMEOUT)
            
        except Exception as e:
            logging.error(f"Failed to setup Selenium driver: {e}")
            self.driver = None
    
    def search_with_selenium(self, url: str, wait_element: str = None) -> Optional[BeautifulSoup]:
        """Load a page with Selenium and return BeautifulSoup object."""
        if not self.driver:
            return None
        
        try:
            self.driver.get(url)
            
            if wait_element:
                wait = WebDriverWait(self.driver, config.SELENIUM_TIMEOUT)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, wait_element)))
            
            time.sleep(2)  # Additional wait for dynamic content
            
            html_content = self.driver.page_source
            return BeautifulSoup(html_content, 'html.parser')
            
        except Exception as e:
            logging.error(f"Selenium search failed for {url}: {e}")
            return None
    
    def close(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None

class SearchEngineManager:
    """Manager for coordinating multiple search engines."""
    
    def __init__(self):
        self.engines = {}
        self.selenium_engine = None
        self._init_engines()
    
    def _init_engines(self):
        """Initialize search engines based on configuration."""
        if 'google' in config.SEARCH_ENGINES:
            self.engines['google'] = GoogleSearch()
        
        if 'bing' in config.SEARCH_ENGINES:
            self.engines['bing'] = BingSearch()
        
        if 'duckduckgo' in config.SEARCH_ENGINES:
            self.engines['duckduckgo'] = DuckDuckGoSearch()
    
    def search_all(self, keyword: str, platforms: List[str] = None) -> Dict[str, List[Dict]]:
        """Search across all configured search engines."""
        all_results = {}
        
        # Generate different search queries for better coverage
        queries = self._generate_search_queries(keyword, platforms)
        
        for engine_name, engine in self.engines.items():
            engine_results = []
            
            for query in queries:
                try:
                    results = engine.search(query, config.MAX_RESULTS_PER_SEARCH // len(queries))
                    engine_results.extend(results)
                    
                    # Rate limiting between queries
                    time.sleep(1)
                    
                except Exception as e:
                    logging.error(f"Search failed for {engine_name} with query '{query}': {e}")
            
            all_results[engine_name] = engine_results
            logging.info(f"{engine_name}: Found {len(engine_results)} results")
        
        return all_results
    
    def _generate_search_queries(self, keyword: str, platforms: List[str] = None) -> List[str]:
        """Generate optimized search queries for different purposes."""
        queries = []
        
        # Platform-specific queries
        if platforms:
            for platform in platforms:
                if platform in config.SEARCH_TEMPLATES:
                    queries.append(config.SEARCH_TEMPLATES[platform].format(keyword=keyword))
        else:
            # Use all social platforms
            for platform in config.SOCIAL_PLATFORMS:
                if platform in config.SEARCH_TEMPLATES:
                    queries.append(config.SEARCH_TEMPLATES[platform].format(keyword=keyword))
        
        # Contact-specific queries
        queries.extend([
            config.SEARCH_TEMPLATES['email'].format(keyword=keyword),
            config.SEARCH_TEMPLATES['phone'].format(keyword=keyword),
            config.SEARCH_TEMPLATES['general'].format(keyword=keyword)
        ])
        
        return list(set(queries))  # Remove duplicates
    
    def get_selenium_engine(self) -> Optional[SeleniumSearchEngine]:
        """Get Selenium engine for JavaScript-heavy sites."""
        if not self.selenium_engine:
            self.selenium_engine = SeleniumSearchEngine()
        return self.selenium_engine
    
    def cleanup(self):
        """Cleanup resources."""
        if self.selenium_engine:
            self.selenium_engine.close()
            self.selenium_engine = None

# Create global search manager
search_manager = SearchEngineManager()