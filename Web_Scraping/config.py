"""
Configuration file for Practo scraper
"""

# Scraping configuration
# Focus on Bangalore as requested in the issue
CITIES = ['Bangalore']  # Changed from multiple cities to focus on Bangalore only

SPECIALITIES = [
    'Cardiologist', 'Chiropractor', 'Dentist', 'Dermatologist', 
    'Dietitian/Nutritionist', 'Gastroenterologist', 'bariatric surgeon', 
    'Gynecologist', 'Infertility Specialist', 'Neurologist', 'Neurosurgeon', 
    'Ophthalmologist', 'Orthopedist', 'Pediatrician', 'Physiotherapist', 
    'Psychiatrist', 'Pulmonologist', 'Rheumatologist', 'Urologist',
    # Additional specialities to improve coverage
    'General Physician', 'ENT Specialist', 'Radiologist', 'Pathologist',
    'Anesthesiologist', 'Emergency Medicine Physician', 'Geriatrician',
    'Plastic Surgeon', 'Vascular Surgeon', 'Thoracic Surgeon',
    'Endocrinologist', 'Nephrologist', 'Oncologist', 'Homeopath',
    'Ayurveda', 'Unani', 'Sexologist', 'Cosmetologist'
]

# Output configuration
OUTPUT_DIR = 'data'
CSV_FILENAME = 'doctors_data.csv'

# Scraping delays and limits
REQUEST_DELAY = 2
MAX_DOCTORS_PER_SPECIALITY = None  # Remove limit to capture all doctors
MAX_PAGES_PER_SPECIALITY = 50  # Limit pages to prevent infinite loops

# Browser configuration for Playwright
BROWSER_CONFIG = {
    'headless': True,
    'timeout': 30000,
    'viewport': {'width': 1920, 'height': 1080},
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}