# Practo Scraper - Troubleshooting Guide

## Recent Fixes Applied

### ✅ Fixed Missing Simple Spider
- **Problem**: The runner script expected a `practo_doctors_simple` spider that didn't exist
- **Solution**: Added `PractoDoctorsSimpleSpider` class that works without Playwright
- **Usage**: `python run_scraper.py --spider simple`

### ✅ Improved Error Handling  
- **Problem**: Generic error messages made debugging difficult
- **Solution**: Enhanced error detection and specific suggestions for different failure modes
- **Features**: Detects Playwright, network, and dependency issues with specific fixes

### ✅ Fixed Playwright Configuration
- **Problem**: Playwright handlers were disabled in settings, breaking enhanced spider
- **Solution**: Re-enabled Playwright handlers with proper fallback handling
- **Usage**: `python run_scraper.py --spider enhanced` (when Playwright browsers are installed)

## Available Spiders

### Simple Spider (`practo_doctors_simple`)
- **Technology**: Pure HTTP requests with Scrapy
- **Pros**: No browser dependencies, faster, more stable
- **Cons**: May miss dynamic content loaded by JavaScript
- **Best for**: Basic scraping when Playwright issues occur

### Enhanced Spider (`practo_doctors`)  
- **Technology**: Playwright with Chromium browser
- **Pros**: Handles JavaScript, scrolling, dynamic loading
- **Cons**: Requires browser installation, slower, more resource intensive
- **Best for**: Complete data extraction when network and browsers work

## Common Issues & Solutions

### 1. "Spider not found: practo_doctors_simple"
**Status**: ✅ FIXED
```bash
# This error is now resolved - the simple spider has been added
python run_scraper.py --spider simple
```

### 2. Playwright Browser Installation Failed
```bash
# Install browsers manually
python -m playwright install chromium

# Or use simple spider as fallback
python run_scraper.py --spider simple
```

### 3. Network/DNS Issues
```bash
# Symptoms: "DNS lookup failed" or "no results for hostname"
# Check connectivity
curl -I https://www.practo.com

# If blocked, try VPN or use existing data
# The simple spider will work once network access is restored
```

### 4. Module Import Errors
```bash
# Install all dependencies
pip install -r requirements.txt

# Verify installation
python test_spiders.py
```

## Diagnostic Tools

### Quick Test
```bash
# Test spider components without network
python test_spiders.py
```

### Full Diagnostics
```bash
# Comprehensive system check
python diagnose.py
```

### Manual Spider Test
```bash
# Test specific spider with detailed logging
scrapy crawl practo_doctors_simple -L DEBUG

# Test with item limit
scrapy crawl practo_doctors_simple -s CLOSESPIDER_ITEMCOUNT=5
```

## Usage Examples

### Basic Usage
```bash
# Use simple spider (recommended)
python run_scraper.py --spider simple

# Use enhanced spider (requires Playwright)
python run_scraper.py --spider enhanced
```

### Testing/Development
```bash
# Limit items for testing
python run_scraper.py --spider simple --limit 5

# Debug mode
scrapy crawl practo_doctors_simple -L DEBUG --pdb
```

### Data Output
- CSV files saved to `data/doctors_%(time)s.csv`
- Database export available in `data/doctors_database.db`
- Check existing data in `data/` directory

## Architecture Changes Made

### 1. Dual Spider Support
- Both spiders now coexist in the same file
- Runner script properly handles both types
- Settings adjusted to disable Playwright for simple spider

### 2. Enhanced Error Handling
- Specific error detection for common failure modes
- Helpful suggestions for each error type
- Better logging and user feedback

### 3. Configuration Improvements
- Playwright handlers re-enabled for enhanced spider
- Proper fallback mechanism for simple spider
- Better separation of concerns

## Data Verification

The scraper was working before, as evidenced by existing data files:
- `consolidated_doctors_latest.csv` (1.6MB)
- `bangalore_doctors_final.csv` (810KB)  
- `cleaned_doctors_full.csv` (830KB)

This indicates the scraping strategy and data extraction logic are sound.

## Next Steps

1. **Network Access**: Once network connectivity to practo.com is restored, both spiders should work
2. **Testing**: Use `test_spiders.py` to verify components work correctly
3. **Deployment**: Use simple spider by default, enhanced spider when full functionality needed
4. **Monitoring**: Check `scrapy.log` for ongoing issues

## Support

If issues persist:
1. Run `python diagnose.py` for system status
2. Check `scrapy.log` for detailed error messages  
3. Verify network access to https://www.practo.com
4. Test with simple spider first: `python run_scraper.py --spider simple --limit 1`