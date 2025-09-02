"""
Bangalore Doctors Spider

This spider scrapes doctor information from Practo.com for all doctors in Bangalore.
It handles JavaScript-heavy content and pagination to collect comprehensive data.
"""

import scrapy
import json
import re
from urllib.parse import urljoin, quote_plus
from doctor_scraper.items import DoctorItem
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
try:
    from config import TARGET_CITY, SPECIALITIES, SCRAPING_CONFIG
except ImportError:
    # Fallback configuration
    TARGET_CITY = 'Bangalore'
    SPECIALITIES = ['General Physician', 'Cardiologist', 'Dermatologist']
    SCRAPING_CONFIG = {'delay_between_requests': 2, 'max_pages_per_speciality': 10}


class BangaloreDoctorsSpider(scrapy.Spider):
    name = "bangalore_doctors"
    allowed_domains = ["practo.com"]
    
    # Configuration
    target_city = TARGET_CITY
    specialities = SPECIALITIES
    max_pages = SCRAPING_CONFIG.get('max_pages_per_speciality', 50)
    
    custom_settings = {
        'DOWNLOAD_DELAY': SCRAPING_CONFIG.get('delay_between_requests', 2),
        'CONCURRENT_REQUESTS': SCRAPING_CONFIG.get('concurrent_requests', 2),
    }
    
    def start_requests(self):
        """Generate initial requests for all specialities in Bangalore"""
        
        for speciality in self.specialities:
            # Build the search URL for Practo
            # Format: https://www.practo.com/search/doctors?results_type=doctor&q=[{"word":"Cardiologist","autocompleted":true,"category":"subspeciality"}]&city=Bangalore
            search_query = json.dumps([{
                "word": speciality,
                "autocompleted": True,
                "category": "subspeciality"
            }])
            
            # URL encode the query
            encoded_query = quote_plus(search_query)
            url = f"https://www.practo.com/search/doctors?results_type=doctor&q={encoded_query}&city={self.target_city}"
            
            self.logger.info(f"Starting scrape for {speciality} in {self.target_city}")
            
            yield scrapy.Request(
                url=url,
                callback=self.parse_doctor_list,
                meta={
                    'speciality': speciality,
                    'page': 1,
                    'dont_cache': True,  # Don't cache search pages
                },
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
            )
    
    def parse_doctor_list(self, response):
        """Parse the doctors listing page and extract doctor profile URLs"""
        
        speciality = response.meta['speciality']
        page = response.meta['page']
        
        self.logger.info(f"Parsing {speciality} page {page}")
        
        # Extract doctor profile links
        # Look for doctor profile links in the listing
        doctor_links = response.css('a[href*="/doctor/"]::attr(href)').getall()
        
        if not doctor_links:
            # Try alternative selectors
            doctor_links = response.css('a[data-qa-id="doctor_name"]::attr(href)').getall()
        
        if not doctor_links:
            # Try more generic approach
            doctor_links = response.xpath('//a[contains(@href, "/doctor/")]/@href').getall()
        
        self.logger.info(f"Found {len(doctor_links)} doctor links on page {page} for {speciality}")
        
        # Process each doctor profile
        for link in doctor_links:
            if link:
                # Convert relative URLs to absolute
                doctor_url = urljoin(response.url, link)
                
                yield scrapy.Request(
                    url=doctor_url,
                    callback=self.parse_doctor_profile,
                    meta={
                        'speciality': speciality,
                        'doctor_url': doctor_url,
                    },
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    }
                )
        
        # Check for next page
        if len(doctor_links) > 0 and page < self.max_pages:
            # Look for next page link or pagination
            next_page_url = self.get_next_page_url(response, page)
            if next_page_url:
                yield scrapy.Request(
                    url=next_page_url,
                    callback=self.parse_doctor_list,
                    meta={
                        'speciality': speciality,
                        'page': page + 1,
                        'dont_cache': True,
                    },
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    }
                )
    
    def get_next_page_url(self, response, current_page):
        """Get the URL for the next page of results"""
        
        # Method 1: Look for pagination links
        next_links = response.css('a[aria-label="Next"]::attr(href)').getall()
        if next_links:
            return urljoin(response.url, next_links[0])
        
        # Method 2: Look for page numbers
        page_links = response.css('.pagination a::attr(href)').getall()
        for link in page_links:
            if f'page={current_page + 1}' in link:
                return urljoin(response.url, link)
        
        # Method 3: Construct next page URL manually
        if 'page=' in response.url:
            return re.sub(r'page=\d+', f'page={current_page + 1}', response.url)
        else:
            separator = '&' if '?' in response.url else '?'
            return f"{response.url}{separator}page={current_page + 1}"
        
        return None
    
    def parse_doctor_profile(self, response):
        """Parse individual doctor profile page"""
        
        speciality = response.meta['speciality']
        doctor_url = response.meta['doctor_url']
        
        item = DoctorItem()
        
        # Basic Information
        item['name'] = self.extract_text(response, [
            'h1.doctor-name::text',
            'h1[data-qa-id="doctor_name"]::text',
            '.doctor-profile h1::text',
            'h1::text'
        ])
        
        item['speciality'] = speciality
        
        item['qualifications'] = self.extract_text(response, [
            '.qualification-text::text',
            '.doctor-qualification::text',
            '[data-qa-id="doctor_qualification"]::text',
            '.qualification::text'
        ])
        
        item['experience_years'] = self.extract_text(response, [
            '.experience-text::text',
            '[data-qa-id="doctor_experience"]::text',
            '.experience::text'
        ])
        
        # Location Information
        item['clinic_name'] = self.extract_text(response, [
            '.clinic-name::text',
            '[data-qa-id="practice_name"]::text',
            '.practice-name::text'
        ])
        
        item['area'] = self.extract_text(response, [
            '.clinic-location::text',
            '.practice-location::text',
            '[data-qa-id="practice_locality"]::text'
        ])
        
        item['city'] = self.target_city
        
        item['full_address'] = self.extract_text(response, [
            '.full-address::text',
            '.practice-address::text',
            '[data-qa-id="practice_address"]::text'
        ])
        
        # Contact Information
        item['phone'] = self.extract_text(response, [
            '.phone-number::text',
            '[data-qa-id="practice_phone"]::text',
            '.contact-phone::text'
        ])
        
        # Rating & Reviews
        item['rating'] = self.extract_text(response, [
            '.rating-value::text',
            '[data-qa-id="doctor_score"]::text',
            '.doctor-rating::text'
        ])
        
        item['reviews_count'] = self.extract_text(response, [
            '.reviews-count::text',
            '[data-qa-id="doctor_reviews_count"]::text',
            '.review-count::text'
        ])
        
        item['patient_stories'] = self.extract_text(response, [
            '.patient-stories::text',
            '[data-qa-id="patient_stories"]::text'
        ])
        
        # Pricing
        item['consultation_fee'] = self.extract_text(response, [
            '.consultation-fee::text',
            '[data-qa-id="consultation_fee"]::text',
            '.fee-amount::text'
        ])
        
        # Availability
        item['available_today'] = self.extract_text(response, [
            '.available-today::text',
            '[data-qa-id="available_today"]::text'
        ])
        
        item['next_available_slot'] = self.extract_text(response, [
            '.next-slot::text',
            '[data-qa-id="next_available_slot"]::text'
        ])
        
        # Google Maps Link - This is crucial for the medical chatbot
        item['google_map_link'] = self.extract_google_maps_link(response)
        
        # Profile URL
        item['profile_url'] = doctor_url
        
        # Additional Information
        item['about'] = self.extract_text(response, [
            '.doctor-about::text',
            '[data-qa-id="doctor_about"]::text',
            '.about-text::text'
        ])
        
        item['services'] = self.extract_list_text(response, [
            '.services-list li::text',
            '.treatment-list li::text'
        ])
        
        item['awards'] = self.extract_list_text(response, [
            '.awards-list li::text',
            '.achievements li::text'
        ])
        
        # Validate that we got essential information
        if item.get('name') and item.get('speciality'):
            yield item
        else:
            self.logger.warning(f"Incomplete data for doctor at {doctor_url}")
    
    def extract_text(self, response, selectors):
        """Extract text using multiple selector fallbacks"""
        for selector in selectors:
            text = response.css(selector).get()
            if text:
                return text.strip()
        return ""
    
    def extract_list_text(self, response, selectors):
        """Extract list of text items using multiple selector fallbacks"""
        for selector in selectors:
            items = response.css(selector).getall()
            if items:
                return '; '.join([item.strip() for item in items if item.strip()])
        return ""
    
    def extract_google_maps_link(self, response):
        """Extract Google Maps link from the page"""
        
        # Method 1: Look for direct Google Maps links
        maps_links = response.css('a[href*="google.com/maps"]::attr(href)').getall()
        if maps_links:
            return maps_links[0]
        
        # Method 2: Look for map data attributes
        lat = response.css('[data-lat]::attr(data-lat)').get()
        lng = response.css('[data-lng]::attr(data-lng)').get()
        
        if lat and lng:
            return f"https://www.google.com/maps?q={lat},{lng}"
        
        # Method 3: Look for onclick map interactions
        onclick_links = response.css('[onclick*="map"]::attr(onclick)').getall()
        for onclick in onclick_links:
            if 'lat' in onclick and 'lng' in onclick:
                # Try to extract coordinates from onclick
                lat_match = re.search(r'lat["\']?\s*:\s*["\']?([-\d.]+)', onclick)
                lng_match = re.search(r'lng["\']?\s*:\s*["\']?([-\d.]+)', onclick)
                if lat_match and lng_match:
                    return f"https://www.google.com/maps?q={lat_match.group(1)},{lng_match.group(1)}"
        
        # Method 4: Look for address for manual geocoding later
        address = self.extract_text(response, [
            '.full-address::text',
            '.practice-address::text',
            '[data-qa-id="practice_address"]::text'
        ])
        
        if address:
            # Return a search URL for the address
            return f"https://www.google.com/maps/search/{quote_plus(address + ' ' + self.target_city)}"
        
        return ""
    
    def closed(self, reason):
        """Called when spider is closed"""
        self.logger.info(f"Spider closed: {reason}")
        
        # Log summary statistics
        stats = self.crawler.stats
        items_scraped = stats.get_value('item_scraped_count', 0)
        pages_crawled = stats.get_value('downloader/response_count', 0)
        
        self.logger.info(f"Scraping completed: {items_scraped} doctors found from {pages_crawled} pages")