"""
Configuration settings for Bangalore doctors scraping
"""

# Target configuration
TARGET_CITY = 'Bangalore'

# Comprehensive list of medical specialities available on Practo
SPECIALITIES = [
    # Primary care
    'General Physician',
    'Family Medicine',
    
    # Cardiology
    'Cardiologist',
    'Cardiac Surgeon',
    
    # Neurology
    'Neurologist',
    'Neurosurgeon',
    
    # Orthopedics
    'Orthopedist',
    'Orthopedic Surgeon',
    
    # Gynecology & Obstetrics
    'Gynecologist',
    'Obstetrician',
    'Infertility Specialist',
    
    # Pediatrics
    'Pediatrician',
    'Pediatric Surgeon',
    
    # Surgery
    'General Surgeon',
    'Plastic Surgeon',
    'Cosmetic Surgeon',
    'Bariatric Surgeon',
    'Vascular Surgeon',
    'Thoracic Surgeon',
    
    # Gastroenterology
    'Gastroenterologist',
    'Hepatologist',
    
    # Pulmonology
    'Pulmonologist',
    'Chest Physician',
    
    # Dermatology
    'Dermatologist',
    'Cosmetologist',
    
    # Ophthalmology
    'Ophthalmologist',
    'Eye Surgeon',
    
    # ENT
    'ENT Specialist',
    'ENT Surgeon',
    
    # Urology
    'Urologist',
    'Andrologist',
    
    # Oncology
    'Oncologist',
    'Radiation Oncologist',
    'Surgical Oncologist',
    
    # Endocrinology
    'Endocrinologist',
    'Diabetologist',
    
    # Nephrology
    'Nephrologist',
    
    # Rheumatology
    'Rheumatologist',
    
    # Mental Health
    'Psychiatrist',
    'Psychologist',
    'Counsellor',
    
    # Dentistry
    'Dentist',
    'Oral Surgeon',
    'Orthodontist',
    'Periodontist',
    'Endodontist',
    
    # Alternative Medicine
    'Homeopath',
    'Ayurveda',
    'Unani',
    
    # Allied Health
    'Physiotherapist',
    'Dietitian/Nutritionist',
    'Speech Therapist',
    'Audiologist',
    
    # Emergency & Critical Care
    'Emergency Medicine Physician',
    'Intensivist',
    'Anesthesiologist',
    
    # Radiology & Pathology
    'Radiologist',
    'Pathologist',
    
    # Geriatrics
    'Geriatrician',
    
    # Other specialists
    'Sexologist',
    'Pain Management Specialist',
    'Sleep Medicine Specialist',
    'Addiction Medicine Specialist',
]

# Scraping configuration
SCRAPING_CONFIG = {
    'delay_between_requests': 2,  # seconds
    'max_pages_per_speciality': 100,  # prevent infinite loops
    'max_retries': 3,
    'timeout': 30,  # seconds
    'concurrent_requests': 2,  # be respectful to the server
}

# Database configuration  
DATABASE_CONFIG = {
    'type': 'sqlite',  # 'sqlite' or 'postgresql'
    'sqlite_path': '../data/bangalore_doctors.db',
    # For PostgreSQL (uncomment and configure if needed):
    # 'host': 'localhost',
    # 'port': 5432,
    # 'database': 'medical_chatbot',
    # 'user': 'your_username',
    # 'password': 'your_password'
}

# Output configuration
OUTPUT_CONFIG = {
    'csv_file': '../data/bangalore_doctors.csv',
    'json_file': '../data/bangalore_doctors.json',
    'excel_file': '../data/bangalore_doctors.xlsx',
}

# Browser configuration for Playwright
BROWSER_CONFIG = {
    'headless': True,
    'viewport': {'width': 1920, 'height': 1080},
    'timeout': 30000,  # milliseconds
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}