# AI-Based Business Lead Discovery & Market Intelligence System

This is a lightweight Python-based system that automatically discovers and organizes business information from publicly available sources. It helps analyze businesses, understand their digital presence, classify opportunities, and generate AI insights.

## Features
- **Data Collection:** Simulates scraping business listings (Google Maps).
- **Website Checking:** Analyzes digital presence (presence/absence of website, quality heuristics).
- **Data Processing:** Cleans and structures data using Pandas.
- **Data Intelligence:** Classifies business potential into High/Medium/Low based on web presence.
- **AI Analysis:** Optionally uses OpenAI to write a brief summary of the digital opportunity for each lead.
- **Google Sheets Integration:** Automatically exports collected datasets to a Google Sheet.

## Prerequisites
- Python 3.8+
- [Git](https://git-scm.com/) (optional)
- A Google Cloud Project with the Google Sheets & Drive API enabled (for Google Sheets sync)
- An OpenAI API Key (optional, for AI analysis)

## Setup Process

1. Clone or download this project.
2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up the Environment Variables:
   - Rename `.env.example` to `.env`.
   - Open `.env` and fill in your details:
     - `OPENAI_API_KEY`: Your OpenAI API Key (leave blank to skip AI analysis).
     - `GOOGLE_SHEETS_CREDENTIALS_FILE`: The path to your Google Service Account standard JSON format file.
     - `GOOGLE_SHEET_ID`: The ID of your target Google Sheet (from its URL).

## Running Instructions

Run the main orchestrator script:
```bash
python main.py
```

The system will prompt you for:
- **Target Industry:** e.g., "Hotels", "Manufacturing", "Restaurants"
- **Target Location:** e.g., "Indore", "New York", "London"

### Workflow Output
1. The script will scrape standard listings.
2. It deduplicates and cleans the data.
3. It performs a request against any discovered website links to categorise as "Good Website", "Poor Website", or "No Website".
4. Defines Priority (High/Medium/Low) based on website status.
5. If OpenAI is enabled, it generates a custom digital solution requirement sentence for the business.
6. Writes the final structured dataset into Google Sheets (if credentials provided), and always saves a local `.csv` file in the `data/` folder.

## Architecture & Project Structure
- `main.py` - Application entry point.
- `src/scraper/` - Contains logic to simulate scraping (`google_maps_scraper.py`) and website quality check (`website_checker.py`).
- `src/processor/` - Cleans raw data and categorizes website gaps (`data_cleaner.py`).
- `src/sheets/` - Automates updating target Google Spreadsheets (`google_sheets_client.py`).
- `src/ai_analysis/` - Interfaces with OpenAI chat completion (`business_analyzer.py`).
