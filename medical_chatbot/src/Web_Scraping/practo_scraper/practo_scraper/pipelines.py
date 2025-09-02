# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import re
import pandas as pd
import os
from datetime import datetime
import logging


class ValidationPipeline:
    """Pipeline to validate scraped items"""
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Skip if name is missing (essential field)
        name = adapter.get('name', '').strip()
        if not name:
            raise DropItem(f"Missing or empty name in {item}")
        
        # Skip if name looks like garbage (too short or contains HTML)
        if len(name) < 3 or any(tag in name.lower() for tag in ['<', '>', 'html', 'div', 'span']):
            raise DropItem(f"Invalid name format: {name}")
            
        # Skip if profile URL is missing or invalid
        profile_url = adapter.get('profile_url', '')
        if not profile_url or not profile_url.startswith('https://www.practo.com'):
            raise DropItem(f"Missing or invalid profile URL: {profile_url}")
        
        # Skip if speciality is missing
        speciality = adapter.get('speciality', '').strip()
        if not speciality:
            raise DropItem(f"Missing speciality for {name}")
            
        # Validate consultation fee if present
        consultation_fee = adapter.get('consultation_fee')
        if consultation_fee is not None:
            try:
                fee_value = float(consultation_fee)
                if fee_value < 0 or fee_value > 50000:  # Reasonable fee range
                    spider.logger.warning(f"Unusual consultation fee for {name}: {fee_value}")
            except (ValueError, TypeError):
                spider.logger.warning(f"Invalid consultation fee format for {name}: {consultation_fee}")
        
        # Validate experience if present
        experience = adapter.get('year_of_experience')
        if experience is not None and experience != '':
            try:
                exp_value = float(experience)
                if exp_value < 0 or exp_value > 60:  # Reasonable experience range
                    spider.logger.warning(f"Unusual experience value for {name}: {exp_value}")
            except (ValueError, TypeError):
                spider.logger.warning(f"Invalid experience format for {name}: {experience}")
        
        return item


