import scrapy
from scrapy_playwright.page import PageMethod
from urllib.parse import urlencode
import time
import re
from practo_scraper.items import DoctorItem
import sys
import os
import asyncio

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
                # Build the search URL
                params = {
                    'results_type': 'doctor',
                    'q': f'[{{"word":"{speciality}","autocompleted":true,"category":"subspeciality"}}]',
                    'city': city
                }
                url = f"https://www.practo.com/search/doctors?{urlencode(params)}"
                
                yield scrapy.Request(
                    url=url,
                    meta={
                        "playwright": True,
                        "playwright_include_page": True,
                        "playwright_page_methods": [
                            PageMethod("wait_for_selector", "div.info-section", timeout=30000),
                        ],
                        "city": city,
                        "speciality": speciality,
                    },
                    callback=self.parse_doctors_listing,
                    errback=self.handle_error,
                )

    async def parse_doctors_listing(self, response):
        """Parse the doctors listing page and extract doctor profile URLs"""
        page = response.meta["playwright_page"]
        city = response.meta["city"]
        speciality = response.meta["speciality"]
        
        try:
            # Scroll to load all doctors
            await self.scroll_to_load_all(page)
            
            # Extract doctor profile URLs
            doctor_links = await page.query_selector_all('a[data-qa-id="doctor_name"], .doctor-name a, .listing-doctor-name a')
            
            for link in doctor_links:
                href = await link.get_attribute('href')
                if href:
                    full_url = response.urljoin(href)
                    yield scrapy.Request(
                        url=full_url,
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
            # Fix for asyncio loop issue: ensure page.close() is called in the correct loop
            try:
                if page and not page.is_closed():
                    # Get the current loop to ensure we're in the right context
                    loop = asyncio.get_running_loop()
                    # Create a task in the current loop to close the page
                    await asyncio.create_task(page.close())
            except Exception as close_error:
                self.logger.warning(f"Error closing page: {str(close_error)}")

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
        page = response.meta["playwright_page"]
        city = response.meta["city"]
        speciality = response.meta["speciality"]
        
        try:
            # Extract doctor information
            item = DoctorItem()
            
            # Basic information
            item['name'] = await self.extract_text(page, 'h1.c-profile__title, .doctor-name h1')
            item['speciality'] = speciality
            item['city'] = city
            item['url'] = response.url
            
            # Additional fields can be added here based on the page structure
            item['experience'] = await self.extract_text(page, '.c-profile__experience, .experience')
            item['location'] = await self.extract_text(page, '.c-profile__location, .location')
            item['fees'] = await self.extract_text(page, '.c-profile__fee, .fee')
            
            yield item
            
        except Exception as e:
            self.logger.error(f"Error parsing doctor profile {response.url}: {str(e)}")
        
        finally:
            # Fix for asyncio loop issue: ensure page.close() is called in the correct loop  
            try:
                if page and not page.is_closed():
                    # Get the current loop to ensure we're in the right context
                    loop = asyncio.get_running_loop()
                    # Create a task in the current loop to close the page
                    await asyncio.create_task(page.close())
            except Exception as close_error:
                self.logger.warning(f"Error closing page: {str(close_error)}")

    async def extract_text(self, page, selector):
        """Extract text content from page using selector"""
        try:
            element = await page.query_selector(selector)
            if element:
                return await element.text_content()
        except Exception:
            pass
        return None

    def handle_error(self, failure):
        """Handle request errors"""
        self.logger.error(f"Request failed: {failure.request.url} - {failure.value}")
        
    def closed(self, reason):
        """Called when spider is closed"""
        self.logger.info(f"Spider closed: {reason}")