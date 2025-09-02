"""
Define here the models for your scraped items

See documentation in:
https://docs.scrapy.org/en/latest/topics/items.html
"""

import scrapy


class DoctorItem(scrapy.Item):
    """Item class for doctor information from Practo"""
    
    # Basic Information
    name = scrapy.Field()
    speciality = scrapy.Field()
    qualifications = scrapy.Field()
    experience_years = scrapy.Field()
    
    # Location Information
    clinic_name = scrapy.Field()
    area = scrapy.Field()
    city = scrapy.Field()
    full_address = scrapy.Field()
    
    # Contact Information
    phone = scrapy.Field()
    
    # Rating & Reviews
    rating = scrapy.Field()
    reviews_count = scrapy.Field()
    patient_stories = scrapy.Field()
    
    # Pricing
    consultation_fee = scrapy.Field()
    
    # Availability
    available_today = scrapy.Field()
    next_available_slot = scrapy.Field()
    
    # Links and References
    profile_url = scrapy.Field()
    google_map_link = scrapy.Field()
    
    # Metadata
    scraped_at = scrapy.Field()
    source = scrapy.Field()
    
    # Additional Information
    about = scrapy.Field()
    services = scrapy.Field()
    awards = scrapy.Field()