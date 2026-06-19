import os
from dotenv import load_dotenv

from src.scraper.osm_scraper import OSMScraper
from src.scraper.website_checker import WebsiteChecker
from src.processor.data_cleaner import DataCleaner
from src.ai_analysis.business_analyzer import BusinessAnalyzer
from src.sheets.google_sheets_client import GoogleSheetsClient

def main():
    load_dotenv()
    print("Starting AI-Based Business Lead Discovery & Market Intelligence System...\n")
    
    industry = input("Enter target industry (e.g., Hotels): ").strip()
    location = input("Enter target location (e.g., Indore): ").strip()
    
    if not industry or not location:
        print("Industry and Location are required. Exiting.")
        return

    # Step 1: Data Collection via OpenStreetMap (free, no API key needed)
    print("\n--- Step 1: Data Collection (OpenStreetMap) ---")
    scraper = OSMScraper()
    raw_data = scraper.search_businesses(industry, location, max_results=5)
    scraper.close()
    
    if not raw_data:
        print("No businesses found. Try a different industry keyword or a larger city.")
        return

    # Step 2: Data Processing
    print("\n--- Step 2: Data Processing ---")
    cleaner = DataCleaner()
    df = cleaner.clean_data(raw_data)
    print(f"Cleaned data reveals {len(df)} unique businesses.")
    
    # Step 3: Website Checking
    print("\n--- Step 3: Website Checking ---")
    checker = WebsiteChecker()
    website_statuses = []
    for url in df['Website URL']:
        status = checker.check_website(url)
        website_statuses.append(status)
    df['Website Status'] = website_statuses
    
    # Step 4: Data Classification (Potential)
    df['Potential Category'] = df['Website Status'].apply(DataCleaner.classify_digital_opportunity)
    
    # Step 5: AI-Based Analysis (Optional but recommended)
    print("\n--- Step 4: AI Analysis ---")
    analyzer = BusinessAnalyzer()
    ai_insights = []
    for idx, row in df.iterrows():
        insight = analyzer.analyze_opportunity(row['Business Name'], industry, row['Website Status'])
        ai_insights.append(insight)
    df['AI Insight'] = ai_insights
    
    # Restructure dataframe for final output
    final_columns = [
        'Business Name', 'Category', 'Location', 'Website Status', 
        'Phone Number', 'Email Address', 'Potential Category', 'AI Insight', 
        'Google Maps Profile Link', 'Website URL'
    ]
    df = df[[c for c in final_columns if c in df.columns]]
    
    # Step 6: Google Sheets Automation
    print("\n--- Step 5: Data Export to Google Sheets ---")
    sheets_client = GoogleSheetsClient()
    sheets_client.export_to_sheet(df)
    
    if os.getenv("SAVE_LOCAL_CSV", "false").lower() in ("1", "true", "yes"):
        os.makedirs("data", exist_ok=True)
        csv_path = os.path.join("data", f"{industry}_{location}_leads.csv")
        df.to_csv(csv_path, index=False)
        print(f"\nSaved local backup to {csv_path}")

    print("\nSystem Workflow Complete.")

if __name__ == "__main__":
    main()
