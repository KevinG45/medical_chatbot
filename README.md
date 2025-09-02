# Medical Chatbot - Bangalore Doctor Scraper

A web scraping project to collect comprehensive doctor information from Practo.com for Bangalore doctors. This data will be used to build a medical chatbot that recommends doctors based on symptoms and location.

## Project Overview

- **Target**: Scrape all doctor details in Bangalore from Practo.com
- **Technology**: Scrapy + Playwright + scrapy-playwright
- **Database**: SQLite for development, PostgreSQL ready for production
- **Data Points**: Doctor name, speciality, qualifications, experience, location, ratings, consultation fees, Google Maps links

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Run the scraper
cd doctor_scraper
scrapy crawl bangalore_doctors

# Check results
ls data/
```

## Features

- Handles JavaScript-heavy content with Playwright
- Pagination support for 2000+ doctors
- Comprehensive data validation and cleaning
- Google Maps link extraction
- SQLite database storage with export capabilities
- Rate limiting and error handling