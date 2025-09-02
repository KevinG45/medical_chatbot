#!/usr/bin/env python3
"""
Data consolidation script to clean and merge existing CSV files
This script will:
1. Load both CSV files
2. Clean and standardize the data
3. Remove duplicates intelligently
4. Merge compatible records
5. Output a single, clean dataset
"""

import pandas as pd
import numpy as np
import re
import hashlib
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataConsolidator:
    def __init__(self):
        self.consolidated_data = []
        
    def clean_text(self, text):
        """Clean text by removing extra whitespace and special characters"""
        if pd.isna(text) or text == '':
            return None
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', str(text)).strip()
        return text if text else None
    
    def is_valid_location(self, location):
        """Check if a location is valid and not HTML garbage"""
        if not location or pd.isna(location):
            return False
        
        location = str(location).strip()
        
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
        if location.count(',') > 8:
            return False
        
        # Check if it looks like HTML tags
        if '<' in location or '>' in location:
            return False
        
        # Check if it's all lowercase letters and commas (typical HTML tag pattern)
        if re.match(r'^[a-z,\s]+$', location) and ',' in location and len(location.split(',')) > 4:
            return False
        
        return True
    
    def extract_experience_years(self, experience_text):
        """Extract number of years from experience text"""
        if pd.isna(experience_text) or experience_text == '':
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
    
    def normalize_consultation_fee(self, fee_text):
        """Normalize consultation fee"""
        if pd.isna(fee_text) or fee_text == '':
            return None
        
        try:
            fee = float(fee_text)
            # Validate reasonable fee range
            if 0 <= fee <= 50000:
                return fee
            else:
                return None
        except (ValueError, TypeError):
            return None
    
    def normalize_dp_score(self, score_text):
        """Normalize DP score"""
        if pd.isna(score_text) or score_text == '':
            return None
        
        try:
            score = float(score_text)
            # Validate reasonable score range
            if 0 <= score <= 100:
                return score
            else:
                return None
        except (ValueError, TypeError):
            return None
    
    def create_doctor_key(self, name, location, city):
        """Create a unique key for a doctor based on name and location"""
        name = str(name).strip().lower() if name else ''
        location = str(location).strip().lower() if location else ''
        city = str(city).strip().lower() if city else ''
        
        # Create a normalized doctor identifier
        doctor_key = f"{name}|{location}|{city}"
        return hashlib.md5(doctor_key.encode()).hexdigest()[:12]
    
    def load_and_clean_csv(self, filepath, filename):
        """Load and clean a CSV file"""
        logger.info(f"Loading and cleaning {filename}...")
        
        try:
            df = pd.read_csv(filepath)
            logger.info(f"Loaded {len(df)} records from {filename}")
            
            # Standardize column names and clean data
            cleaned_records = []
            
            for _, row in df.iterrows():
                # Extract and clean basic fields
                name = self.clean_text(row.get('name'))
                if not name:
                    continue  # Skip records without names
                
                speciality = self.clean_text(row.get('speciality'))
                degree = self.clean_text(row.get('degree'))
                city = self.clean_text(row.get('city', 'Bangalore'))
                profile_url = self.clean_text(row.get('profile_url'))
                
                # Clean location
                location = self.clean_text(row.get('location'))
                if location and not self.is_valid_location(location):
                    location = None  # Remove garbage location data
                
                # Clean experience
                experience = self.extract_experience_years(row.get('year_of_experience'))
                
                # Clean scores and fees
                consultation_fee = self.normalize_consultation_fee(row.get('consultation_fee'))
                dp_score = self.normalize_dp_score(row.get('dp_score'))
                npv = row.get('npv') if not pd.isna(row.get('npv')) else None
                
                # Google maps link
                google_map_link = self.clean_text(row.get('google_map_link'))
                
                # Scraped timestamp
                scraped_at = self.clean_text(row.get('scraped_at'))
                
                # Create cleaned record
                cleaned_record = {
                    'name': name,
                    'speciality': speciality,
                    'degree': degree,
                    'year_of_experience': experience,
                    'location': location,
                    'city': city,
                    'dp_score': dp_score,
                    'npv': npv,
                    'consultation_fee': consultation_fee,
                    'profile_url': profile_url,
                    'google_map_link': google_map_link,
                    'scraped_at': scraped_at,
                    'source_file': filename,
                    'doctor_key': self.create_doctor_key(name, location, city)
                }
                
                cleaned_records.append(cleaned_record)
            
            logger.info(f"Cleaned {len(cleaned_records)} valid records from {filename}")
            return cleaned_records
            
        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")
            return []
    
    def merge_duplicate_records(self, records):
        """Merge records that represent the same doctor"""
        logger.info("Merging duplicate records...")
        
        # Group by doctor_key
        doctor_groups = {}
        for record in records:
            key = record['doctor_key']
            if key not in doctor_groups:
                doctor_groups[key] = []
            doctor_groups[key].append(record)
        
        merged_records = []
        duplicate_count = 0
        
        for key, group in doctor_groups.items():
            if len(group) == 1:
                # No duplicates, keep as is
                merged_records.append(group[0])
            else:
                # Merge duplicates
                duplicate_count += len(group) - 1
                merged_record = self.merge_doctor_records(group)
                merged_records.append(merged_record)
        
        logger.info(f"Merged {duplicate_count} duplicate records")
        logger.info(f"Final count: {len(merged_records)} unique doctors")
        
        return merged_records
    
    def merge_doctor_records(self, records):
        """Merge multiple records of the same doctor"""
        # Start with the first record as base
        merged = records[0].copy()
        
        # Collect all specialities
        specialities = set()
        for record in records:
            if record['speciality']:
                specialities.add(record['speciality'])
        
        # Merge logic: take the best available value for each field
        for record in records:
            # Take non-null values when available
            for field in ['degree', 'location', 'google_map_link']:
                if not merged[field] and record[field]:
                    merged[field] = record[field]
            
            # Take highest dp_score
            if record['dp_score'] and (not merged['dp_score'] or record['dp_score'] > merged['dp_score']):
                merged['dp_score'] = record['dp_score']
            
            # Take highest npv
            if record['npv'] and (not merged['npv'] or record['npv'] > merged['npv']):
                merged['npv'] = record['npv']
            
            # Take non-zero consultation_fee
            if record['consultation_fee'] and record['consultation_fee'] > 0:
                if not merged['consultation_fee'] or merged['consultation_fee'] == 0:
                    merged['consultation_fee'] = record['consultation_fee']
            
            # Take highest experience
            if record['year_of_experience'] and (not merged['year_of_experience'] or record['year_of_experience'] > merged['year_of_experience']):
                merged['year_of_experience'] = record['year_of_experience']
        
        # Set merged specialities (join multiple if needed)
        merged['speciality'] = ', '.join(sorted(specialities)) if specialities else None
        
        # Update source files
        source_files = set()
        for record in records:
            source_files.add(record['source_file'])
        merged['source_file'] = ', '.join(sorted(source_files))
        
        return merged
    
    def consolidate_data(self, csv_files):
        """Main consolidation method"""
        logger.info("Starting data consolidation...")
        
        all_records = []
        
        # Load and clean all CSV files
        for filepath, filename in csv_files:
            records = self.load_and_clean_csv(filepath, filename)
            all_records.extend(records)
        
        logger.info(f"Total records loaded: {len(all_records)}")
        
        # Merge duplicates
        consolidated_records = self.merge_duplicate_records(all_records)
        
        # Convert to DataFrame
        df = pd.DataFrame(consolidated_records)
        
        # Sort by name
        df = df.sort_values(['name', 'speciality'])
        
        # Reorder columns
        column_order = [
            'name', 'speciality', 'degree', 'year_of_experience', 
            'location', 'city', 'dp_score', 'npv', 'consultation_fee',
            'profile_url', 'google_map_link', 'scraped_at', 'source_file'
        ]
        
        # Only include columns that exist
        existing_columns = [col for col in column_order if col in df.columns]
        df = df[existing_columns]
        
        return df

