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
        if not adapter.get('name'):
            raise DropItem(f"Missing name in {item}")
            
        # Skip if consultation fee is missing
        if not adapter.get('consultation_fee'):
            raise DropItem(f"Missing consultation fee in {item}")
            
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
            return 0
        
        # Look for patterns like "5 years", "10+ years", etc.
        pattern = r'(\d+)(?:\+)?\s*(?:years?|yrs?)'
        match = re.search(pattern, str(experience_text), re.IGNORECASE)
        
        if match:
            return int(match.group(1))
        
        # Look for just numbers
        pattern = r'(\d+)'
        match = re.search(pattern, str(experience_text))
        if match:
            return int(match.group(1))
        
        return 0
    
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
            r'[a-z]+,[a-z]+,[a-z]+,[a-z]+',  # Multiple comma-separated lowercase words
            r'^(a|abbr|acronym|address|applet|article|aside|audio|b|big|blockquote)$',  # Single HTML tags
        ]
        
        for pattern in html_patterns:
            if re.search(pattern, location, re.IGNORECASE):
                return False
        
        # Check if it's suspiciously long (garbage data tends to be very long)
        if len(location) > 200:
            return False
            
        # Check if it contains too many commas (likely tag list)
        if location.count(',') > 5:
            return False
        
        # Check if it looks like HTML tags
        if '<' in location or '>' in location:
            return False
        
        return True
    
    def recover_location_from_map_link(self, map_link, city):
        """Try to recover location information from Google Maps link"""
        if not map_link:
            return city or "Location Unknown"
        
        # Extract coordinates from map link
        coord_pattern = r'maps/place/(-?\d+\.?\d*),(-?\d+\.?\d*)'
        match = re.search(coord_pattern, str(map_link))
        if match:
            try:
                lat, lng = float(match.group(1)), float(match.group(2))
                # For now, just return city with coordinates info
                return f"{city} ({lat:.3f}, {lng:.3f})"
            except ValueError:
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
