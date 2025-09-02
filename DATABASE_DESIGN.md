# Medical Chatbot - Database Design & Implementation

## Database Choice: SQLite vs PostgreSQL

### Why SQLite (Current Implementation)

**Advantages:**
- ✅ **Zero Configuration**: No server setup required
- ✅ **Embedded**: Database file included with application  
- ✅ **Lightweight**: Perfect for prototyping and development
- ✅ **ACID Compliant**: Reliable transactions
- ✅ **Cross-platform**: Works on any OS
- ✅ **Built-in**: No external dependencies
- ✅ **Easy Backup**: Single file can be copied/moved
- ✅ **Perfect for 2000+ doctors**: Handles the scale efficiently

**Use Cases:**
- Development and testing
- Small to medium datasets (< 100K records)
- Single-user applications
- Embedded systems
- Proof of concept implementations

### When to Use PostgreSQL (Production Scale)

**Advantages:**
- ✅ **Concurrent Users**: Multiple simultaneous connections
- ✅ **Advanced Features**: JSON, GIS, full-text search
- ✅ **Scalability**: Handles millions of records
- ✅ **Performance**: Better for complex queries
- ✅ **Replication**: Master-slave configurations
- ✅ **Extensions**: PostGIS for geographic queries
- ✅ **ACID Compliance**: Enterprise-grade reliability

**Migration Path:**
```python
# PostgreSQL configuration (when needed)
DATABASE_CONFIG = {
    'type': 'postgresql',
    'host': 'localhost',
    'port': 5432,
    'database': 'medical_chatbot',
    'user': 'chatbot_user',
    'password': 'secure_password'
}
```

## Database Schema

### Doctors Table Structure

```sql
CREATE TABLE doctors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Basic Information
    name TEXT NOT NULL,
    speciality TEXT NOT NULL,
    qualifications TEXT,
    experience_years INTEGER,
    
    -- Location Information
    clinic_name TEXT,
    area TEXT,
    city TEXT,
    full_address TEXT,
    
    -- Contact Information
    phone TEXT,
    
    -- Rating & Reviews
    rating REAL,
    reviews_count INTEGER,
    patient_stories INTEGER,
    
    -- Pricing
    consultation_fee INTEGER,
    
    -- Availability
    available_today TEXT,
    next_available_slot TEXT,
    
    -- Links and References
    profile_url TEXT UNIQUE,        -- Prevents duplicates
    google_map_link TEXT,           -- Crucial for navigation
    
    -- Additional Information
    about TEXT,
    services TEXT,
    awards TEXT,
    
    -- Metadata
    scraped_at TEXT,
    source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes for Performance

```sql
-- Essential indexes for fast queries
CREATE INDEX idx_doctors_speciality ON doctors(speciality);
CREATE INDEX idx_doctors_area ON doctors(area);
CREATE INDEX idx_doctors_rating ON doctors(rating DESC);
CREATE INDEX idx_doctors_city_speciality ON doctors(city, speciality);
CREATE INDEX idx_doctors_consultation_fee ON doctors(consultation_fee);
```

## Data Pipeline Architecture

### 1. Data Collection (Scrapy + Playwright)
```
Practo.com → Spider → Raw HTML → Data Extraction → Items
```

### 2. Data Processing Pipeline
```
Raw Items → Validation → Cleaning → Database Storage → Export
```

### 3. Pipeline Components

#### ValidationPipeline
- Validates required fields (name, speciality, profile_url)
- Filters out invalid or incomplete records
- Ensures data quality before processing

#### CleaningPipeline  
- Normalizes text fields (removes extra whitespace)
- Extracts numeric values (ratings, fees, experience)
- Standardizes data formats
- Adds metadata (scraped_at, source)

#### DatabasePipeline
- Stores data in SQLite database
- Handles duplicate prevention (by profile_url)
- Creates database schema automatically
- Provides connection management

#### ExportPipeline
- Exports data to CSV and JSON formats
- Creates timestamped files
- Handles encoding properly (UTF-8)

## Google Maps Integration

### Map Link Extraction Strategy

1. **Direct Links**: Look for existing Google Maps URLs
2. **Coordinates**: Extract lat/lng from data attributes
3. **Address Search**: Generate Maps search URLs from addresses
4. **Fallback**: Manual geocoding for missing data

```python
def extract_google_maps_link(self, response):
    # Method 1: Direct Google Maps links
    maps_links = response.css('a[href*="google.com/maps"]::attr(href)').getall()
    if maps_links:
        return maps_links[0]
    
    # Method 2: Latitude/Longitude coordinates
    lat = response.css('[data-lat]::attr(data-lat)').get()
    lng = response.css('[data-lng]::attr(data-lng)').get()
    if lat and lng:
        return f"https://www.google.com/maps?q={lat},{lng}"
    
    # Method 3: Address-based search
    address = self.extract_address(response)
    if address:
        return f"https://www.google.com/maps/search/{quote_plus(address)}"
