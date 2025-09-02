#!/usr/bin/env python3
"""
Demo script to test the medical chatbot doctor scraper

This script demonstrates the basic functionality without requiring
external dependencies that might not be available.
"""

import os
import sys
import sqlite3
import json
from datetime import datetime

def create_sample_database():
    """Create a sample database with demo data"""
    
    # Create data directory
    os.makedirs('data', exist_ok=True)
    
    # Connect to database
    db_path = 'data/bangalore_doctors.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table
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
    cursor.execute(create_table_sql)
    
    # Sample doctors data
    sample_doctors = [
        {
            'name': 'Dr. Rajesh Kumar',
            'speciality': 'Cardiologist',
            'qualifications': 'MBBS, MD (Cardiology)',
            'experience_years': 15,
            'clinic_name': 'Heart Care Clinic',
            'area': 'Koramangala',
            'city': 'Bangalore',
            'full_address': '123 Heart Care Clinic, Koramangala, Bangalore - 560034',
            'phone': '+91-9876543210',
            'rating': 4.5,
            'reviews_count': 250,
            'patient_stories': 180,
            'consultation_fee': 800,
            'available_today': 'Yes',
            'next_available_slot': '2:00 PM',
            'profile_url': 'https://www.practo.com/bangalore/doctor/dr-rajesh-kumar-cardiologist',
            'google_map_link': 'https://www.google.com/maps?q=12.9351,77.6101',
            'about': 'Experienced cardiologist specializing in interventional cardiology',
            'services': 'ECG; Echo; Angioplasty; Heart Surgery Consultation',
            'awards': 'Best Doctor Award 2023',
            'scraped_at': datetime.now().isoformat(),
            'source': 'practo.com'
        },
        {
            'name': 'Dr. Priya Sharma',
            'speciality': 'Dermatologist',
            'qualifications': 'MBBS, MD (Dermatology)',
            'experience_years': 10,
            'clinic_name': 'Skin Plus Clinic',
            'area': 'Indiranagar',
            'city': 'Bangalore',
            'full_address': '456 Skin Plus Clinic, Indiranagar, Bangalore - 560038',
            'phone': '+91-9876543211',
            'rating': 4.7,
            'reviews_count': 320,
            'patient_stories': 280,
            'consultation_fee': 600,
            'available_today': 'No',
            'next_available_slot': 'Tomorrow 10:00 AM',
            'profile_url': 'https://www.practo.com/bangalore/doctor/dr-priya-sharma-dermatologist',
            'google_map_link': 'https://www.google.com/maps?q=12.9716,77.6412',
            'about': 'Specialist in cosmetic dermatology and skin disorders',
            'services': 'Acne Treatment; Hair Loss Treatment; Laser Therapy; Chemical Peels',
            'awards': 'Excellence in Dermatology 2022',
            'scraped_at': datetime.now().isoformat(),
            'source': 'practo.com'
        },
        {
            'name': 'Dr. Amit Patel',
            'speciality': 'General Physician',
            'qualifications': 'MBBS, MD (Internal Medicine)',
            'experience_years': 12,
            'clinic_name': 'City Health Center',
            'area': 'Jayanagar',
            'city': 'Bangalore',
            'full_address': '789 City Health Center, Jayanagar, Bangalore - 560011',
            'phone': '+91-9876543212',
            'rating': 4.2,
            'reviews_count': 450,
            'patient_stories': 350,
            'consultation_fee': 400,
            'available_today': 'Yes',
            'next_available_slot': '4:30 PM',
            'profile_url': 'https://www.practo.com/bangalore/doctor/dr-amit-patel-general-physician',
            'google_map_link': 'https://www.google.com/maps?q=12.9279,77.5937',
            'about': 'General physician with expertise in preventive healthcare',
            'services': 'Health Checkups; Diabetes Management; Hypertension Treatment; Vaccination',
            'awards': '',
            'scraped_at': datetime.now().isoformat(),
            'source': 'practo.com'
        }
    ]
    
    # Insert sample data
    insert_sql = """
    INSERT OR REPLACE INTO doctors (
        name, speciality, qualifications, experience_years, clinic_name, area, city,
        full_address, phone, rating, reviews_count, patient_stories, consultation_fee,
        available_today, next_available_slot, profile_url, google_map_link, about,
        services, awards, scraped_at, source
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    for doctor in sample_doctors:
        values = (
            doctor['name'], doctor['speciality'], doctor['qualifications'], 
            doctor['experience_years'], doctor['clinic_name'], doctor['area'], 
            doctor['city'], doctor['full_address'], doctor['phone'], 
            doctor['rating'], doctor['reviews_count'], doctor['patient_stories'], 
            doctor['consultation_fee'], doctor['available_today'], 
            doctor['next_available_slot'], doctor['profile_url'], 
            doctor['google_map_link'], doctor['about'], doctor['services'], 
            doctor['awards'], doctor['scraped_at'], doctor['source']
        )
        cursor.execute(insert_sql, values)
    
    conn.commit()
    conn.close()
    
    print(f"✓ Sample database created: {db_path}")
    print(f"✓ Added {len(sample_doctors)} sample doctors")
    
    return db_path

def test_database_functionality(db_path):
    """Test basic database operations"""
    
    print("\\n--- Testing Database Functionality ---")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Test 1: Count total doctors
    cursor.execute("SELECT COUNT(*) FROM doctors")
    total = cursor.fetchone()[0]
    print(f"✓ Total doctors in database: {total}")
    
    # Test 2: Get doctors by speciality
    cursor.execute("SELECT COUNT(*) FROM doctors WHERE speciality = 'Cardiologist'")
    cardiologists = cursor.fetchone()[0]
    print(f"✓ Cardiologists found: {cardiologists}")
    
    # Test 3: Get doctors with Google Maps links
    cursor.execute("SELECT COUNT(*) FROM doctors WHERE google_map_link IS NOT NULL AND google_map_link != ''")
    with_maps = cursor.fetchone()[0]
    print(f"✓ Doctors with Google Maps links: {with_maps}")
    
    # Test 4: Find top rated doctors
    cursor.execute("SELECT name, speciality, rating FROM doctors ORDER BY rating DESC LIMIT 3")
    top_doctors = cursor.fetchall()
    print("\\n✓ Top rated doctors:")
    for name, speciality, rating in top_doctors:
        print(f"   {name} ({speciality}) - ⭐{rating}")
    
    # Test 5: Search functionality
    search_area = "Koramangala"
    cursor.execute("SELECT name, area, google_map_link FROM doctors WHERE area LIKE ?", (f"%{search_area}%",))
    local_doctors = cursor.fetchall()
    print(f"\\n✓ Doctors in {search_area}:")
    for name, area, maps_link in local_doctors:
        print(f"   {name} - {area}")
        print(f"   Maps: {maps_link}")
    
    conn.close()

def demonstrate_use_cases():
    """Demonstrate key use cases for the medical chatbot"""
    
    print("\\n--- Medical Chatbot Use Cases ---")
    
    print("\\n1. SYMPTOM-BASED RECOMMENDATION:")
    print("   User: 'I have chest pain and shortness of breath'")
    print("   → Chatbot recommends: Cardiologists in user's area")
    print("   → Provides: Google Maps links for navigation")
    
    print("\\n2. LOCATION-BASED SEARCH:")
    print("   User: 'Find dermatologists near Indiranagar'")
    print("   → Chatbot shows: Dr. Priya Sharma - Skin Plus Clinic")
    print("   → Includes: Rating (4.7⭐), Fee (₹600), Availability")
    
    print("\\n3. SPECIALTY FILTERING:")
    print("   User: 'I need a general physician for routine checkup'")
    print("   → Chatbot finds: General physicians sorted by rating/proximity")
    print("   → Shows: Available time slots and contact information")
    
    print("\\n4. RATING & REVIEW BASED:")
    print("   User: 'Best rated doctors for diabetes management'")
    print("   → Chatbot filters: High-rated doctors with diabetes expertise")
    print("   → Prioritizes: Experience and patient feedback")

def show_project_structure():
    """Show the project structure"""
    
    print("\\n--- Project Structure ---")
    print("""
