import scrapy
import re
import json
from urllib.parse import urlencode, urlparse, parse_qs
from practo_scraper.items import DoctorItem
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
try:
    from config import SPECIALITIES
except ImportError:
    # Fallback if config import fails
    SPECIALITIES = [
        'Cardiologist', 'Chiropractor', 'Dentist', 'Dermatologist', 
        'Dietitian/Nutritionist', 'Gastroenterologist', 'bariatric surgeon', 
        'Gynecologist', 'Infertility Specialist', 'Neurologist', 'Neurosurgeon', 
        'Ophthalmologist', 'Orthopedist', 'Pediatrician', 'Physiotherapist', 
        'Psychiatrist', 'Pulmonologist', 'Rheumatologist', 'Urologist'
    ]


class PractoDoctorsSimpleSpider(scrapy.Spider):
    name = "practo_doctors_simple"
    allowed_domains = ["practo.com"]
    
    # Focus on Bangalore as requested
    city = "Bangalore"
    specialities = SPECIALITIES  # Use all specialities instead of limiting to 5
    
    # Add counters for tracking
    total_doctors_found = 0
    total_specialities_processed = 0
    
    custom_settings = {
        'CONCURRENT_REQUESTS': 2,
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
    }
    
    def start_requests(self):
        """Generate initial requests for Bangalore specialities"""
        
        for speciality in self.specialities:
            # Use a simpler URL format that works with regular HTTP
            url = f"https://www.practo.com/{self.city}/doctors/{speciality.lower().replace(' ', '-').replace('/', '-')}"
            
            # Alternative URL format 
            alt_url = f"https://www.practo.com/bangalore/{speciality.lower().replace(' ', '-').replace('/', '-')}"
            
            # Try both URL formats to maximize coverage
            for search_url in [url, alt_url]:
                yield scrapy.Request(
                    url=search_url,
                    meta={
                        "city": self.city,
                        "speciality": speciality,
                    },
                    callback=self.parse_doctors_listing,
                    errback=self.handle_error,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'gzip, deflate',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                    }
                )
    
    def parse_doctors_listing(self, response):
        """Parse the doctors listing page and extract doctor profile URLs"""
        
        city = response.meta['city']
        speciality = response.meta['speciality']
        page_number = response.meta.get('page_number', 1)
        
        self.logger.info(f"Parsing {speciality} doctors in {city} from {response.url} (page {page_number})")
        
        # Try multiple selectors for doctor profiles
        doctor_selectors = [
            'div.listing-card a[href*="/doctor/"]',  # Standard listing card
            'a[href*="/dr-"]',  # Alternative doctor URL format
            'a[href*="/doctor-"]',  # Another doctor URL format
            '.doc-card a',  # Doctor card link
            '.doctor-profile-link',  # Direct class
            '.listing-item a[href*="/doctor/"]',  # Listing item format
            '[data-doctor-id] a',  # Data attribute approach
        ]
        
        doctor_links = []
        for selector in doctor_selectors:
            links = response.css(selector + '::attr(href)').getall()
            if links:
                doctor_links.extend(links)
                self.logger.info(f"Found {len(links)} doctor links using selector: {selector}")
                break
        
        # Remove duplicates
        doctor_links = list(set(doctor_links))
        
        self.logger.info(f"Found {len(doctor_links)} unique doctors for {speciality} in {city} (page {page_number})")
        self.total_doctors_found += len(doctor_links)
        
        # If no doctors found, try to extract from JavaScript or JSON data
        if not doctor_links:
            # Try to find JSON data in script tags
            scripts = response.css('script:contains("doctor")').getall()
            for script in scripts:
                if 'doctor' in script.lower() and ('url' in script.lower() or 'href' in script.lower()):
                    # Extract URLs from script content
                    urls = re.findall(r'/doctor/[^"\'>\s]+', script)
                    if urls:
                        doctor_links.extend(urls)
                        self.logger.info(f"Found {len(urls)} doctor URLs in JavaScript")
                        break
        
        # Process doctor links
        for href in doctor_links:  # Process all doctors found (removed artificial limit)
            if href:
                profile_url = response.urljoin(href)
                
                yield scrapy.Request(
                    url=profile_url,
                    meta={
                        "city": city,
                        "speciality": speciality,
                    },
                    callback=self.parse_doctor_profile,
                    errback=self.handle_error,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    }
                )
        
        # Try to find pagination or "load more" functionality
        page_number = response.meta.get('page_number', 1)
        max_pages = 20  # Limit to prevent infinite loops
        
        if page_number < max_pages:
            next_page_selectors = [
                'a.next-page',
                'a[aria-label="Next"]',
                'button[data-qa-id="load_more_doctors"]',
                '.pagination .next a',
                'a:contains("Next")',
                '.load-more-btn',
                f'a[href*="page={page_number + 1}"]',  # Direct page number link
            ]
            
            next_page_found = False
            for selector in next_page_selectors:
                next_page = response.css(selector + '::attr(href)').get()
                if next_page:
                    self.logger.info(f"Found next page for {speciality} in {city}: page {page_number + 1}")
                    yield scrapy.Request(
                        url=response.urljoin(next_page),
                        meta={
                            "city": city,
                            "speciality": speciality,
                            "page_number": page_number + 1,
                        },
                        callback=self.parse_doctors_listing,
                        headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        }
                    )
                    next_page_found = True
                    break
            
            # If no explicit next page found, try constructing page URLs
            if not next_page_found and page_number == 1:
                # Try common pagination patterns
                base_url = response.url.split('?')[0]
                next_page_url = f"{base_url}?page={page_number + 1}"
                
                yield scrapy.Request(
                    url=next_page_url,
                    meta={
                        "city": city,
                        "speciality": speciality,
                        "page_number": page_number + 1,
                    },
                    callback=self.parse_doctors_listing,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    },
                    dont_filter=True  # Allow duplicate requests for pagination
                )
    
    def parse_doctor_profile(self, response):
        """Parse individual doctor profile page"""
        
        city = response.meta['city']
        speciality = response.meta['speciality']
        
        self.logger.info(f"Parsing doctor profile: {response.url}")
        
        item = DoctorItem()
        
        # Basic information
        item['city'] = city
        item['speciality'] = speciality
        item['profile_url'] = response.url
        
        # Name - try multiple selectors
        name_selectors = [
            'h1.c-profile__title::text',
            'h1[data-qa-id="doctor_name"]::text', 
            '.doctor-name::text',
            '.profile-title h1::text',
            'h1::text',
            '.doc-name::text',
        ]
        
        name = None
        for selector in name_selectors:
            name = response.css(selector).get()
            if name:
                name = name.strip()
                break
        
        if not name:
            # Try extracting from title tag
            title = response.css('title::text').get()
            if title and 'Dr.' in title:
                name = title.split('|')[0].strip()
        
        item['name'] = name or ""
        
        # Degree/qualification
        degree_selectors = [
            'p.c-profile__details::text',
            '.doctor-degree::text',
            '.qualification::text',
            '.doc-qualification::text',
            '[data-qa-id="doctor_qualification"]::text',
        ]
        
        degree = None
        for selector in degree_selectors:
            degree = response.css(selector).get()
            if degree:
                degree = degree.strip()
                break
        
        item['degree'] = degree or ""
        
        # Experience
        experience_text = ""
        # Look for text containing "years" or "experience"
        all_text = response.css('*::text').getall()
        for text in all_text:
            if text and ('year' in text.lower() and any(char.isdigit() for char in text)):
                experience_text = text.strip()
                break
        
        item['year_of_experience'] = experience_text
        
        # Location
        location_selectors = [
            'h4.c-profile--clinic__location::text',
            '.clinic-location::text',
            '.doctor-location::text',
            '.practice-location::text',
            '[data-qa-id="clinic_location"]::text',
        ]
        
        location = None
        for selector in location_selectors:
            location = response.css(selector).get()
            if location:
                location = location.strip()
                break
        
        # If no specific location found, try to extract from address-like text
        if not location:
            for text in all_text:
                if text and (any(word in text.lower() for word in ['road', 'street', 'bangalore', 'bengaluru', 'area', 'nagar'])):
                    location = text.strip()[:100]  # Limit length
                    break
        
        item['location'] = location or ""
        
        # DP Score (rating)
        rating_selectors = [
            'span.u-green-text.u-bold.u-large-font::text',
            '.rating-score::text',
            '.doctor-rating::text',
            '[data-qa-id="doctor_rating"]::text',
            '.star-rating::text',
        ]
        
        rating = None
        for selector in rating_selectors:
            rating = response.css(selector).get()
            if rating:
                rating = rating.strip()
                break
        
        item['dp_score'] = rating or ""
        
        # Number of votes/reviews
        votes_text = ""
        for text in all_text:
            if text and ('votes' in text.lower() or 'reviews' in text.lower()) and any(char.isdigit() for char in text):
                votes_text = text.strip()
                break
        
        item['npv'] = votes_text
        
        # Consultation fee
        fee_selectors = [
            'span.u-strike::text',
            '.consultation-fee::text',
            '.doctor-fee::text',
            '.fee-amount::text',
            '[data-qa-id="consultation_fee"]::text',
        ]
        
        fee = None
        for selector in fee_selectors:
            fee = response.css(selector).get()
            if fee:
                fee = fee.strip()
                break
        
        # If no specific fee found, look for currency symbols
        if not fee:
            for text in all_text:
                if text and ('₹' in text or 'Rs' in text.upper()) and any(char.isdigit() for char in text):
                    fee = text.strip()
                    break
        
        item['consultation_fee'] = fee or ""
        
        # Google Map link - multiple approaches
        google_map_link = ""
        
        # 1. Look for iframe with Google Maps
        map_iframe = response.css('iframe[src*="google.com/maps"]::attr(src)').get()
        if map_iframe:
            google_map_link = map_iframe
        
        # 2. Look for direct links to Google Maps
        if not google_map_link:
            map_link = response.css('a[href*="google.com/maps"]::attr(href)').get()
            if map_link:
                google_map_link = map_link
        
        # 3. Look for map data in JavaScript
        if not google_map_link:
            scripts = response.css('script::text').getall()
            for script in scripts:
                # Look for coordinates in JavaScript
                lat_match = re.search(r'lat["\']?\s*[:=]\s*["\']*([0-9.-]+)', script)
                lng_match = re.search(r'lng["\']?\s*[:=]\s*["\']*([0-9.-]+)', script)
                
                if lat_match and lng_match:
                    lat = lat_match.group(1)
                    lng = lng_match.group(1)
                    google_map_link = f"https://www.google.com/maps?q={lat},{lng}"
                    break
                
                # Look for Google Maps URLs in script
                map_url_match = re.search(r'(https://[^"\']*google\.com/maps[^"\']*)', script)
                if map_url_match:
                    google_map_link = map_url_match.group(1)
                    break
        
        # 4. Create a search-based Google Maps link if we have location
        if not google_map_link and (item['location'] or item['name']):
            search_query = f"{item['name']} {item['location']} {city}".strip()
            if search_query:
                google_map_link = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
        
        item['google_map_link'] = google_map_link
        
        # Only yield if we have essential data
        if item.get('name') and (item.get('consultation_fee') or item.get('location')):
            yield item
            self.logger.info(f"Successfully extracted: {item['name']}")
        else:
            self.logger.warning(f"Skipping incomplete profile: {response.url}")
    
    def handle_error(self, failure):
        """Handle request errors"""
        self.logger.error(f"Request failed: {failure.request.url} - {failure.value}")
        
    def closed(self, reason):
        """Called when spider is closed"""
        self.logger.info(f"Spider closed: {reason}")
        self.logger.info(f"Total doctors found across all specialities: {self.total_doctors_found}")
        self.logger.info(f"Total specialities processed: {self.total_specialities_processed}")