```

## Medical Chatbot Integration

### 1. Symptom to Speciality Mapping

```python
SYMPTOM_SPECIALITY_MAP = {
    'chest pain': ['Cardiologist', 'General Physician'],
    'skin problems': ['Dermatologist'],
    'headache': ['Neurologist', 'General Physician'],
    'joint pain': ['Orthopedist', 'Rheumatologist'],
    'stomach pain': ['Gastroenterologist', 'General Physician'],
    'breathing problems': ['Pulmonologist', 'Cardiologist'],
    'eye problems': ['Ophthalmologist'],
    'dental issues': ['Dentist'],
    'pregnancy': ['Gynecologist', 'Obstetrician'],
    'child health': ['Pediatrician'],
}
```

### 2. Location-Based Recommendations

```python
def find_nearby_doctors(user_location, speciality, radius_km=10):
    """Find doctors near user location"""
    query = """
        SELECT *, 
               (google_map_link IS NOT NULL) as has_maps
        FROM doctors 
        WHERE speciality = ? 
        AND area LIKE ?
        ORDER BY rating DESC, has_maps DESC
        LIMIT 5
    """
    return execute_query(query, [speciality, f"%{user_location}%"])
```

### 3. Chatbot Query Examples

```python
# Example 1: Symptom-based search
user_input = "I have chest pain"
specialities = symptom_to_speciality("chest pain")
doctors = find_doctors_by_speciality(specialities, user_location)

# Example 2: Location + speciality search  
user_input = "cardiologist in Koramangala"
doctors = find_doctors_by_area("Koramangala", "Cardiologist")

# Example 3: Rating-based filtering
doctors = find_top_rated_doctors(speciality="Dermatologist", min_rating=4.0)
```

## Performance Considerations

### Database Optimization
- **Indexing**: Critical fields indexed for fast lookups
- **Normalization**: Balanced approach (not over-normalized)
- **Data Types**: Appropriate types for each field
- **Constraints**: UNIQUE constraint on profile_url prevents duplicates

### Query Optimization
```sql
-- Fast speciality lookup
SELECT * FROM doctors 
WHERE speciality = 'Cardiologist' 
ORDER BY rating DESC 
LIMIT 10;

-- Location-based search with speciality
SELECT * FROM doctors 
WHERE city = 'Bangalore' 
AND speciality = 'Dermatologist'
AND area LIKE '%Indiranagar%'
ORDER BY rating DESC;

-- Available doctors with maps
SELECT * FROM doctors 
WHERE available_today = 'Yes'
AND google_map_link IS NOT NULL
AND google_map_link != ''
ORDER BY rating DESC;
```

## Scalability & Future Enhancements

### Immediate Scaling (SQLite)
- Current implementation handles 2000+ doctors efficiently
- Can scale to 50K+ records without issues
- Perfect for Bangalore-focused chatbot

### Future Scaling (PostgreSQL Migration)
```python
# Easy migration path using same pipeline code
DATABASE_CONFIG = {
    'type': 'postgresql',
    'connection_string': 'postgresql://user:pass@host:5432/db'
}
```

### Advanced Features
1. **Geographic Search**: PostGIS extension for radius-based queries
2. **Full-text Search**: Search in doctor descriptions and services
3. **Real-time Updates**: Periodic re-scraping and data updates
4. **API Integration**: REST API for chatbot integration
5. **Caching**: Redis for frequently accessed data

## Data Quality Metrics

### Current Implementation Tracking
- **Completeness**: % of records with all fields populated
- **Accuracy**: Validation of phone numbers, ratings, fees
- **Freshness**: Timestamp tracking for data recency
- **Uniqueness**: Duplicate prevention by profile URL

### Quality Monitoring
```python
def generate_quality_report():
    return {
        'total_doctors': count_total_doctors(),
        'with_google_maps': count_doctors_with_maps(),
        'with_phone': count_doctors_with_phone(),
        'with_rating': count_doctors_with_rating(),
        'avg_rating': calculate_average_rating(),
        'data_freshness': calculate_data_age()
    }
```

## Security & Privacy

### Data Protection
- **Personal Data**: Publicly available information only
- **Contact Info**: Only business phone numbers
- **Privacy**: No patient data or personal medical information
- **Compliance**: Follows web scraping best practices

### Rate Limiting
- Respectful scraping with delays between requests
- User-agent identification
- Retry logic with exponential backoff
- Server load monitoring

This database design provides a solid foundation for the medical chatbot while being easily scalable and maintainable.