#!/usr/bin/env python3
"""
Run script for Practo Scraper

This script runs the practo_doctors spider to scrape doctor data from Practo.com
"""

import os
import sys
import subprocess

def main():
    # Change to the scraper directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print(f"Working directory: {os.getcwd()}")
    print("Running Practo scraper...")
    
    # Run the spider
    cmd = ["scrapy", "crawl", "practo_doctors"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
            
        return result.returncode
        
    except Exception as e:
        print(f"Error running scraper: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())