medical_chatbot/
├── README.md                          # Project documentation
├── requirements.txt                   # Python dependencies
├── config.py                         # Configuration settings
├── run_scraper.py                    # Main scraper runner
├── analyze_data.py                   # Data analysis tools
├── demo.py                           # This demo script
├── data/                             # Scraped data storage
│   ├── bangalore_doctors.db          # SQLite database
│   ├── bangalore_doctors_*.csv       # CSV exports
│   └── bangalore_doctors_*.json      # JSON exports
├── logs/                             # Scraper logs
│   └── scraper.log
└── doctor_scraper/                   # Scrapy project
    ├── scrapy.cfg                    # Scrapy config
    └── doctor_scraper/
        ├── __init__.py
        ├── items.py                  # Data structure definitions
        ├── settings.py               # Scrapy settings
        ├── pipelines.py              # Data processing pipelines
        └── spiders/
            ├── __init__.py
            └── bangalore_doctors.py   # Main spider
    """)

def main():
    """Main demo function"""
    
    print("=" * 60)
    print("MEDICAL CHATBOT - BANGALORE DOCTOR SCRAPER DEMO")
    print("=" * 60)
    
    print("\\nThis demo shows the functionality of the medical chatbot")
    print("doctor scraper without requiring external dependencies.")
    
    # Create sample database
    print("\\n1. Creating sample database...")
    db_path = create_sample_database()
    
    # Test database functionality
    test_database_functionality(db_path)
    
    # Show use cases
    demonstrate_use_cases()
    
    # Show project structure
    show_project_structure()
    
    print("\\n--- Next Steps ---")
    print("\\n1. INSTALL DEPENDENCIES:")
    print("   pip install -r requirements.txt")
    print("   playwright install chromium")
    
    print("\\n2. RUN THE SCRAPER:")
    print("   python run_scraper.py --setup    # Setup environment")
    print("   python run_scraper.py --run      # Start scraping")
    
    print("\\n3. ANALYZE THE DATA:")
    print("   python analyze_data.py --summary # View statistics")
    print("   python analyze_data.py --export-csv # Export to CSV")
    
    print("\\n4. INTEGRATION WITH CHATBOT:")
    print("   - Use the SQLite database as the data source")
    print("   - Implement symptom → speciality mapping")
    print("   - Add location-based filtering")
    print("   - Use Google Maps links for navigation")
    
    print("\\n✓ Demo completed successfully!")
    print(f"✓ Sample database available at: {db_path}")
    print("✓ Ready for full scraping and chatbot integration")

if __name__ == "__main__":
    main()