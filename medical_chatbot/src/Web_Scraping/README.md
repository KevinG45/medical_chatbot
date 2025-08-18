
## Web Scraping Module

This folder contains the web scraping component of the medical chatbot project. It is designed to collect, clean, and store data about doctors from Practo for further use in recommendations and chatbot responses.

### Structure

- `practo_scraper/`: Main Scrapy project for scraping Practo doctor listings.
  - `spiders/practo_doctors.py`: Spider for crawling and extracting doctor data.
  - `items.py`, `pipelines.py`, `middlewares.py`, `settings.py`: Scrapy configuration and data processing.
  - `data/`: Contains cleaned CSV, database, and SQL files with processed doctor data.
- `run_scraper.py`: Script to run the scraper.
- `bangalore_enhanced.csv`: Example output data file.
- `config.py`: Configuration for scraping parameters.
- `requirements.txt`: Python dependencies for the scraping module.

### Usage

1. **Install dependencies**:
  ```bash
  pip install -r requirements.txt
  ```

2. **Run the scraper**:
  ```bash
  python practo_scraper/run_scraper.py
  ```

3. **Output**:
  - Scraped data will be saved in the `data/` folder as CSV, DB, and SQL files.

### Notes

- The scraped data is used by the chatbot to recommend doctors and answer user queries.
- You can modify `config.py` to change scraping parameters (e.g., location, filters).

For more details, see the code in the `practo_scraper` folder and the configuration files.
