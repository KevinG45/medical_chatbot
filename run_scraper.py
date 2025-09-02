#!/usr/bin/env python3
"""
Bangalore Doctors Scraper Runner

This script provides an easy way to run the doctor scraper with various options.
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime

def run_scraper(spider_name="bangalore_doctors", output_format="all", max_pages=None, specialities=None):
    """Run the Scrapy spider with specified options"""
    
    # Change to the scraper directory
    scraper_dir = os.path.join(os.path.dirname(__file__), 'doctor_scraper')
    os.chdir(scraper_dir)
    
    # Build the scrapy command
    cmd = ["scrapy", "crawl", spider_name]
    
    # Add custom settings if specified
    if max_pages:
        cmd.extend(["-s", f"MAX_PAGES={max_pages}"])
    
    if specialities:
        # Convert list to string for passing as argument
        specialities_str = ",".join(specialities)
        cmd.extend(["-s", f"SPECIALITIES={specialities_str}"])
    
    # Set output format
    if output_format in ["csv", "all"]:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cmd.extend(["-o", f"../data/doctors_{timestamp}.csv"])
    
    print(f"Running command: {' '.join(cmd)}")
    print(f"Working directory: {os.getcwd()}")
    
    try:
        # Run the scraper
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("\\nScraping completed successfully!")
            print(f"Check the data/ directory for output files.")
        else:
            print(f"\\nScraping failed with return code: {result.returncode}")
            
    except FileNotFoundError:
        print("Error: Scrapy not found. Please install scrapy first:")
        print("pip install scrapy")
        sys.exit(1)
    except Exception as e:
        print(f"Error running scraper: {e}")
        sys.exit(1)

def setup_environment():
    """Setup the environment and check dependencies"""
    
    print("Checking dependencies...")
    
    # Check if scrapy is installed
    try:
        import scrapy
        print(f"✓ Scrapy {scrapy.__version__} is available")
    except ImportError:
        print("✗ Scrapy not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "scrapy"])
            print("✓ Scrapy installed successfully")
        except Exception as e:
            print(f"✗ Failed to install Scrapy: {e}")
            return False
    
    # Check other dependencies
    try:
        import sqlite3
        print("✓ SQLite3 is available")
    except ImportError:
        print("✗ SQLite3 not found")
        return False
    
    # Create necessary directories
    dirs_to_create = ['data', 'logs']
    for dir_name in dirs_to_create:
        os.makedirs(dir_name, exist_ok=True)
        print(f"✓ Directory '{dir_name}' ready")
    
    return True

def main():
    """Main function to handle command line arguments and run the scraper"""
    
    parser = argparse.ArgumentParser(description="Bangalore Doctors Scraper")
    
    parser.add_argument(
        "--setup", 
        action="store_true", 
        help="Setup environment and install dependencies"
    )
    
    parser.add_argument(
        "--run", 
        action="store_true", 
        help="Run the scraper"
    )
    
    parser.add_argument(
        "--spider", 
        default="bangalore_doctors",
        help="Name of the spider to run (default: bangalore_doctors)"
    )
    
    parser.add_argument(
        "--format", 
        choices=["csv", "json", "all"],
        default="all",
        help="Output format (default: all)"
    )
    
    parser.add_argument(
        "--max-pages", 
        type=int,
        help="Maximum pages to scrape per speciality"
    )
    
    parser.add_argument(
        "--specialities", 
        nargs="+",
        help="Specific specialities to scrape (space-separated)"
    )
    
    parser.add_argument(
        "--list-specialities", 
        action="store_true",
        help="List all available specialities"
    )
    
    args = parser.parse_args()
    
    if args.list_specialities:
        # Import config to list specialities
        sys.path.append(os.path.dirname(__file__))
        try:
            from config import SPECIALITIES
            print("Available specialities:")
            for i, spec in enumerate(SPECIALITIES, 1):
                print(f"{i:2d}. {spec}")
        except ImportError:
            print("Could not load specialities from config")
        return
    
    if args.setup:
        print("Setting up environment...")
        if setup_environment():
            print("\\n✓ Environment setup completed successfully!")
            print("You can now run the scraper with: python run_scraper.py --run")
        else:
            print("\\n✗ Environment setup failed!")
            sys.exit(1)
        return
    
    if args.run:
        print("Starting Bangalore doctors scraper...")
        run_scraper(
            spider_name=args.spider,
            output_format=args.format,
            max_pages=args.max_pages,
            specialities=args.specialities
        )
        return
    
    # If no action specified, show help
    parser.print_help()

if __name__ == "__main__":
    main()