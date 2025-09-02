import scrapy
from scrapy_playwright.page import PageMethod
from urllib.parse import urlencode, quote_plus
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
            
            # Name
            name_element = await page.query_selector('h1.c-profile__title')
            if name_element:
                item['name'] = await name_element.inner_text()
            
            # Degree
            degree_element = await page.query_selector('p.c-profile__details')
            if degree_element:
                item['degree'] = await degree_element.inner_text()
            
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
                'div[data-qa*="experience"]'  # Data attribute
            ]
            
            for selector in experience_selectors:
                try:
                    if 'contains' in selector:
                        # For text-based selectors, use different approach
                        elements = await page.query_selector_all('*')
                        for elem in elements:
                            text = await elem.inner_text() if elem else ""
                            if text and ("years" in text.lower() or "experience" in text.lower()):
                                if any(char.isdigit() for char in text):
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
            
            # If no direct map link found, try enhanced strategies
            if not google_map_link:
                try:
                    # Strategy 1: Look for elements with coordinates in data attributes
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
            
            # Strategy 2: Extract coordinates from page source/JavaScript
            if not google_map_link:
                try:
                    page_content = await page.content()
                    # Look for coordinate patterns in the page source
                    import re
                    coord_patterns = [
                        r'[\"\']?lat[\"\']?\s*[:=]\s*[\"\']*(-?\d+\.?\d*)[\"\']*.*?[\"\']?lng[\"\']?\s*[:=]\s*[\"\']*(-?\d+\.?\d*)[\"\']*',
                        r'[\"\']?latitude[\"\']?\s*[:=]\s*[\"\']*(-?\d+\.?\d*)[\"\']*.*?[\"\']?longitude[\"\']?\s*[:=]\s*[\"\']*(-?\d+\.?\d*)[\"\']*',
                        r'google\.maps.*?(-?\d{1,3}\.\d+),\s*(-?\d{1,3}\.\d+)',
                        r'maps\.google.*?(-?\d{1,3}\.\d+),\s*(-?\d{1,3}\.\d+)',
                        r'LatLng\(\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*\)'
                    ]
                    
                    for pattern in coord_patterns:
                        matches = re.finditer(pattern, page_content, re.IGNORECASE)
                        for match in matches:
                            try:
                                lat, lng = float(match.group(1)), float(match.group(2))
                                # Basic validation for Indian coordinates
                                if 6 <= lat <= 37 and 68 <= lng <= 98:  # India bounds
                                    google_map_link = f"https://www.google.com/maps?q={lat},{lng}"
                                    break
                            except (ValueError, IndexError):
                                continue
                        if google_map_link:
                            break
                except Exception:
                    pass
            
            # Strategy 3: Look for button elements that might trigger map display
            if not google_map_link:
                try:
                    map_buttons = await page.query_selector_all('button, a, div')
                    for button in map_buttons[:20]:  # Limit to avoid too many checks
                        button_text = await button.inner_text() if button else ""
                        button_class = await button.get_attribute('class') or ""
                        button_id = await button.get_attribute('id') or ""
                        onclick = await button.get_attribute('onclick') or ""
                        
                        if any(keyword in (button_text + button_class + button_id + onclick).lower() 
                               for keyword in ['direction', 'location', 'map', 'navigate']):
                            # Check for data attributes on this element
                            for attr in ['data-lat', 'data-lng', 'data-latitude', 'data-longitude']:
                                coord = await button.get_attribute(attr)
                                if coord:
                                    try:
                                        coord_val = float(coord)
                                        if attr in ['data-lat', 'data-latitude']:
                                            lat = coord_val
                                            lng_attr = 'data-lng' if 'data-lat' in attr else 'data-longitude'
                                            lng_val = await button.get_attribute(lng_attr)
                                            if lng_val:
                                                lng = float(lng_val)
                                                if 6 <= lat <= 37 and 68 <= lng <= 98:
                                                    google_map_link = f"https://www.google.com/maps?q={lat},{lng}"
                                                    break
                                    except ValueError:
                                        continue
                        if google_map_link:
                            break
                except Exception:
                    pass
            
            # Strategy 4: Generate map link from location text when available
            if not google_map_link and location_text and location_text.strip():
                try:
                    # Clean location text for search
                    clean_location = location_text.strip()
                    # Remove common unwanted parts
                    clean_location = re.sub(r':\s*Practo$', '', clean_location)
                    clean_location = re.sub(r'^[^,]+,\s*', '', clean_location)  # Remove clinic name if present
                    
                    if clean_location and len(clean_location) > 3:
                        # Add city if not already present
                        city_name = response.meta.get('city', '')
                        if city_name and city_name.lower() not in clean_location.lower():
                            clean_location = f"{clean_location}, {city_name}"
                        
                        # Create Google Maps search URL
                        from urllib.parse import quote_plus
                        encoded_location = quote_plus(clean_location)
                        google_map_link = f"https://www.google.com/maps/search/{encoded_location}"
                except Exception:
                    pass
            
            # Strategy 5: Last resort - use city name if available
            if not google_map_link:
                try:
                    city_name = response.meta.get('city', '')
                    if city_name:
                        from urllib.parse import quote_plus
                        encoded_city = quote_plus(city_name)
                        google_map_link = f"https://www.google.com/maps/search/{encoded_city}"
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
            
            # Consultation fee
            fee_element = await page.query_selector('span.u-strike')
            if fee_element:
                item['consultation_fee'] = await fee_element.inner_text()
            else:
                # Try alternative selector
                fee_element = await page.query_selector('div.u-f-right.u-large-font.u-bold.u-valign--middle.u-lheight-normal')
                if fee_element:
                    item['consultation_fee'] = await fee_element.inner_text()
            
            # Only yield if we have essential data
            if item.get('name') and item.get('consultation_fee'):
                yield item
            else:
                self.logger.warning(f"Skipping incomplete profile: {response.url}")
                
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
