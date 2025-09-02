#!/usr/bin/env python3
"""
Runner script for Practo Scraper
This script runs the Scrapy spider programmatically
"""

import os
import sys
import argparse
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_spider(spider_name="practo_doctors_simple", item_limit=None):
    """Run the Practo doctors spider
    
    Args:
        spider_name: Which spider to run ("practo_doctors" or "practo_doctors_simple")
        item_limit: Optional limit on number of items to scrape
    """
    
    # Get the Scrapy project settings
    settings = get_project_settings()
    
    # Add item limit if specified
    if item_limit:
        settings.set('CLOSESPIDER_ITEMCOUNT', item_limit)
    
    # For the simple spider, disable Playwright handlers to avoid conflicts
    if spider_name == "practo_doctors_simple":
        settings.set('DOWNLOAD_HANDLERS', {})
        print("Running simple spider - Playwright disabled")
    
    # Create crawler process
    process = CrawlerProcess(settings)
    
    # Add the spider to the process
    process.crawl(spider_name)
    
    # Start the crawling process
    process.start()

def main():
    parser = argparse.ArgumentParser(description='Run Practo Doctor Scraper')
    parser.add_argument('--spider', 
                       choices=['simple', 'enhanced'], 
                       default='simple',
                       help='Which spider to use: simple (HTTP) or enhanced (Playwright)')
    parser.add_argument('--limit', 
                       type=int, 
                       help='Limit number of items to scrape (for testing)')
    
    args = parser.parse_args()
    
    # Map spider choices to actual spider names
    spider_map = {
        'simple': 'practo_doctors_simple',
        'enhanced': 'practo_doctors'
    }
    
    spider_name = spider_map[args.spider]
    
    print(f"Starting Practo Scraper using {spider_name}...")
    
    if args.spider == 'enhanced':
        print("Note: Enhanced spider requires Playwright browsers to be installed.")
        print("Run 'python -m playwright install chromium' if not installed.")
    
    if args.limit:
        print(f"Limited to {args.limit} items for testing.")
    
    try:
        run_spider(spider_name, args.limit)
        print("Scraping completed!")
    except Exception as e:
        error_msg = str(e).lower()
        print(f"Error during scraping: {e}")
        
        if "playwright" in error_msg:
            print("\n🔧 Playwright Error Detected!")
            print("This could be due to:")
            print("1. Playwright browsers not installed - run: python -m playwright install chromium")
            print("2. Playwright package issues - try: pip install --upgrade scrapy-playwright")
            print("3. Browser dependencies missing in environment")
            print("\n💡 Try using the simple spider instead:")
            print("python run_scraper.py --spider simple")
        elif "spider not found" in error_msg:
            print(f"\n🕷️ Spider '{spider_name}' not found!")
            print("Available spiders: simple, enhanced")
            print("Use: python run_scraper.py --spider simple")
        elif "module" in error_msg and "not found" in error_msg:
            print(f"\n📦 Missing Dependencies!")
            print("Install required packages with:")
            print("pip install -r requirements.txt")
        elif "connection" in error_msg or "network" in error_msg:
            print(f"\n🌐 Network Error!")
            print("Check internet connection and try again")
        else:
            print(f"\n❌ Unexpected error occurred")
            print("Check the scrapy.log file for more details")

if __name__ == "__main__":
    main()
