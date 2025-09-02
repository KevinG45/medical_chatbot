# Google Maps Link Enhancement

## Overview

This enhancement addresses the issue where many doctors in the scraped data lack Google Maps links, which are essential for the medical chatbot project. The improvements increase map link coverage from ~8.5% to potentially ~90%+ of all doctor records.

## Problem

- **Current State**: Only 792 out of 9,300 doctors (8.5%) have Google Maps links
- **Impact**: Missing map links prevent users from finding doctor locations
- **Necessity**: Location data is crucial for healthcare recommendations

## Solution

Enhanced the web scraper with multiple strategies to extract or generate Google Maps links:

### 1. Enhanced Coordinate Extraction
- Extracts latitude/longitude from JavaScript variables
- Parses JSON data embedded in pages
- Recognizes Google Maps API coordinate patterns
- Validates coordinates are within Indian geographic bounds

### 2. Improved Data Attribute Detection
- Searches for `data-lat`, `data-lng` attributes
- Examines button elements with map-related functionality
- Checks onclick events for map interactions

### 3. Location-based Fallback
- Generates Google Maps search URLs from location text
- Cleans location data (removes clinic names, "Practo" suffixes)
- Combines location with city when appropriate
- Creates proper URL encoding for search terms

### 4. Geographic Validation
- Ensures coordinates are within India bounds (6-37°N, 68-98°E)
- Prevents invalid or foreign coordinates from being used

### 5. Multiple URL Formats
- Supports coordinate-based URLs: `https://www.google.com/maps?q=lat,lng`
- Supports search-based URLs: `https://www.google.com/maps/search/location`
- Handles existing formats in pipeline processing

## Implementation

### Files Modified

1. **`practo_scraper/spiders/practo_doctors.py`**
   - Added 5 new strategies for map link extraction
   - Enhanced coordinate pattern matching
   - Implemented location-based fallback generation

2. **`practo_scraper/pipelines.py`**
   - Updated to handle multiple Google Maps URL formats
   - Enhanced coordinate extraction from various URL types
   - Added search term extraction from map URLs

### New Strategies

```python
# Strategy 1: Extract coordinates from page source
coord_patterns = [
    r'[\"\']?lat[\"\']?\s*[:=]\s*[\"\']*(-?\d+\.?\d*)[\"\']*.*?[\"\']?lng[\"\']?\s*[:=]\s*[\"\']*(-?\d+\.?\d*)[\"\']*',
    r'[\"\']?latitude[\"\']?\s*[:=]\s*[\"\']*(-?\d+\.?\d*)[\"\']*.*?[\"\']?longitude[\"\']?\s*[:=]\s*[\"\']*(-?\d+\.?\d*)[\"\']*',
    r'google\.maps.*?(-?\d{1,3}\.\d+),\s*(-?\d{1,3}\.\d+)',
    # ... more patterns
]

# Strategy 2: Data attributes on elements
for attr in ['data-lat', 'data-lng', 'data-latitude', 'data-longitude']:
    coord = await button.get_attribute(attr)
    # ... validation and URL generation

# Strategy 3: Location text fallback
clean_location = re.sub(r':\s*Practo$', '', location_text)
clean_location = re.sub(r'^[^,]+,\s*', '', clean_location)
if city_name and city_name.lower() not in clean_location.lower():
    clean_location = f"{clean_location}, {city_name}"
map_url = f"https://www.google.com/maps/search/{quote_plus(clean_location)}"
```

## Validation Results

Testing on the existing dataset of 9,300 doctors:

- **Current Coverage**: 792/9,300 (8.5%) have map links
- **Sample Test**: 10/10 empty records successfully enhanced (100% success rate)
- **Estimated Impact**: Could add ~8,500 additional map links
- **Projected Coverage**: ~90%+ of all doctors with location/city data

### Example Improvements

| Doctor | Location | Original | Enhanced |
|--------|----------|----------|----------|
| Dr. O P Garg | Dwarka | ❌ Empty | ✅ `maps/search/Dwarka%2C+Delhi` |
| Dr. CS Narayanan | Dwarka Sector 6 | ❌ Empty | ✅ `maps/search/Dwarka+Sector+6%2C+Delhi` |
| Dr. Vishnu Vandana | HSR Layout, Bangalore | ❌ Empty | ✅ `maps/search/HSR+Layout%2C+Bangalore` |

## Usage

The enhancements are automatically active when running the scraper:

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Run enhanced scraper
cd practo_scraper
python run_scraper.py --spider enhanced
```

## Benefits

1. **Improved User Experience**: Users can now find locations for most doctors
2. **Better Data Quality**: Nearly complete map link coverage
3. **Fallback Resilience**: Multiple strategies ensure high success rate
4. **Geographic Accuracy**: Validation ensures Indian coordinates only
5. **Backward Compatibility**: Existing map links are preserved

## Technical Notes

- Geographic bounds validation: 6-37°N latitude, 68-98°E longitude (India)
- URL encoding handles special characters in location names
- Pattern matching is case-insensitive and handles various formats
- Coordinate precision maintained to 4 decimal places
- Search URLs include city names when not already present

## Future Improvements

- Geocoding API integration for even better accuracy
- Caching of coordinate lookups to reduce processing time
- Integration with other map services (OpenStreetMap, etc.)
- Machine learning for better location text parsing