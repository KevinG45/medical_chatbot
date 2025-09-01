import scrapy
from scrapy_playwright.page import PageMethod
from urllib.parse import urlencode
import time
import re
from practo_scraper.items import DoctorItem
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
try:
    from config import CITIES, SPECIALITIES
except ImportError:
    # Fallback if config import fails
    CITIES = ['Bangalore', 'Delhi', 'Mumbai']
    SPECIALITIES = [
        'Cardiologist', 'Chiropractor', 'Dentist', 'Dermatologist', 
        'Dietitian/Nutritionist', 'Gastroenterologist', 'bariatric surgeon', 
        'Gynecologist', 'Infertility Specialist', 'Neurologist', 'Neurosurgeon', 
        'Ophthalmologist', 'Orthopedist', 'Pediatrician', 'Physiotherapist', 
        'Psychiatrist', 'Pulmonologist', 'Rheumatologist', 'Urologist'
    ]


class PractoDoctorsSpider(scrapy.Spider):
    name = "practo_doctors"
    allowed_domains = ["practo.com"]
    
    # Configuration
    cities = CITIES
    specialities = SPECIALITIES
    
    def start_requests(self):
        """Generate initial requests for all city-speciality combinations"""
        
        for city in self.cities:
            for speciality in self.specialities:
                # Build the search URL for Practo
                search_query = f'[{{"word":"{speciality}","autocompleted":true,"category":"subspeciality"}}]'
                url = f"https://www.practo.com/search/doctors?results_type=doctor&q={search_query}&city={city}"
                
                yield scrapy.Request(
                    url=url,
                    meta={
                        "playwright": True,
                        "playwright_include_page": True,
                        "playwright_page_methods": [
                            PageMethod("wait_for_selector", "div.u-border-general--bottom", timeout=10000),
                            PageMethod("evaluate", "window.scrollTo(0, document.body.scrollHeight)"),
                            PageMethod("wait_for_timeout", 2000),
                        ],
                        "city": city,
                        "speciality": speciality,
                    },
                    callback=self.parse_doctors_listing,
                    errback=self.handle_error,
                )
    
    async def parse_doctors_listing(self, response):
        """Parse the doctors listing page and extract doctor profile URLs"""
        
        city = response.meta['city']
        speciality = response.meta['speciality']
        
        page = response.meta["playwright_page"]
        
        try:
            # Scroll to load all doctors
            await self.scroll_to_load_all(page)
            
            # Extract doctor profile links
            doctor_links = await page.query_selector_all('div.u-border-general--bottom a[href*="/doctor/"]')
            
            self.logger.info(f"Found {len(doctor_links)} doctors for {speciality} in {city}")
            
            for link in doctor_links:
                href = await link.get_attribute('href')
                if href:
                    profile_url = response.urljoin(href)
                    
                    yield scrapy.Request(
                        url=profile_url,
                        meta={
                            "playwright": True,
                            "playwright_include_page": True,
                            "playwright_page_methods": [
                                PageMethod("wait_for_selector", "h1.c-profile__title", timeout=10000),
                            ],
                            "city": city,
                            "speciality": speciality,
                        },
                        callback=self.parse_doctor_profile,
                        errback=self.handle_error,
                    )
                    
        except Exception as e:
            self.logger.error(f"Error parsing doctors listing for {speciality} in {city}: {str(e)}")
        
        finally:
            await page.close()
    
    async def scroll_to_load_all(self, page):
        """Scroll to load all doctors on the page with enhanced loading"""
        try:
            scroll_attempts = 0
            max_scroll_attempts = 20  # Increase max attempts
            consecutive_same_height = 0
            
            previous_height = await page.evaluate("document.body.scrollHeight")
            
            while scroll_attempts < max_scroll_attempts:
                # Scroll to bottom
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(3000)  # Increased wait time
                
                # Try clicking "Load More" button if it exists
                try:
                    load_more_button = await page.query_selector('button[data-qa-id="load_more_doctors"], .load-more-button, .load-more')
                    if load_more_button:
                        await load_more_button.click()
                        await page.wait_for_timeout(2000)
                        self.logger.info("Clicked 'Load More' button")
                except Exception:
                    pass  # Button might not exist or be clickable
                
                # Get new height
                new_height = await page.evaluate("document.body.scrollHeight")
                
                # Check if height changed
                if new_height == previous_height:
                    consecutive_same_height += 1
                    if consecutive_same_height >= 3:  # Stop after 3 consecutive same heights
                        break
                else:
                    consecutive_same_height = 0
                    
                previous_height = new_height
                scroll_attempts += 1
                
                self.logger.debug(f"Scroll attempt {scroll_attempts}, height: {new_height}")
                
        except Exception as e:
            self.logger.warning(f"Error during scrolling: {str(e)}")
    
    async def parse_doctor_profile(self, response):
        """Parse individual doctor profile page"""
        
        city = response.meta['city']
        speciality = response.meta['speciality']
        page = response.meta["playwright_page"]
        
        try:
            item = DoctorItem()
            
            # Extract doctor information
            item['city'] = city
            item['speciality'] = speciality
            item['profile_url'] = response.url
            
            # Name - try multiple selectors
            name_selectors = [
                'h1.c-profile__title',  # Original selector
                'h1[class*="title"]',  # Any h1 with title in class
                '.doctor-name',  # Direct naming
                '.profile-name',  # Profile name
                'h1[class*="name"]',  # H1 with name in class
                '.physician-name',  # Physician name
                'h2[class*="title"]',  # H2 with title
                '.doc-name',  # Doc name
            ]
            
            for selector in name_selectors:
                try:
                    name_element = await page.query_selector(selector)
                    if name_element:
                        item['name'] = await name_element.inner_text()
                        break
                except Exception:
                    continue
            
            # Degree - try multiple selectors
            degree_selectors = [
                'p.c-profile__details',  # Original selector
                '.doctor-degree',  # Direct naming
                '.profile-degree',  # Profile degree
                'p[class*="degree"]',  # Paragraph with degree
                '.qualification',  # Qualification
                '.doctor-qualification',  # Doctor qualification
                'span[class*="degree"]',  # Span with degree
                '.credentials',  # Credentials
                '.education',  # Education
            ]
            
            for selector in degree_selectors:
                try:
                    degree_element = await page.query_selector(selector)
                    if degree_element:
                        item['degree'] = await degree_element.inner_text()
                        break
                except Exception:
                    continue
            
            # Years of experience - try multiple selectors
            experience_text = None
            experience_selectors = [
                'div.c-profile__details h2',  # Original selector
                '.c-profile__details .years',  # Alternative 1
                '*[class*="experience"]',  # Any element with experience in class
                '*[class*="years"]',  # Any element with years in class
                'span:contains("years")',  # Text-based search
                'div:contains("Experience")',  # Text-based search
                '.profile-details .experience',  # Common pattern
                '.doctor-experience',  # Direct naming
                'h2:contains("years")',  # Header with years
                'div[data-qa*="experience"]',  # Data attribute
                '.experience-text',  # Experience text
                '.years-experience',  # Years experience
                '.work-experience',  # Work experience
                'span[class*="year"]',  # Span with year in class
                'div[class*="experience"]',  # Div with experience in class
                '.profile-experience',  # Profile experience
                '.doctor-years',  # Doctor years
                'p:contains("years of experience")',  # Paragraph with full text
                'span:contains("experience")',  # Span with experience
                '.experience-value',  # Experience value
            ]
            
            def is_valid_experience_text(text):
                """Check if text represents years of experience rather than graduation year"""
                if not text:
                    return False
                
                import re
                # Look for patterns like "5 years", "10+ years", "15 years of experience"
                experience_patterns = [
                    r'(\d{1,2})\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)',
                    r'(\d{1,2})\+?\s*(?:years?|yrs?)',
                    r'experience:?\s*(\d{1,2})\+?\s*(?:years?|yrs?)',
                ]
                
                for pattern in experience_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        years = int(match.group(1))
                        # Validate reasonable experience range (1-50 years)
                        if 1 <= years <= 50:
                            return True
                
                # Avoid graduation years (1990-2030)
                graduation_patterns = [
                    r'(?:graduated|degree|mbbs|md|bds|phd)\s*(?:in)?\s*(19\d{2}|20[0-3]\d)',
                    r'(19\d{2}|20[0-3]\d)\s*(?:graduate|degree)',
                    r'^(19\d{2}|20[0-3]\d)$',  # Just a year that looks like graduation year
                ]
                
                for pattern in graduation_patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        return False
                
                return False
            
            for selector in experience_selectors:
                try:
                    if 'contains' in selector:
                        # For text-based selectors, use different approach
                        elements = await page.query_selector_all('*')
                        for elem in elements:
                            text = await elem.inner_text() if elem else ""
                            if text and ("years" in text.lower() or "experience" in text.lower()):
                                if is_valid_experience_text(text):
                                    experience_text = text
                                    break
                        if experience_text:
                            break
                    else:
                        elements = await page.query_selector_all(selector)
                        if elements:
                            for elem in elements:
                                text = await elem.inner_text() if elem else ""
                                if text and ("years" in text.lower() or "experience" in text.lower()):
                                    if is_valid_experience_text(text):
                                        experience_text = text
                                        break
                            if experience_text:
                                break
                except Exception:
                    continue
            
            item['year_of_experience'] = experience_text or ""
            
            # Location - try multiple selectors with validation
            location_text = None
            location_selectors = [
                'h4.c-profile--clinic__location',  # Original selector
                '.c-profile--clinic__location',  # Without h4
                '.clinic-location',  # Common pattern
                '.doctor-location',  # Direct naming
                '.profile-location',  # Profile pattern
                'div[data-qa*="location"]',  # Data attribute
                '.practice-location',  # Practice pattern
                '.hospital-address',  # Hospital pattern
                '.address-text',  # Address text
                '.clinic-address',  # Clinic address
                'span[class*="location"]:not([class*="html"])',  # Specific location spans, excluding HTML elements
                'div[class*="address"]:not([class*="html"])',  # Specific address divs, excluding HTML elements
                '.address-line',  # Address line
                '.clinic-info .address',  # Clinic info address
                '.practice-address',  # Practice address
                '.location-text',  # Location text
                'p[class*="address"]',  # Paragraph with address
                'span[class*="address"]',  # Span with address
                '.area-name',  # Area name
                '.locality',  # Locality
                '.address-details',  # Address details
            ]
            
            def is_valid_location(text):
                """Check if extracted text is a valid location and not HTML garbage"""
                if not text or not text.strip():
                    return False
                
                text = text.strip()
                
                # Check for HTML tag patterns (common garbage)
                html_patterns = [
                    r'^a,abbr,acronym,address,applet,article',  # Common garbage pattern
                    r'[a-z]+,[a-z]+,[a-z]+,[a-z]+',  # Multiple comma-separated lowercase words
                    r'^(a|abbr|acronym|address|applet|article|aside|audio|b|big|blockquote)$',  # Single HTML tags
                ]
                
                for pattern in html_patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        return False
                
                # Check if it's suspiciously long (garbage data tends to be very long)
                if len(text) > 200:
                    return False
                    
                # Check if it contains too many commas (likely tag list)
                if text.count(',') > 5:
                    return False
                
                # Check if it looks like HTML tags
                if '<' in text or '>' in text:
                    return False
                
                return True
            
            for selector in location_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        text = await element.inner_text()
                        if is_valid_location(text):
                            location_text = text.strip()
                            self.logger.debug(f"Found valid location with selector '{selector}': {location_text}")
                            break
                        else:
                            self.logger.debug(f"Invalid location found with selector '{selector}': {text}")
                except Exception as e:
                    self.logger.debug(f"Error with location selector '{selector}': {e}")
                    continue
            
            item['location'] = location_text or ""
            
            # DP Score (rating)
            score_element = await page.query_selector('span.u-green-text.u-bold.u-large-font')
            if score_element:
                item['dp_score'] = await score_element.inner_text()
            
            # Google Map link - try multiple approaches
            google_map_link = None
            map_selectors = [
                'iframe[src*="google.com/maps"]',  # iFrame with Google Maps
                'iframe[src*="maps.google"]',  # Alternative Google Maps iframe
                'a[href*="google.com/maps"]',  # Direct link to Google Maps
                'a[href*="maps.google"]',  # Alternative Google Maps link
                '*[data-src*="google.com/maps"]',  # Data-src attribute
                '*[data-href*="google.com/maps"]',  # Data-href attribute
                '.map-container iframe',  # Map container with iframe
                '.google-map',  # Direct class naming
                '*[class*="map"]',  # Any element with map in class
                'div[id*="map"]'  # Any div with map in ID
            ]
            
            for selector in map_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        # Try different attributes
                        for attr in ['src', 'href', 'data-src', 'data-href']:
                            link = await element.get_attribute(attr)
                            if link and ('google.com/maps' in link or 'maps.google' in link):
                                google_map_link = link
                                break
                        if google_map_link:
                            break
                except Exception:
                    continue
            
            # If no direct map link found, try to find any element that might contain location data
            if not google_map_link:
                try:
                    # Look for elements that might have onclick events or data attributes with coordinates
                    map_elements = await page.query_selector_all('*[onclick*="map"], *[data-lat], *[data-lng], *[data-coordinates]')
                    for elem in map_elements:
                        onclick = await elem.get_attribute('onclick') or ""
                        data_lat = await elem.get_attribute('data-lat') or ""
                        data_lng = await elem.get_attribute('data-lng') or ""
                        
                        if onclick and ('map' in onclick.lower() or 'google' in onclick.lower()):
                            google_map_link = f"Found map interaction: {onclick[:100]}"
                            break
                        elif data_lat and data_lng:
                            google_map_link = f"https://www.google.com/maps?q={data_lat},{data_lng}"
                            break
                except Exception:
                    pass
            
            item['google_map_link'] = google_map_link or ""
            
            # Number of patient votes - try multiple selectors
            votes_text = None
            votes_selectors = [
                'span.u-smallest-font.u-grey_3-text',  # Original selector
                '*[class*="votes"]',  # Any element with votes in class
                '*[class*="reviews"]',  # Any element with reviews in class
                '*[class*="rating"]',  # Any element with rating in class
                '.vote-count',  # Common pattern
                '.review-count',  # Review pattern
                '.patient-votes',  # Direct naming
                'span[data-qa*="votes"]',  # Data attribute
                '*:contains("votes")',  # Text-based search
                '*:contains("reviews")',  # Text-based search
                '.total-reviews',  # Total reviews pattern
                '.feedback-count'  # Feedback pattern
            ]
            
            for selector in votes_selectors:
                try:
                    if 'contains' in selector:
                        # For text-based selectors, search through elements
                        elements = await page.query_selector_all('span, div, p')
                        for elem in elements:
                            text = await elem.inner_text() if elem else ""
                            if text and ("votes" in text.lower() or "reviews" in text.lower()):
                                if any(char.isdigit() for char in text):
                                    votes_text = text
                                    break
                        if votes_text:
                            break
                    else:
                        element = await page.query_selector(selector)
                        if element:
                            text = await element.inner_text()
                            if text and text.strip():
                                votes_text = text.strip()
                                break
                except Exception:
                    continue
            
            item['npv'] = votes_text or "0"
            
            # Consultation fee - try multiple selectors
            fee_text = None
            fee_selectors = [
                'span.u-strike',  # Original selector
                'div.u-f-right.u-large-font.u-bold.u-valign--middle.u-lheight-normal',  # Original alternative
                '*[class*="fee"]',  # Any element with "fee" in class
                '*[class*="price"]',  # Any element with "price" in class
                '*[class*="cost"]',  # Any element with "cost" in class
                '*[class*="consultation"]',  # Any element with "consultation" in class
                '.consultation-fee',  # Common pattern
                '.doctor-fee',  # Direct naming
                '.fee-amount',  # Fee amount
                'span[data-qa*="fee"]',  # Data attribute for fee
                'div[data-qa*="price"]',  # Data attribute for price
                'span:contains("₹")',  # Text-based search for rupee symbol
                'div:contains("₹")',  # Div with rupee symbol
                '.price-display',  # Price display
                '.consultation-price',  # Consultation price
            ]
            
            for selector in fee_selectors:
                try:
                    if 'contains' in selector:
                        # For text-based selectors, use different approach
                        elements = await page.query_selector_all('*')
                        for elem in elements:
                            text = await elem.inner_text() if elem else ""
                            if text and ("₹" in text or "rs" in text.lower()):
                                # Check if it's likely a fee (contains currency and numbers)
                                import re
                                if re.search(r'[₹$]\s*\d+|rs\s*\d+|\d+\s*[₹$]', text, re.IGNORECASE):
                                    fee_text = text
                                    break
                        if fee_text:
                            break
                    else:
                        element = await page.query_selector(selector)
                        if element:
                            text = await element.inner_text()
                            if text and text.strip():
                                # Validate that this looks like a fee
                                import re
                                if re.search(r'[₹$]\s*\d+|rs\s*\d+|\d+\s*[₹$]|\d+', text, re.IGNORECASE):
                                    fee_text = text.strip()
                                    break
                except Exception:
                    continue
            
            item['consultation_fee'] = fee_text or ""
            
            # Only yield if we have essential data (name is the minimum requirement)
            if item.get('name'):
                yield item
            else:
                self.logger.warning(f"Skipping profile without name: {response.url}")
                
        except Exception as e:
            self.logger.error(f"Error parsing doctor profile {response.url}: {str(e)}")
        
        finally:
            await page.close()
    
    def handle_error(self, failure):
        """Handle request errors"""
        self.logger.error(f"Request failed: {failure.request.url} - {failure.value}")
        
    def closed(self, reason):
        """Called when spider is closed"""
        self.logger.info(f"Spider closed: {reason}")
