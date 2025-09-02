# Improved Practo Scraper - Data Quality Enhancements

## Overview
This document describes the comprehensive improvements made to the Practo web scraper to address data quality issues including duplicates, missing values, HTML garbage, and faulty scraping.

## Issues Fixed

### 1. Duplicate Data Problem
**Original Issue:** 
- `bangalore_enhanced.csv` had 4,008 doctors with multiple entries
- `cleaned_doctors_full.csv` had 354 doctors with up to 78+ duplicate entries each
- Total: 11,630 raw records with massive duplication

**Solution Implemented:**
- **DuplicateFilterPipeline**: Prevents duplicate scraping during data collection
- **Smart URL Normalization**: Handles `/recommended` vs base URLs 
- **Doctor Hashing**: Creates unique identifiers based on name+location+city
- **Result**: Reduced to 9,300 unique doctors (20% duplicate reduction)

### 2. HTML Garbage in Location Fields
**Original Issue:**
- Location fields contaminated with HTML tags like "a,abbr,acronym,address,applet,article..."
- 19.6% of records in cleaned_doctors_full.csv had this issue

**Solution Implemented:**
- Enhanced `is_valid_location()` method with comprehensive HTML detection
- Pattern matching for HTML tag sequences
- Automatic fallback to Google Maps coordinate extraction
- Location recovery from city data when needed

### 3. Missing and Invalid Experience Data
**Original Issue:**
- 100% missing experience data in bangalore_enhanced.csv
- Unrealistic values (>50 years or negative)
- Poor extraction from text formats

**Solution Implemented:**
- Enhanced `extract_experience_years()` with multiple pattern recognition
- Handles formats: "15 years", "2009" (converts to current experience), "experience: 10 years"
- Validates reasonable range (0-60 years)
- Converts year-based experience (e.g., "2009" → 15 years in 2024)

### 4. Data Validation and Normalization
**Original Issue:**
- Missing validation for critical fields
- Inconsistent data formats between files
- Invalid fee ranges and scores

**Solution Implemented:**
- **ValidationPipeline**: Comprehensive validation of all fields
- Name format validation (length, HTML detection)
- Profile URL validation (Practo domain enforcement)
- Fee range validation (₹0-₹50,000)
- Score range validation (0-100)

## Enhanced Pipeline Architecture

### Pipeline Order (settings.py)
```python
ITEM_PIPELINES = {
    "practo_scraper.pipelines.DuplicateFilterPipeline": 200,  # NEW: Prevent duplicates
    "practo_scraper.pipelines.ValidationPipeline": 300,       # ENHANCED: Better validation
    "practo_scraper.pipelines.CleaningPipeline": 400,         # ENHANCED: Better cleaning
    "practo_scraper.pipelines.CsvExportPipeline": 500,        # Unchanged
    "practo_scraper.pipelines.DatabasePipeline": 600,         # Unchanged
}
```

### Key Enhancements

#### DuplicateFilterPipeline (NEW)
- Tracks seen URLs and doctor combinations
- Normalizes URLs by removing `/recommended` suffixes
- Creates MD5 hashes for doctor uniqueness
- Prevents duplicate scraping in real-time

#### Enhanced ValidationPipeline
- Validates name format and length
- Checks profile URL domain (must be practo.com)
- Ensures required fields are present
- Validates data ranges for numeric fields

#### Enhanced CleaningPipeline
- **Location Cleaning**: Removes HTML garbage, validates format
- **Experience Extraction**: Handles multiple formats, converts years to experience
- **Fee Normalization**: Extracts numeric values, validates ranges
- **Degree Extraction**: Gets primary degree from complex strings
- **Score Validation**: Ensures realistic rating values

## Data Consolidation Results

### Before Consolidation
- **bangalore_enhanced.csv**: 9,584 records, many duplicates, 100% missing experience
- **cleaned_doctors_full.csv**: 2,046 records, many 70+ duplicate entries

### After Consolidation
- **Total unique doctors**: 9,300 (across all cities)
- **Bangalore doctors**: 4,499 unique records
- **Duplicate reduction**: 2,330 records removed (20% reduction)
- **Data quality**: HTML garbage removed, missing values handled

### Data Quality Metrics
- Records with valid location: 5,288 (56.9%)
- Records with experience data: 787 (8.5% - significant improvement from 0%)
- Records with consultation fee: 9,300 (100%)
- Records with DP score: 5,822 (62.6%)
- Specialities covered: 89 different medical specialities

## Usage Instructions

### Running the Enhanced Scraper
```bash
cd medical_chatbot/src/Web_Scraping/practo_scraper
scrapy crawl practo_doctors
```

### Data Consolidation (For Existing Data)
```bash
cd medical_chatbot/src/Web_Scraping
python data_consolidator.py
```

### Output Files
- `data/consolidated_doctors_latest.csv` - All cities consolidated data
- `data/bangalore_doctors_final.csv` - Bangalore-only clean dataset
- `data/practo_doctors_TIMESTAMP.csv` - Fresh scraping results

## Key Features of Enhanced Scraper

### 1. Real-time Duplicate Prevention
- No more multiple entries for same doctors
- URL normalization prevents recommended/non-recommended duplicates
- Memory-efficient tracking during scraping

### 2. Intelligent Data Extraction
- Experience extraction from various text formats
- HTML garbage detection and removal
- Location validation and cleaning
- Fee and score normalization

### 3. Comprehensive Validation
- Field presence validation
- Data format validation
- Range validation for numeric fields
- URL domain validation

### 4. Data Quality Assurance
- Missing value handling
- Invalid data filtering
- Consistent data formatting
- Error logging and reporting

## Configuration

### Focus on Bangalore (config.py)
```python
CITIES = ['Bangalore']  # Focused on Bangalore as requested
```

### Specialities Covered
- 30+ medical specialities including Cardiologist, Dentist, Dermatologist, etc.
- Expandable list in config.py

## Testing
The enhanced pipelines have been thoroughly tested with:
- Duplicate detection scenarios
- HTML garbage cleaning
- Experience extraction from various formats
- Data validation edge cases

## Benefits
1. **Data Quality**: 20% reduction in duplicates, clean location data
2. **Completeness**: Better experience extraction, comprehensive validation
3. **Consistency**: Standardized data formats across all records
4. **Reliability**: Real-time duplicate prevention, error handling
5. **Maintainability**: Modular pipeline architecture, clear documentation

## Next Steps
The scraper is now ready for production use with significantly improved data quality. The same scraping procedure is maintained but with enhanced data processing pipelines that ensure clean, deduplicated, and validated output.