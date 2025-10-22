import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from config import config

class ScraperDatabase:
    """Database manager for storing scraped profile data."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DATABASE_PATH
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create searches table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS searches (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        keyword TEXT NOT NULL,
                        search_engines TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        total_results INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'pending'
                    )
                ''')
                
                # Create profiles table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS profiles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        search_id INTEGER,
                        name TEXT,
                        url TEXT UNIQUE,
                        platform TEXT,
                        title TEXT,
                        company TEXT,
                        location TEXT,
                        description TEXT,
                        profile_image_url TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (search_id) REFERENCES searches (id)
                    )
                ''')
                
                # Create contacts table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS contacts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        profile_id INTEGER,
                        contact_type TEXT,  -- 'email' or 'phone'
                        contact_value TEXT,
                        confidence REAL DEFAULT 1.0,
                        source_url TEXT,
                        verified BOOLEAN DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (profile_id) REFERENCES profiles (id),
                        UNIQUE(profile_id, contact_type, contact_value)
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_profiles_url ON profiles(url)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_contacts_profile ON contacts(profile_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_contacts_type ON contacts(contact_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_searches_keyword ON searches(keyword)')
                
                conn.commit()
                logging.info("Database initialized successfully")
                
        except Exception as e:
            logging.error(f"Database initialization error: {e}")
            raise
    
    def create_search_session(self, keyword: str, search_engines: List[str]) -> int:
        """Create a new search session and return its ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO searches (keyword, search_engines)
                    VALUES (?, ?)
                ''', (keyword, json.dumps(search_engines)))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logging.error(f"Error creating search session: {e}")
            return None
    
    def update_search_status(self, search_id: int, status: str, total_results: int = None):
        """Update search session status and results count."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if total_results is not None:
                    cursor.execute('''
                        UPDATE searches 
                        SET status = ?, total_results = ?
                        WHERE id = ?
                    ''', (status, total_results, search_id))
                else:
                    cursor.execute('''
                        UPDATE searches 
                        SET status = ?
                        WHERE id = ?
                    ''', (status, search_id))
                conn.commit()
        except Exception as e:
            logging.error(f"Error updating search status: {e}")
    
    def add_profile(self, search_id: int, profile_data: Dict) -> Optional[int]:
        """Add a profile to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO profiles 
                    (search_id, name, url, platform, title, company, location, description, profile_image_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    search_id,
                    profile_data.get('name'),
                    profile_data.get('url'),
                    profile_data.get('platform'),
                    profile_data.get('title'),
                    profile_data.get('company'),
                    profile_data.get('location'),
                    profile_data.get('description'),
                    profile_data.get('profile_image_url')
                ))
                
                if cursor.rowcount > 0:
                    profile_id = cursor.lastrowid
                else:
                    # Get existing profile ID
                    cursor.execute('SELECT id FROM profiles WHERE url = ?', (profile_data.get('url'),))
                    result = cursor.fetchone()
                    profile_id = result[0] if result else None
                
                conn.commit()
                return profile_id
        except Exception as e:
            logging.error(f"Error adding profile: {e}")
            return None
    
    def add_contact(self, profile_id: int, contact_type: str, contact_value: str, 
                   confidence: float = 1.0, source_url: str = None) -> bool:
        """Add a contact (email/phone) to a profile."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO contacts 
                    (profile_id, contact_type, contact_value, confidence, source_url)
                    VALUES (?, ?, ?, ?, ?)
                ''', (profile_id, contact_type, contact_value, confidence, source_url))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error adding contact: {e}")
            return False
    
    def get_search_results(self, search_id: int) -> Dict:
        """Get all results for a specific search."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get search info
                cursor.execute('SELECT * FROM searches WHERE id = ?', (search_id,))
                search_info = dict(cursor.fetchone())
                
                # Get profiles with contacts
                cursor.execute('''
                    SELECT p.*, 
                           GROUP_CONCAT(c.contact_type || ':' || c.contact_value, ';') as contacts
                    FROM profiles p
                    LEFT JOIN contacts c ON p.id = c.profile_id
                    WHERE p.search_id = ?
                    GROUP BY p.id
                ''', (search_id,))
                
                profiles = []
                for row in cursor.fetchall():
                    profile = dict(row)
                    if profile['contacts']:
                        contacts = {}
                        for contact in profile['contacts'].split(';'):
                            if ':' in contact:
                                contact_type, contact_value = contact.split(':', 1)
                                if contact_type not in contacts:
                                    contacts[contact_type] = []
                                contacts[contact_type].append(contact_value)
                        profile['contacts'] = contacts
                    else:
                        profile['contacts'] = {}
                    profiles.append(profile)
                
                return {
                    'search_info': search_info,
                    'profiles': profiles
                }
        except Exception as e:
            logging.error(f"Error getting search results: {e}")
            return {}
    
    def get_all_searches(self) -> List[Dict]:
        """Get all search sessions."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT s.*, COUNT(p.id) as profile_count
                    FROM searches s
                    LEFT JOIN profiles p ON s.id = p.search_id
                    GROUP BY s.id
                    ORDER BY s.timestamp DESC
                ''')
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error getting searches: {e}")
            return []
    
    def export_to_csv(self, search_id: int, filename: str) -> bool:
        """Export search results to CSV."""
        try:
            import pandas as pd
            
            results = self.get_search_results(search_id)
            if not results or not results['profiles']:
                return False
            
            # Flatten the data for CSV export
            csv_data = []
            for profile in results['profiles']:
                base_data = {
                    'name': profile['name'],
                    'url': profile['url'],
                    'platform': profile['platform'],
                    'title': profile['title'],
                    'company': profile['company'],
                    'location': profile['location'],
                    'description': profile['description']
                }
                
                # Add contact information
                emails = profile['contacts'].get('email', [])
                phones = profile['contacts'].get('phone', [])
                
                base_data['emails'] = '; '.join(emails) if emails else ''
                base_data['phones'] = '; '.join(phones) if phones else ''
                
                csv_data.append(base_data)
            
            df = pd.DataFrame(csv_data)
            df.to_csv(filename, index=False)
            return True
            
        except Exception as e:
            logging.error(f"Error exporting to CSV: {e}")
            return False
    
    def cleanup_old_searches(self, days: int = 30):
        """Clean up old search data."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM searches 
                    WHERE timestamp < datetime('now', '-{} days')
                '''.format(days))
                conn.commit()
                logging.info(f"Cleaned up searches older than {days} days")
        except Exception as e:
            logging.error(f"Error cleaning up old searches: {e}")

# Create global database instance
db = ScraperDatabase()