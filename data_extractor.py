import re
import logging
from typing import List, Dict, Set, Optional
from urllib.parse import urljoin, urlparse
import phonenumbers
from email_validator import validate_email, EmailNotValidError
from config import config

class DataExtractor:
    """Extract contact information and profile data from web content."""
    
    def __init__(self):
        self.email_pattern = re.compile(config.EMAIL_PATTERN, re.IGNORECASE)
        self.phone_patterns = [re.compile(pattern) for pattern in config.PHONE_PATTERNS]
        
        # Social media URL patterns
        self.social_patterns = {
            'linkedin': re.compile(r'linkedin\.com/in/([a-zA-Z0-9\-_]+)', re.IGNORECASE),
            'twitter': re.compile(r'twitter\.com/([a-zA-Z0-9\-_]+)', re.IGNORECASE),
            'github': re.compile(r'github\.com/([a-zA-Z0-9\-_]+)', re.IGNORECASE),
            'facebook': re.compile(r'facebook\.com/([a-zA-Z0-9\-_.]+)', re.IGNORECASE),
            'instagram': re.compile(r'instagram\.com/([a-zA-Z0-9\-_.]+)', re.IGNORECASE)
        }
    
    def extract_emails(self, text: str, source_url: str = None) -> List[Dict]:
        """Extract and validate email addresses from text."""
        emails = []
        found_emails = set()
        
        # Find all email patterns
        matches = self.email_pattern.findall(text)
        
        for email in matches:
            email = email.lower().strip()
            
            # Skip if already found
            if email in found_emails:
                continue
                
            # Skip common false positives
            if self._is_valid_email(email):
                found_emails.add(email)
                emails.append({
                    'value': email,
                    'confidence': self._calculate_email_confidence(email, text),
                    'source_url': source_url
                })
        
        return sorted(emails, key=lambda x: x['confidence'], reverse=True)
    
    def extract_phones(self, text: str, source_url: str = None) -> List[Dict]:
        """Extract and validate phone numbers from text."""
        phones = []
        found_phones = set()
        
        for pattern in self.phone_patterns:
            matches = pattern.findall(text)
            
            for match in matches:
                if isinstance(match, tuple):
                    # For patterns with groups
                    phone = ''.join(match)
                else:
                    phone = match
                
                # Clean phone number
                phone_clean = re.sub(r'[^\d+]', '', phone)
                
                # Skip if too short or already found
                if len(phone_clean) < 10 or phone_clean in found_phones:
                    continue
                
                # Validate phone number
                if self._is_valid_phone(phone_clean):
                    found_phones.add(phone_clean)
                    phones.append({
                        'value': self._format_phone(phone_clean),
                        'confidence': self._calculate_phone_confidence(phone, text),
                        'source_url': source_url
                    })
        
        return sorted(phones, key=lambda x: x['confidence'], reverse=True)
    
    def extract_social_profiles(self, text: str, html_content: str = None) -> List[Dict]:
        """Extract social media profile URLs."""
        profiles = []
        found_urls = set()
        
        # Combine text and HTML for URL extraction
        search_content = text
        if html_content:
            search_content += " " + html_content
        
        for platform, pattern in self.social_patterns.items():
            matches = pattern.finditer(search_content)
            
            for match in matches:
                url = match.group(0)
                username = match.group(1)
                
                # Clean URL
                if not url.startswith('http'):
                    url = 'https://' + url
                
                if url not in found_urls:
                    found_urls.add(url)
                    profiles.append({
                        'platform': platform,
                        'url': url,
                        'username': username,
                        'confidence': self._calculate_social_confidence(url, search_content)
                    })
        
        return sorted(profiles, key=lambda x: x['confidence'], reverse=True)
    
    def extract_profile_info(self, soup, url: str) -> Dict:
        """Extract profile information from BeautifulSoup object."""
        profile = {
            'url': url,
            'platform': self._detect_platform(url),
            'name': None,
            'title': None,
            'company': None,
            'location': None,
            'description': None,
            'profile_image_url': None
        }
        
        # Platform-specific extraction
        platform = profile['platform']
        
        if platform == 'linkedin':
            profile.update(self._extract_linkedin_info(soup, url))
        elif platform == 'twitter':
            profile.update(self._extract_twitter_info(soup, url))
        elif platform == 'github':
            profile.update(self._extract_github_info(soup, url))
        elif platform == 'facebook':
            profile.update(self._extract_facebook_info(soup, url))
        else:
            profile.update(self._extract_generic_info(soup, url))
        
        return profile
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email address."""
        try:
            validate_email(email)
            
            # Additional filters for common false positives
            invalid_domains = [
                'example.com', 'test.com', 'localhost', 'domain.com',
                'email.com', 'mail.com', 'gmail.co', 'yahoo.co'
            ]
            
            domain = email.split('@')[1].lower()
            if domain in invalid_domains:
                return False
            
            # Check for suspicious patterns
            if len(email.split('@')[0]) < 2:  # Username too short
                return False
                
            return True
            
        except EmailNotValidError:
            return False
    
    def _is_valid_phone(self, phone: str) -> bool:
        """Validate phone number using phonenumbers library."""
        try:
            # Try parsing as US number first
            parsed = phonenumbers.parse(phone, "US")
            return phonenumbers.is_valid_number(parsed)
        except:
            try:
                # Try parsing with international format
                parsed = phonenumbers.parse(phone, None)
                return phonenumbers.is_valid_number(parsed)
            except:
                return False
    
    def _format_phone(self, phone: str) -> str:
        """Format phone number to standard format."""
        try:
            parsed = phonenumbers.parse(phone, "US")
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        except:
            return phone
    
    def _calculate_email_confidence(self, email: str, context: str) -> float:
        """Calculate confidence score for email based on context."""
        confidence = 0.5  # Base confidence
        
        # Higher confidence for common business domains
        business_domains = ['gmail.com', 'outlook.com', 'yahoo.com', 'hotmail.com']
        domain = email.split('@')[1].lower()
        
        if domain in business_domains:
            confidence += 0.2
        elif '.' in domain and not domain.endswith('.png') and not domain.endswith('.jpg'):
            confidence += 0.3  # Custom domain
        
        # Context-based confidence
        email_keywords = ['contact', 'email', 'mail', 'reach', 'business']
        context_lower = context.lower()
        
        for keyword in email_keywords:
            if keyword in context_lower:
                confidence += 0.1
                break
        
        return min(confidence, 1.0)
    
    def _calculate_phone_confidence(self, phone: str, context: str) -> float:
        """Calculate confidence score for phone based on context."""
        confidence = 0.5  # Base confidence
        
        # Higher confidence for formatted numbers
        if any(char in phone for char in ['-', '(', ')', ' ', '.']):
            confidence += 0.2
        
        # Context-based confidence
        phone_keywords = ['phone', 'call', 'contact', 'tel', 'mobile', 'cell']
        context_lower = context.lower()
        
        for keyword in phone_keywords:
            if keyword in context_lower:
                confidence += 0.2
                break
        
        return min(confidence, 1.0)
    
    def _calculate_social_confidence(self, url: str, context: str) -> float:
        """Calculate confidence score for social profile."""
        confidence = 0.7  # Base confidence for social URLs
        
        # Higher confidence if mentioned in context
        platform = self._detect_platform(url)
        if platform and platform.lower() in context.lower():
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _detect_platform(self, url: str) -> str:
        """Detect social media platform from URL."""
        url_lower = url.lower()
        
        if 'linkedin.com' in url_lower:
            return 'linkedin'
        elif 'twitter.com' in url_lower or 'x.com' in url_lower:
            return 'twitter'
        elif 'github.com' in url_lower:
            return 'github'
        elif 'facebook.com' in url_lower:
            return 'facebook'
        elif 'instagram.com' in url_lower:
            return 'instagram'
        else:
            return 'other'
    
    def _extract_linkedin_info(self, soup, url: str) -> Dict:
        """Extract LinkedIn-specific profile information."""
        info = {}
        
        # Name
        name_selectors = [
            'h1.text-heading-xlarge',
            '.pv-text-details__left-panel h1',
            '.profile-real-name',
            'h1[data-test="profile-heading"]'
        ]
        info['name'] = self._find_text_by_selectors(soup, name_selectors)
        
        # Title
        title_selectors = [
            '.text-body-medium.break-words',
            '.pv-text-details__left-panel .text-body-medium',
            '.profile-headline'
        ]
        info['title'] = self._find_text_by_selectors(soup, title_selectors)
        
        # Company
        company_selectors = [
            '.pv-entity__company-summary-info h3',
            '.experience-item__company',
            '.pv-experience-entity h3'
        ]
        info['company'] = self._find_text_by_selectors(soup, company_selectors)
        
        # Location
        location_selectors = [
            '.pv-text-details__left-panel .text-body-small',
            '.profile-location'
        ]
        info['location'] = self._find_text_by_selectors(soup, location_selectors)
        
        return info
    
    def _extract_twitter_info(self, soup, url: str) -> Dict:
        """Extract Twitter-specific profile information."""
        info = {}
        
        # Name
        name_selectors = [
            '[data-testid="UserName"] span',
            '.profile-name',
            'h1.profile-name'
        ]
        info['name'] = self._find_text_by_selectors(soup, name_selectors)
        
        # Description/Bio
        bio_selectors = [
            '[data-testid="UserDescription"]',
            '.profile-bio',
            '.bio'
        ]
        info['description'] = self._find_text_by_selectors(soup, bio_selectors)
        
        return info
    
    def _extract_github_info(self, soup, url: str) -> Dict:
        """Extract GitHub-specific profile information."""
        info = {}
        
        # Name
        name_selectors = [
            '.vcard-fullname',
            '.profile-name',
            'h1.vcard-names span'
        ]
        info['name'] = self._find_text_by_selectors(soup, name_selectors)
        
        # Bio
        bio_selectors = [
            '.user-profile-bio',
            '.profile-bio',
            '.bio'
        ]
        info['description'] = self._find_text_by_selectors(soup, bio_selectors)
        
        # Company
        company_selectors = [
            '.vcard-detail[itemprop="worksFor"]',
            '.company'
        ]
        info['company'] = self._find_text_by_selectors(soup, company_selectors)
        
        # Location
        location_selectors = [
            '.vcard-detail[itemprop="homeLocation"]',
            '.location'
        ]
        info['location'] = self._find_text_by_selectors(soup, location_selectors)
        
        return info
    
    def _extract_facebook_info(self, soup, url: str) -> Dict:
        """Extract Facebook-specific profile information."""
        info = {}
        
        # Facebook profiles are heavily protected, limited extraction
        name_selectors = [
            'h1',
            '.profile-name',
            '#fb-timeline-cover-name'
        ]
        info['name'] = self._find_text_by_selectors(soup, name_selectors)
        
        return info
    
    def _extract_generic_info(self, soup, url: str) -> Dict:
        """Extract generic profile information from any website."""
        info = {}
        
        # Try to find name in common places
        name_selectors = [
            'h1', 'h2', '.name', '.full-name', '.profile-name',
            '[itemprop="name"]', '.author-name'
        ]
        info['name'] = self._find_text_by_selectors(soup, name_selectors)
        
        # Try to find title/description
        desc_selectors = [
            '.bio', '.description', '.about', '.summary',
            '[itemprop="description"]', 'meta[name="description"]'
        ]
        info['description'] = self._find_text_by_selectors(soup, desc_selectors)
        
        return info
    
    def _find_text_by_selectors(self, soup, selectors: List[str]) -> Optional[str]:
        """Find text content using multiple CSS selectors."""
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    if text and len(text) > 2:  # Minimum meaningful length
                        return text
            except:
                continue
        return None

# Create global extractor instance
extractor = DataExtractor()