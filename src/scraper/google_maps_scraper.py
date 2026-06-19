import os
import logging
import requests

logger = logging.getLogger(__name__)

class GoogleMapsScraper:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        
    def search_businesses(self, query, location, max_results=10):
        """
        Fetches highly accurate business data directly from the official Google Places API.
        """
        print(f"Fetching businesses for '{query}' in '{location}' via API...")
        
        if not self.api_key or self.api_key == "your_google_places_api_key_here":
            print("Error: GOOGLE_PLACES_API_KEY is missing. Returning empty results.")
            return []

        search_query = f"{query} in {location}"
        
        # 1. Text Search API to find places
        text_search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        search_params = {
            "query": search_query,
            "key": self.api_key
        }
        
        try:
            logger.info("Calling Google Places Text Search for '%s' in '%s'", query, location)
            response = requests.get(text_search_url, params=search_params)
            logger.info("Returned from Google Places Text Search for '%s' in '%s'", query, location)
            response.raise_for_status()
            search_data = response.json()
            
            places = search_data.get("results", [])[:max_results]
            results = []
            
            print(f"Found {len(places)} places. Fetching detailed contact info...")
            
            # 2. Place Details API to get phone numbers and websites
            details_url = "https://maps.googleapis.com/maps/api/place/details/json"
            for place in places:
                place_id = place.get("place_id")
                
                details_params = {
                    "place_id": place_id,
                    "fields": "name,formatted_address,formatted_phone_number,website,url",
                    "key": self.api_key
                }
                
                logger.info("Calling Google Places Details for place_id=%s", place_id)
                detail_response = requests.get(details_url, params=details_params)
                logger.info("Returned from Google Places Details for place_id=%s", place_id)
                detail_data = detail_response.json().get("result", {})
                
                results.append({
                    "Business Name": detail_data.get("name", place.get("name", "Unknown")),
                    "Category": query,
                    "Location": location,
                    "Google Maps Profile Link": detail_data.get("url", f"https://www.google.com/maps/place/?q=place_id:{place_id}"),
                    "Website URL": detail_data.get("website"),
                    "Phone Number": detail_data.get("formatted_phone_number"),
                    "Email Address": None, # Google Places API natively omits emails
                })
                
            print(f"Successfully processed {len(results)} businesses via API.")
            return results

        except requests.exceptions.RequestException as e:
            print(f"API Request failed: {e}")
            return []

    def close(self):
        # API doesn't require closing a browser, but we keep the method so main.py doesn't break
        pass

if __name__ == "__main__":
    scraper = GoogleMapsScraper()
    data = scraper.search_businesses("Hotels", "Indore", 5)
    print(data)
    scraper.close()
