#!/usr/bin/env python3
"""
Database Analysis Script

This script provides tools to analyze the scraped doctor data,
generate reports, and export data in various formats.
"""

import sqlite3
import pandas as pd
import os
import json
from datetime import datetime
import argparse


class DatabaseAnalyzer:
    """Class to analyze the scraped doctor database"""
    
    def __init__(self, db_path="data/bangalore_doctors.db"):
        self.db_path = db_path
        self.connection = None
        
    def connect(self):
        """Connect to the database"""
        if not os.path.exists(self.db_path):
            print(f"Database not found: {self.db_path}")
            print("Please run the scraper first to create the database.")
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
        
        # Total doctors
        cursor = self.connection.cursor()
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
        
        # Doctors by area
        cursor.execute("""
            SELECT area, COUNT(*) as count 
            FROM doctors 
            WHERE area IS NOT NULL AND area != ''
            GROUP BY area 
            ORDER BY count DESC 
            LIMIT 10
        """)
        stats['top_areas'] = cursor.fetchall()
        
        # Rating distribution
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN rating >= 4.5 THEN 'Excellent (4.5+)'
                    WHEN rating >= 4.0 THEN 'Very Good (4.0-4.5)'
                    WHEN rating >= 3.5 THEN 'Good (3.5-4.0)'
                    WHEN rating >= 3.0 THEN 'Average (3.0-3.5)'
                    WHEN rating > 0 THEN 'Below Average (<3.0)'
                    ELSE 'No Rating'
                END as rating_category,
                COUNT(*) as count
            FROM doctors
            GROUP BY rating_category
            ORDER BY rating DESC
        """)
        stats['rating_distribution'] = cursor.fetchall()
        
        # Consultation fee analysis
        cursor.execute("""
            SELECT 
                AVG(consultation_fee) as avg_fee,
                MIN(consultation_fee) as min_fee,
                MAX(consultation_fee) as max_fee,
                COUNT(CASE WHEN consultation_fee > 0 THEN 1 END) as doctors_with_fee
            FROM doctors
            WHERE consultation_fee > 0
        """)
        fee_stats = cursor.fetchone()
        if fee_stats[0]:
            stats['consultation_fee'] = {
                'average': round(fee_stats[0], 2),
                'minimum': fee_stats[1],
                'maximum': fee_stats[2],
                'doctors_with_fee': fee_stats[3]
            }
        
        # Experience analysis
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN experience_years >= 20 THEN '20+ years'
                    WHEN experience_years >= 15 THEN '15-20 years'
                    WHEN experience_years >= 10 THEN '10-15 years'
                    WHEN experience_years >= 5 THEN '5-10 years'
                    WHEN experience_years > 0 THEN '1-5 years'
                    ELSE 'Not specified'
                END as experience_category,
                COUNT(*) as count
            FROM doctors
            GROUP BY experience_category
        """)
        stats['experience_distribution'] = cursor.fetchall()
        
        # Data quality metrics
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN google_map_link IS NOT NULL AND google_map_link != '' THEN 1 END) as with_maps,
                COUNT(CASE WHEN phone IS NOT NULL AND phone != '' THEN 1 END) as with_phone,
                COUNT(CASE WHEN rating > 0 THEN 1 END) as with_rating,
                COUNT(CASE WHEN consultation_fee > 0 THEN 1 END) as with_fee,
                COUNT(*) as total
            FROM doctors
        """)
        quality_stats = cursor.fetchone()
        stats['data_quality'] = {
            'with_google_maps': quality_stats[0],
            'with_phone': quality_stats[1],
            'with_rating': quality_stats[2],
            'with_consultation_fee': quality_stats[3],
            'total_records': quality_stats[4]
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
        
        print("\\nTop Specialities:")
        for speciality, count in stats['by_speciality'][:10]:
            print(f"  {speciality:<30} {count:>4} doctors")
        
        print("\\nTop Areas:")
        for area, count in stats['top_areas']:
            print(f"  {area:<30} {count:>4} doctors")
        
        print("\\nRating Distribution:")
        for category, count in stats['rating_distribution']:
            print(f"  {category:<25} {count:>4} doctors")
        
        if 'consultation_fee' in stats:
            fee = stats['consultation_fee']
            print(f"\\nConsultation Fees:")
            print(f"  Average Fee: ₹{fee['average']}")
            print(f"  Fee Range: ₹{fee['minimum']} - ₹{fee['maximum']}")
            print(f"  Doctors with Fee Info: {fee['doctors_with_fee']}")
        
        print("\\nExperience Distribution:")
        for category, count in stats['experience_distribution']:
            print(f"  {category:<15} {count:>4} doctors")
        
        quality = stats['data_quality']
        total = quality['total_records']
        print("\\nData Quality:")
        print(f"  Google Maps Links: {quality['with_google_maps']:>4}/{total} ({quality['with_google_maps']/total*100:.1f}%)")
        print(f"  Phone Numbers:     {quality['with_phone']:>4}/{total} ({quality['with_phone']/total*100:.1f}%)")
        print(f"  Ratings:           {quality['with_rating']:>4}/{total} ({quality['with_rating']/total*100:.1f}%)")
        print(f"  Consultation Fees: {quality['with_consultation_fee']:>4}/{total} ({quality['with_consultation_fee']/total*100:.1f}%)")
        
        print("\\n" + "=" * 60)
    
    def export_to_csv(self, filename=None):
        """Export all data to CSV"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/bangalore_doctors_export_{timestamp}.csv"
        
        try:
            df = pd.read_sql_query("SELECT * FROM doctors", self.connection)
            df.to_csv(filename, index=False)
            print(f"Data exported to: {filename}")
            print(f"Records exported: {len(df)}")
            return filename
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return None
    
    def search_doctors(self, speciality=None, area=None, min_rating=None, max_fee=None):
        """Search for doctors based on criteria"""
        conditions = []
        params = []
        
        if speciality:
            conditions.append("speciality LIKE ?")
            params.append(f"%{speciality}%")
        
        if area:
            conditions.append("area LIKE ?")
            params.append(f"%{area}%")
        
        if min_rating:
            conditions.append("rating >= ?")
            params.append(min_rating)
        
        if max_fee:
            conditions.append("consultation_fee <= ? AND consultation_fee > 0")
            params.append(max_fee)
        
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
    
    parser = argparse.ArgumentParser(description="Analyze scraped doctor data")
    
    parser.add_argument(
        "--db-path",
        default="data/bangalore_doctors.db",
        help="Path to the SQLite database file"
    )
    
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
        action="store_true",
        help="Search for doctors (interactive mode)"
    )
    
    parser.add_argument(
        "--speciality",
        help="Filter by speciality"
    )
    
    parser.add_argument(
        "--area",
        help="Filter by area"
    )
    
    parser.add_argument(
        "--min-rating",
        type=float,
        help="Minimum rating filter"
    )
    
    parser.add_argument(
        "--max-fee",
        type=int,
        help="Maximum consultation fee filter"
    )
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = DatabaseAnalyzer(args.db_path)
    
    if not analyzer.connect():
        return
    
    try:
        if args.summary:
            analyzer.print_summary()
        
        if args.export_csv:
            filename = None if args.export_csv == "auto" else args.export_csv
            analyzer.export_to_csv(filename)
        
        if args.search or any([args.speciality, args.area, args.min_rating, args.max_fee]):
            results = analyzer.search_doctors(
                speciality=args.speciality,
                area=args.area,
                min_rating=args.min_rating,
                max_fee=args.max_fee
            )
            
            print(f"\\nFound {len(results)} doctors matching criteria:")
            print("-" * 100)
            
            for result in results[:20]:  # Show top 20 results
                name, speciality, area, rating, fee, maps_link, profile = result
                rating_str = f"{rating:.1f}" if rating else "N/A"
                fee_str = f"₹{fee}" if fee else "N/A"
                area_str = area if area else "N/A"
                
                print(f"{name:<30} | {speciality:<20} | {area_str:<15} | ⭐{rating_str} | {fee_str}")
            
            if len(results) > 20:
                print(f"... and {len(results) - 20} more doctors")
        
        if not any([args.summary, args.export_csv, args.search, 
                   args.speciality, args.area, args.min_rating, args.max_fee]):
            parser.print_help()
    
    finally:
        analyzer.close()


if __name__ == "__main__":
    main()