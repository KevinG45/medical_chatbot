# Testing the Scraping Improvements

## Quick Test Commands

To test the improvements on a small sample:

```bash
# Navigate to scraper directory
cd medical_chatbot/src/Web_Scraping/practo_scraper

# Install dependencies
pip install -r ../requirements.txt
playwright install chromium

# Test with limited items (5 doctors only)
scrapy crawl practo_doctors -s CLOSESPIDER_ITEMCOUNT=5 -L INFO

# Check the output
ls -la data/
head -20 data/latest_doctors_data.csv
```

## Expected Improvements

You should see:
1. **More consultation fees extracted** (not just 0 values)
2. **Proper experience years** (1-50 range, not graduation years like 2001)
3. **Better data quality** overall
4. **Less data confusion** between experience and fees

## Validation Script

Run the validation script to test extraction logic:

```bash
cd medical_chatbot/src/Web_Scraping
python /tmp/test_extraction.py
```

## Data Analysis

To analyze existing data quality issues:

```bash
cd medical_chatbot/src/Web_Scraping  
python /tmp/analyze_data.py
```

This will show statistics about the problematic data in the current CSV file.

## Monitoring

Key metrics to monitor:
- **Consultation fee success rate**: Should improve from 48% to 80%+
- **Experience accuracy**: Should improve from 96.6% to 99%+
- **Data confusion elimination**: fee=experience cases should drop significantly

## Troubleshooting

If you encounter issues:

1. **Check logs**: Look for warnings about "Unusually high fee" or validation messages
2. **CSS selector updates**: If Practo changes their website, add new selectors to the spider
3. **Data validation**: The pipeline will log rejected values for debugging

## Next Steps

After testing confirms improvements:
1. Run full scrape on production data
2. Update the cleaned_doctors_full.csv file
3. Re-train the medical chatbot with higher quality data