def main():
    """Main function"""
    consolidator = DataConsolidator()
    
    # Define CSV files to consolidate
    csv_files = [
        ("/home/runner/work/medical_chatbot/medical_chatbot/medical_chatbot/src/Web_Scraping/practo_scraper/bangalore_enhanced.csv", "bangalore_enhanced.csv"),
        ("/home/runner/work/medical_chatbot/medical_chatbot/medical_chatbot/src/Web_Scraping/practo_scraper/data/cleaned_doctors_full.csv", "cleaned_doctors_full.csv")
    ]
    
    # Consolidate data
    consolidated_df = consolidator.consolidate_data(csv_files)
    
    # Save consolidated data
    output_dir = "/home/runner/work/medical_chatbot/medical_chatbot/medical_chatbot/src/Web_Scraping/practo_scraper/data"
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"{output_dir}/consolidated_doctors_{timestamp}.csv"
    
    consolidated_df.to_csv(output_file, index=False, encoding='utf-8')
    logger.info(f"Consolidated data saved to: {output_file}")
    
    # Also save as latest
    latest_file = f"{output_dir}/consolidated_doctors_latest.csv"
    consolidated_df.to_csv(latest_file, index=False, encoding='utf-8')
    logger.info(f"Latest consolidated data saved to: {latest_file}")
    
    # Print summary statistics
    logger.info("\n" + "="*60)
    logger.info("CONSOLIDATION SUMMARY")
    logger.info("="*60)
    logger.info(f"Total unique doctors: {len(consolidated_df)}")
    logger.info(f"Specialities covered: {consolidated_df['speciality'].nunique()}")
    logger.info(f"Records with valid location: {consolidated_df['location'].notna().sum()}")
    logger.info(f"Records with experience data: {consolidated_df['year_of_experience'].notna().sum()}")
    logger.info(f"Records with consultation fee: {consolidated_df['consultation_fee'].notna().sum()}")
    logger.info(f"Records with DP score: {consolidated_df['dp_score'].notna().sum()}")
    
    # Show top specialities
    top_specialities = consolidated_df['speciality'].value_counts().head(10)
    logger.info(f"\nTop 10 specialities:")
    for spec, count in top_specialities.items():
        logger.info(f"  {spec}: {count}")

if __name__ == "__main__":
    main()