class CleaningPipeline:
    """Pipeline to clean and normalize scraped data"""
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Clean name
        if adapter.get('name'):
            adapter['name'] = self.clean_text(adapter['name'])
        
        # Clean and normalize degree
        if adapter.get('degree'):
            adapter['degree'] = self.clean_text(adapter['degree'])
            # Extract the main degree
            adapter['degree'] = self.extract_main_degree(adapter['degree'])
        
        # Clean and extract year of experience 
        if adapter.get('year_of_experience'):
            adapter['year_of_experience'] = self.extract_experience_years(adapter['year_of_experience'])
        
        # Clean and validate location
        if adapter.get('location'):
            cleaned_location = self.clean_text(adapter['location'])
            if self.is_valid_location(cleaned_location):
                adapter['location'] = cleaned_location
            else:
                # If location is garbage, try to extract from google_map_link or fall back to city
                adapter['location'] = self.recover_location_from_map_link(
                    adapter.get('google_map_link'), 
                    adapter.get('city', '')
                )
        
        # Clean and convert dp_score to float
        if adapter.get('dp_score'):
            adapter['dp_score'] = self.clean_score(adapter['dp_score'])
        
        # Clean and extract number from npv (votes)
        if adapter.get('npv'):
            adapter['npv'] = self.extract_votes_count(adapter['npv'])
        
        # Clean and extract consultation fee
        if adapter.get('consultation_fee'):
            adapter['consultation_fee'] = self.extract_fee_amount(adapter['consultation_fee'])
        
        # Add timestamp
        adapter['scraped_at'] = datetime.now().isoformat()
        
        return item
    
    def clean_text(self, text):
        """Clean text by removing extra whitespace and special characters"""
        if not text:
            return ""
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', str(text)).strip()
        return text
    
    def extract_main_degree(self, degree_text):
        """Extract the main degree from degree text"""
        if not degree_text:
            return ""
        
        # Common degrees patterns
        degree_patterns = [
            r'\b(MBBS|MD|MS|BDS|MDS|BAMS|BHMS|BUMS|DNB|DM|MCh|PhD|DSc)\b',
            r'\b(Bachelor|Master|Doctor)\s+of\s+\w+',
        ]
        
        for pattern in degree_patterns:
            match = re.search(pattern, degree_text, re.IGNORECASE)
            if match:
                return match.group()
        
        # If no pattern matches, return first word that looks like a degree
        words = degree_text.split()
        for word in words:
            if len(word) >= 3 and word.isalpha():
                return word
        
        return degree_text[:50]  # Truncate if too long
    
    def extract_experience_years(self, experience_text):
        """Extract number of years from experience text"""
        if not experience_text:
            return None
        
        text = str(experience_text).strip()
        if not text:
            return None
        
        # Try to extract year number - handle various formats
        patterns = [
            r'(\d+)\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)',  # "15 years of experience"
            r'(?:experience|exp).*?(\d+)\s*(?:years?|yrs?)',  # "experience 15 years"
            r'(\d+)\s*(?:years?|yrs?)',  # Just "15 years"
            r'(\d{4})',  # Year format like "2009" - will convert to experience
            r'(\d+)',  # Any number
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    value = int(match.group(1))
                    
                    # If it looks like a year (e.g., 2009), convert to experience
                    if value > 1980 and value <= 2024:
                        current_year = datetime.now().year
                        experience = current_year - value
                        if 0 <= experience <= 50:  # Reasonable experience range
                            return experience
                    
                    # Direct experience value
                    elif 0 <= value <= 60:  # Reasonable experience range
                        return value
                        
                except ValueError:
                    continue
        
        return None
    
    def clean_score(self, score_text):
        """Extract and clean rating score"""
        if not score_text:
            return 0.0
        
        # Extract decimal number
        pattern = r'(\d+\.?\d*)'
        match = re.search(pattern, str(score_text))
        
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return 0.0
        
        return 0.0
    
    def extract_votes_count(self, votes_text):
        """Extract number of votes/reviews"""
        if not votes_text:
            return 0
        
        # Look for patterns like "(123 votes)", "123 patient stories"
        pattern = r'(\d+)(?:\s*(?:votes?|patient|stories|reviews?))?'
        match = re.search(pattern, str(votes_text), re.IGNORECASE)
        
        if match:
            return int(match.group(1))
        
        return 0
    
    def extract_fee_amount(self, fee_text):
        """Extract consultation fee amount"""
        if not fee_text:
            return 0
        
        # Remove currency symbols and extract number
        # Handle patterns like "₹500", "500", "₹1,000", etc.
        cleaned = re.sub(r'[₹$,\s]', '', str(fee_text))
        
        pattern = r'(\d+)'
        match = re.search(pattern, cleaned)
        
        if match:
            return int(match.group(1))
        
        return 0
    
    def is_valid_location(self, location):
        """Check if a location is valid and not HTML garbage"""
        if not location or not location.strip():
            return False
        
        location = location.strip()
        
        # Check for HTML tag patterns (common garbage)
        html_patterns = [
            r'^a,abbr,acronym,address,applet,article',  # Common garbage pattern
            r'[a-z]+,[a-z]+,[a-z]+,[a-z]+,[a-z]+',  # Multiple comma-separated lowercase words (5+)
            r'^(a|abbr|acronym|address|applet|article|aside|audio|b|big|blockquote|body|canvas|caption|center|cite)$',  # Single HTML tags
            r'a,abbr,acronym,address,applet,article,aside,audio,b,big,blockquote,body,canvas,caption,center,cite',  # HTML tag sequence
        ]
        
        for pattern in html_patterns:
            if re.search(pattern, location, re.IGNORECASE):
                return False
        
        # Check if it's suspiciously long (garbage data tends to be very long)
        if len(location) > 200:
            return False
            
        # Check if it contains too many commas (likely tag list)
        if location.count(',') > 8:  # Increased threshold as some addresses might have multiple commas
            return False
        
        # Check if it looks like HTML tags
        if '<' in location or '>' in location:
            return False
        
        # Check if it's all lowercase letters and commas (typical HTML tag pattern)
        if re.match(r'^[a-z,\s]+$', location) and ',' in location and len(location.split(',')) > 4:
            return False
        
        return True
    
    def recover_location_from_map_link(self, map_link, city):
        """Try to recover location information from Google Maps link"""
        if not map_link:
            return city or "Location Unknown"
        
        # Extract coordinates from various map link formats
        coord_patterns = [
            r'maps/place/(-?\d+\.?\d*),(-?\d+\.?\d*)',  # Original pattern
            r'maps\?q=(-?\d+\.?\d*),(-?\d+\.?\d*)',      # Query format
            r'dir//(-?\d+\.?\d*),(-?\d+\.?\d*)',         # Direction format
            r'place/(-?\d+\.?\d*),(-?\d+\.?\d*)'         # Place format
        ]
        
        for pattern in coord_patterns:
            match = re.search(pattern, str(map_link))
            if match:
                try:
                    lat, lng = float(match.group(1)), float(match.group(2))
                    # Basic validation for coordinates
                    if -90 <= lat <= 90 and -180 <= lng <= 180:
                        return f"{city} ({lat:.3f}, {lng:.3f})"
                except ValueError:
                    continue
        
        # If it's a search URL, try to extract the search term
        search_pattern = r'maps/search/([^&?]+)'
        search_match = re.search(search_pattern, str(map_link))
        if search_match:
            try:
                from urllib.parse import unquote_plus
                search_term = unquote_plus(search_match.group(1))
                return search_term
            except:
                pass
        
        # If extraction fails, fall back to city
        return city or "Location Unknown"


class CsvExportPipeline:
    """Pipeline to export data to CSV"""
    
    def __init__(self):
        self.items = []
        
    def process_item(self, item, spider):
        self.items.append(ItemAdapter(item).asdict())
        return item
    
    def close_spider(self, spider):
        if self.items:
            # Create data directory if it doesn't exist
            os.makedirs('data', exist_ok=True)
            
            # Convert to DataFrame
            df = pd.DataFrame(self.items)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'data/practo_doctors_{timestamp}.csv'
            
            # Save to CSV
            df.to_csv(filename, index=False, encoding='utf-8')
            
            spider.logger.info(f'Saved {len(self.items)} items to {filename}')
            
            # Also save to a standard filename for easy access
            df.to_csv('data/latest_doctors_data.csv', index=False, encoding='utf-8')
            spider.logger.info(f'Also saved to data/latest_doctors_data.csv')


from scrapy.exceptions import DropItem
import sqlite3
import os
import hashlib


class DuplicateFilterPipeline:
    """Pipeline to filter duplicate items based on profile URL and doctor details"""
    
    def __init__(self):
        self.seen_urls = set()
        self.seen_doctors = set()  # For doctor name + location combinations
        
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Get profile URL and normalize it
        profile_url = adapter.get('profile_url', '')
        if profile_url:
            # Normalize URL by removing query parameters that don't affect identity
            base_url = profile_url.split('?')[0] if '?' in profile_url else profile_url
            base_url = base_url.replace('/recommended', '')  # Remove /recommended suffix
            
            if base_url in self.seen_urls:
                spider.logger.debug(f"Duplicate URL found: {base_url}")
                raise DropItem(f"Duplicate URL: {base_url}")
            
            self.seen_urls.add(base_url)
        
        # Create a unique identifier for doctor based on name and location
        name = adapter.get('name', '').strip()
        location = adapter.get('location', '').strip()
        city = adapter.get('city', '').strip()
        
        if name:
            # Create a normalized doctor identifier
            doctor_key = f"{name.lower()}|{location.lower()}|{city.lower()}"
            doctor_hash = hashlib.md5(doctor_key.encode()).hexdigest()[:8]
            
            if doctor_hash in self.seen_doctors:
                spider.logger.debug(f"Duplicate doctor found: {name} in {location or city}")
                raise DropItem(f"Duplicate doctor: {name} in {location or city}")
            
            self.seen_doctors.add(doctor_hash)
        
        return item


class DatabasePipeline:
    """Pipeline to save data to SQLite database"""
    
    def __init__(self):
        self.db_path = 'data/doctors_database.db'
        
    def open_spider(self, spider):
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Connect to database
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()
        
        # Create table if it doesn't exist
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                speciality TEXT,
                degree TEXT,
                year_of_experience TEXT,
                location TEXT,
                city TEXT,
                dp_score TEXT,
                npv TEXT,
                consultation_fee TEXT,
                profile_url TEXT UNIQUE,
                google_map_link TEXT,
                scraped_at TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.connection.commit()
        spider.logger.info(f"Database initialized: {self.db_path}")
    
    def close_spider(self, spider):
        # Get count of records
        self.cursor.execute("SELECT COUNT(*) FROM doctors")
        count = self.cursor.fetchone()[0]
        
        self.connection.close()
        spider.logger.info(f"Database closed. Total records: {count}")
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        try:
            # Insert or replace record (avoid duplicates based on profile_url)
            self.cursor.execute('''
                INSERT OR REPLACE INTO doctors (
                    name, speciality, degree, year_of_experience, location, city,
                    dp_score, npv, consultation_fee, profile_url, google_map_link, scraped_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                adapter.get('name', ''),
                adapter.get('speciality', ''),
                adapter.get('degree', ''),
                adapter.get('year_of_experience', ''),
                adapter.get('location', ''),
                adapter.get('city', ''),
                adapter.get('dp_score', ''),
                adapter.get('npv', ''),
                adapter.get('consultation_fee', ''),
                adapter.get('profile_url', ''),
                adapter.get('google_map_link', ''),
                adapter.get('scraped_at', '')
            ))
            
            self.connection.commit()
            
        except sqlite3.Error as e:
            spider.logger.error(f"Database error: {e}")
            
        return item
