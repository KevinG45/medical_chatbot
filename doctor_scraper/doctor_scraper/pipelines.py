"""
Define your item pipelines here

Don't forget to add your pipeline to the ITEM_PIPELINES setting
See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
"""

import sqlite3
import json
import csv
import os
import re
from datetime import datetime
from itemadapter import ItemAdapter


class ValidationPipeline:
    """Pipeline to validate scraped items"""
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Validate required fields
        name = adapter.get('name', '').strip()
        if not name or len(name) < 2:
            spider.logger.warning(f"Dropping item due to invalid name: {name}")
            return None
            
        speciality = adapter.get('speciality', '').strip()
        if not speciality:
            spider.logger.warning(f"Dropping item due to missing speciality for: {name}")
            return None
            
        profile_url = adapter.get('profile_url', '')
        if not profile_url or not profile_url.startswith('https://'):
            spider.logger.warning(f"Dropping item due to invalid profile URL for: {name}")
            return None
        
        return item


class CleaningPipeline:
    """Pipeline to clean and normalize scraped data"""
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Clean text fields
        text_fields = ['name', 'speciality', 'qualifications', 'clinic_name', 'area', 'full_address', 'about']
        for field in text_fields:
            value = adapter.get(field)
            if value:
                # Remove extra whitespace and normalize
                cleaned = ' '.join(str(value).split())
                adapter[field] = cleaned
        
        # Clean and validate experience years
        experience = adapter.get('experience_years')
        if experience:
            # Extract numeric value from experience text
            years = self.extract_years(str(experience))
            adapter['experience_years'] = years
        
        # Clean and validate rating
        rating = adapter.get('rating')
        if rating:
            cleaned_rating = self.extract_rating(str(rating))
            adapter['rating'] = cleaned_rating
        
        # Clean and validate consultation fee
        fee = adapter.get('consultation_fee')
        if fee:
            cleaned_fee = self.extract_fee(str(fee))
            adapter['consultation_fee'] = cleaned_fee
        
        # Clean reviews count
        reviews = adapter.get('reviews_count')
        if reviews:
            cleaned_reviews = self.extract_number(str(reviews))
            adapter['reviews_count'] = cleaned_reviews
        
        # Add metadata
        adapter['scraped_at'] = datetime.now().isoformat()
        adapter['source'] = 'practo.com'
        
        return item
    
    def extract_years(self, text):
        """Extract years of experience from text"""
        match = re.search(r'(\d+)', text)
        return int(match.group(1)) if match else 0
    
    def extract_rating(self, text):
        """Extract rating value from text"""
        match = re.search(r'(\d+\.?\d*)', text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return 0.0
        return 0.0
    
    def extract_fee(self, text):
        """Extract consultation fee from text"""
        # Remove currency symbols and extract number
        text = re.sub(r'[₹$,]', '', text)
        match = re.search(r'(\d+)', text)
        return int(match.group(1)) if match else 0
    
    def extract_number(self, text):
        """Extract number from text"""
        match = re.search(r'(\d+)', text)
        return int(match.group(1)) if match else 0


class DatabasePipeline:
    """Pipeline to save data to SQLite database"""
    
    def __init__(self):
        self.db_path = None
        self.connection = None
        self.cursor = None
    
    def open_spider(self, spider):
        # Import config
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        from config import DATABASE_CONFIG
        
        # Create data directory if it doesn't exist
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        # Setup database
        self.db_path = os.path.join(data_dir, 'bangalore_doctors.db')
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()
        
        # Create table
        self.create_table()
        spider.logger.info(f"Database initialized: {self.db_path}")
    
    def create_table(self):
        """Create the doctors table if it doesn't exist"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            speciality TEXT NOT NULL,
            qualifications TEXT,
            experience_years INTEGER,
            clinic_name TEXT,
            area TEXT,
            city TEXT,
            full_address TEXT,
            phone TEXT,
            rating REAL,
            reviews_count INTEGER,
            patient_stories INTEGER,
            consultation_fee INTEGER,
            available_today TEXT,
            next_available_slot TEXT,
            profile_url TEXT UNIQUE,
            google_map_link TEXT,
            about TEXT,
            services TEXT,
            awards TEXT,
            scraped_at TEXT,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.cursor.execute(create_table_sql)
        self.connection.commit()
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        try:
            # Insert or replace record (avoid duplicates based on profile_url)
            insert_sql = """
            INSERT OR REPLACE INTO doctors (
                name, speciality, qualifications, experience_years, clinic_name, area, city,
                full_address, phone, rating, reviews_count, patient_stories, consultation_fee,
                available_today, next_available_slot, profile_url, google_map_link, about,
                services, awards, scraped_at, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            values = (
                adapter.get('name', ''),
                adapter.get('speciality', ''),
                adapter.get('qualifications', ''),
                adapter.get('experience_years', 0),
                adapter.get('clinic_name', ''),
                adapter.get('area', ''),
                adapter.get('city', ''),
                adapter.get('full_address', ''),
                adapter.get('phone', ''),
                adapter.get('rating', 0.0),
                adapter.get('reviews_count', 0),
                adapter.get('patient_stories', 0),
                adapter.get('consultation_fee', 0),
                adapter.get('available_today', ''),
                adapter.get('next_available_slot', ''),
                adapter.get('profile_url', ''),
                adapter.get('google_map_link', ''),
                adapter.get('about', ''),
                adapter.get('services', ''),
                adapter.get('awards', ''),
                adapter.get('scraped_at', ''),
                adapter.get('source', '')
            )
            
            self.cursor.execute(insert_sql, values)
            self.connection.commit()
            
        except sqlite3.Error as e:
            spider.logger.error(f"Database error: {e}")
            
        return item
    
    def close_spider(self, spider):
        # Get count of records
        self.cursor.execute("SELECT COUNT(*) FROM doctors")
        count = self.cursor.fetchone()[0]
        
        self.connection.close()
        spider.logger.info(f"Database closed. Total records: {count}")


class ExportPipeline:
    """Pipeline to export data to various formats"""
    
    def __init__(self):
        self.items = []
    
    def process_item(self, item, spider):
        self.items.append(dict(item))
        return item
    
    def close_spider(self, spider):
        if not self.items:
            spider.logger.info("No items to export")
            return
        
        # Create data directory if it doesn't exist
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export to CSV
        csv_path = os.path.join(data_dir, f'bangalore_doctors_{timestamp}.csv')
        self.export_csv(csv_path, spider)
        
        # Export to JSON
        json_path = os.path.join(data_dir, f'bangalore_doctors_{timestamp}.json')
        self.export_json(json_path, spider)
        
        spider.logger.info(f"Exported {len(self.items)} items to CSV and JSON")
    
    def export_csv(self, filepath, spider):
        """Export items to CSV file"""
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                if self.items:
                    fieldnames = self.items[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(self.items)
                    spider.logger.info(f"CSV export successful: {filepath}")
        except Exception as e:
            spider.logger.error(f"CSV export failed: {e}")
    
    def export_json(self, filepath, spider):
        """Export items to JSON file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as jsonfile:
                json.dump(self.items, jsonfile, indent=2, ensure_ascii=False)
                spider.logger.info(f"JSON export successful: {filepath}")
        except Exception as e:
            spider.logger.error(f"JSON export failed: {e}")