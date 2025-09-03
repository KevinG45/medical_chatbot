# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class DoctorItem(scrapy.Item):
    # define the fields for your item here like:
    name = scrapy.Field()
    speciality = scrapy.Field()
    city = scrapy.Field()
    url = scrapy.Field()
    experience = scrapy.Field()
    location = scrapy.Field()
    fees = scrapy.Field()
    phone = scrapy.Field()
    rating = scrapy.Field()
    reviews = scrapy.Field()
    clinic_name = scrapy.Field()
    clinic_address = scrapy.Field()
    availability = scrapy.Field()