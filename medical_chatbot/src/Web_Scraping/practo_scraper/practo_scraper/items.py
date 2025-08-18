# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class DoctorItem(scrapy.Item):
    """Item class for doctor information from Practo"""
    
    # Basic information
    name = scrapy.Field()
    speciality = scrapy.Field()
    degree = scrapy.Field()
    year_of_experience = scrapy.Field()
    
    # Location information  
    location = scrapy.Field()
    city = scrapy.Field()
    
    # Rating and reviews
    dp_score = scrapy.Field()
    npv = scrapy.Field()  # Number of patient votes
    
    # Pricing
    consultation_fee = scrapy.Field()
    
    # Additional fields for data quality
    scraped_at = scrapy.Field()
    profile_url = scrapy.Field()
    # Direct Google Map link from Practo page
    google_map_link = scrapy.Field()
