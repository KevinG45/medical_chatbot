#!/usr/bin/env python3
"""
Simple Database Analysis Script (No external dependencies)

This script provides tools to analyze the scraped doctor data
using only built-in Python libraries.
"""

import sqlite3
import os
import json
import csv
from datetime import datetime
import argparse


class SimpleAnalyzer:
    """Simple analyzer using only built-in libraries"""
    
    def __init__(self, db_path="data/bangalore_doctors.db"):
        self.db_path = db_path
        self.connection = None
        
    def connect(self):
        """Connect to the database"""
        if not os.path.exists(self.db_path):
            print(f"Database not found: {self.db_path}")
            print("Please run the demo first: python demo.py")
            return False
        
        try:
            self.connection = sqlite3.connect(self.db_path)
            return True
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return False
    
    def get_summary_stats(self):
        """Get summary statistics about the scraped data"""
        if not self.connection:
            return None
        
        stats = {}
        cursor = self.connection.cursor()
        
        # Total doctors
        cursor.execute("SELECT COUNT(*) FROM doctors")
        stats['total_doctors'] = cursor.fetchone()[0]
        
        # Doctors by speciality
        cursor.execute("""
            SELECT speciality, COUNT(*) as count 
            FROM doctors 
            GROUP BY speciality 
            ORDER BY count DESC
        """)
        stats['by_speciality'] = cursor.fetchall()
        
        # Top areas
        cursor.execute("""
            SELECT area, COUNT(*) as count 
            FROM doctors 
            WHERE area IS NOT NULL AND area != ''
            GROUP BY area 
            ORDER BY count DESC 
            LIMIT 10
        """)
        stats['top_areas'] = cursor.fetchall()
        
        # Data quality
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN google_map_link IS NOT NULL AND google_map_link != '' THEN 1 END) as with_maps,
                COUNT(CASE WHEN phone IS NOT NULL AND phone != '' THEN 1 END) as with_phone,
                COUNT(CASE WHEN rating > 0 THEN 1 END) as with_rating,
                COUNT(*) as total
            FROM doctors
        """)
        quality_stats = cursor.fetchone()
        stats['data_quality'] = {
            'with_google_maps': quality_stats[0],
            'with_phone': quality_stats[1],
            'with_rating': quality_stats[2],
            'total_records': quality_stats[3]
        }
        
        return stats
    
    def print_summary(self):
        """Print a formatted summary of the database"""
        stats = self.get_summary_stats()
        if not stats:
            return
        
        print("=" * 60)
        print("BANGALORE DOCTORS DATABASE SUMMARY")
        print("=" * 60)
        
        print(f"\\nTotal Doctors: {stats['total_doctors']:,}")
        
        print("\\nSpecialities:")
        for speciality, count in stats['by_speciality']:
            print(f"  {speciality:<30} {count:>4} doctors")
        
        if stats['top_areas']:
            print("\\nTop Areas:")
            for area, count in stats['top_areas']:
                print(f"  {area:<30} {count:>4} doctors")
        
        quality = stats['data_quality']
        total = quality['total_records']
        print("\\nData Quality:")
        print(f"  Google Maps Links: {quality['with_google_maps']:>4}/{total} ({quality['with_google_maps']/total*100:.1f}%)")
        print(f"  Phone Numbers:     {quality['with_phone']:>4}/{total} ({quality['with_phone']/total*100:.1f}%)")
        print(f"  Ratings:           {quality['with_rating']:>4}/{total} ({quality['with_rating']/total*100:.1f}%)")
        
        print("\\n" + "=" * 60)
    
    def export_to_csv(self, filename=None):
        """Export all data to CSV using built-in csv module"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/bangalore_doctors_export_{timestamp}.csv"
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM doctors")
            
            # Get column names
            columns = [description[0] for description in cursor.description]
            
            # Write to CSV
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(columns)  # Header
                writer.writerows(cursor.fetchall())  # Data
            
            cursor.execute("SELECT COUNT(*) FROM doctors")
            count = cursor.fetchone()[0]
            
            print(f"Data exported to: {filename}")
            print(f"Records exported: {count}")
            return filename
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return None
    
    def search_doctors(self, speciality=None, area=None):
        """Search for doctors based on criteria"""
        conditions = []
        params = []
        
        if speciality:
            conditions.append("speciality LIKE ?")
            params.append(f"%{speciality}%")
        
        if area:
            conditions.append("area LIKE ?")
            params.append(f"%{area}%")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT name, speciality, area, rating, consultation_fee, google_map_link, profile_url
            FROM doctors 
            WHERE {where_clause}
            ORDER BY rating DESC
        """
        
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        return results
    
    def close(self):
        """Close the database connection"""
        if self.connection:
            self.connection.close()


def main():
    """Main function to handle command line arguments"""
    
    parser = argparse.ArgumentParser(description="Analyze scraped doctor data (Simple version)")
    
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show database summary statistics"
    )
    
    parser.add_argument(
        "--export-csv",
        metavar="FILENAME",
        nargs="?",
        const="auto",
        help="Export data to CSV file"
    )
    
    parser.add_argument(
        "--search",
        nargs=2,
        metavar=("TYPE", "VALUE"),
        help="Search doctors by 'speciality VALUE' or 'area VALUE'"
    )
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = SimpleAnalyzer()
    
    if not analyzer.connect():
        return
    
    try:
        if args.summary:
            analyzer.print_summary()
        
        if args.export_csv:
            filename = None if args.export_csv == "auto" else args.export_csv
            analyzer.export_to_csv(filename)
        
        if args.search:
            search_type, search_value = args.search
            
            if search_type.lower() == "speciality":
                results = analyzer.search_doctors(speciality=search_value)
            elif search_type.lower() == "area":
                results = analyzer.search_doctors(area=search_value)
            else:
                print("Search type must be 'speciality' or 'area'")
                return
            
            print(f"\\nFound {len(results)} doctors matching criteria:")
            print("-" * 80)
            
            for result in results:
                name, speciality, area, rating, fee, maps_link, profile = result
                rating_str = f"{rating:.1f}" if rating else "N/A"
                fee_str = f"₹{fee}" if fee else "N/A"
                area_str = area if area else "N/A"
                
                print(f"{name} | {speciality} | {area_str} | ⭐{rating_str} | {fee_str}")
                if maps_link:
                    print(f"  📍 {maps_link}")
                print()
        
        if not any([args.summary, args.export_csv, args.search]):
            # Show default info
            analyzer.print_summary()
            print("\\nAvailable commands:")
            print("  --summary              Show database summary")
            print("  --export-csv          Export data to CSV")
            print("  --search speciality X  Search by speciality")
            print("  --search area X        Search by area")
    
    finally:
        analyzer.close()


if __name__ == "__main__":
    main()