import requests
import time
import logging

logger = logging.getLogger(__name__)


class OSMScraper:
    """
    Scrapes business data using free OpenStreetMap APIs:
    - Nominatim: geocodes the location string into lat/lon + bounding box
    - Overpass API: searches for POIs (businesses) within that area

    No API key required. Respects Nominatim's 1 req/sec rate limit.
    Also extracts social-media presence tags so downstream scoring is richer.
    """

    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
    OVERPASS_URL  = "https://overpass-api.de/api/interpreter"

    # Maps common industry keywords to OSM tags for Overpass queries
    INDUSTRY_TAG_MAP = {
        "restaurant":      '"amenity"="restaurant"',
        "restaurants":     '"amenity"="restaurant"',
        "hotel":           '"tourism"="hotel"',
        "hotels":          '"tourism"="hotel"',
        "cafe":            '"amenity"="cafe"',
        "cafes":           '"amenity"="cafe"',
        "dentist":         '"amenity"="dentist"',
        "dentists":        '"amenity"="dentist"',
        "gym":             '"leisure"="fitness_centre"',
        "gyms":            '"leisure"="fitness_centre"',
        "salon":           '"shop"="beauty"',
        "salons":          '"shop"="beauty"',
        "clinic":          '"amenity"="clinic"',
        "clinics":         '"amenity"="clinic"',
        "hospital":        '"amenity"="hospital"',
        "hospitals":       '"amenity"="hospital"',
        "pharmacy":        '"amenity"="pharmacy"',
        "pharmacies":      '"amenity"="pharmacy"',
        "school":          '"amenity"="school"',
        "schools":         '"amenity"="school"',
        "bank":            '"amenity"="bank"',
        "banks":           '"amenity"="bank"',
        "supermarket":     '"shop"="supermarket"',
        "supermarkets":    '"shop"="supermarket"',
        "plumber":         '"craft"="plumber"',
        "plumbers":        '"craft"="plumber"',
        "lawyer":          '"office"="lawyer"',
        "lawyers":         '"office"="lawyer"',
        "law firm":        '"office"="lawyer"',
        "law firms":       '"office"="lawyer"',
        "real estate":     '"office"="estate_agent"',
        "bakery":          '"shop"="bakery"',
        "bakeries":        '"shop"="bakery"',
        "bar":             '"amenity"="bar"',
        "bars":            '"amenity"="bar"',
        "car repair":      '"shop"="car_repair"',
        "mechanic":        '"shop"="car_repair"',
        "pet shop":        '"shop"="pet"',
        "pet shops":       '"shop"="pet"',
        "clothing":        '"shop"="clothes"',
        "clothing store":  '"shop"="clothes"',
        "electronics":     '"shop"="electronics"',
    }

    HEADERS = {
        "User-Agent": "LeadForge/1.0 (business-lead-discovery-project)"
    }

    def __init__(self):
        pass

    def _geocode_location(self, location):
        """Uses Nominatim to convert a location name into a bounding box."""
        params = {
            "q": location,
            "format": "json",
            "limit": 1,
            "addressdetails": 1,
        }
        try:
            logger.info("Calling Nominatim geocode for %s", location)
            resp = requests.get(self.NOMINATIM_URL, params=params, headers=self.HEADERS, timeout=10)
            logger.info("Returned from Nominatim geocode for %s", location)
            resp.raise_for_status()
            data = resp.json()
            if not data:
                print(f"Nominatim could not find location: '{location}'")
                return None

            place = data[0]
            bbox = place.get("boundingbox")  # [south, north, west, east]
            if bbox:
                south, north, west, east = float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])
                return (south, west, north, east)
            else:
                lat, lon = float(place["lat"]), float(place["lon"])
                delta = 0.05
                return (lat - delta, lon - delta, lat + delta, lon + delta)
        except requests.RequestException as e:
            print(f"Nominatim request failed: {e}")
            return None

    def _get_overpass_filter(self, industry):
        """Converts an industry keyword to an Overpass QL tag filter."""
        key = industry.lower().strip()
        if key in self.INDUSTRY_TAG_MAP:
            return self.INDUSTRY_TAG_MAP[key]
        return f'"name"~"{industry}"'

    @staticmethod
    def _extract_social(tags):
        """
        Extracts social-media and online-presence links from OSM tags.
        Returns a dict of platform → URL/handle (None if not present).
        """
        def _clean(val):
            if not val:
                return None
            val = val.strip()
            return val if val else None

        facebook  = _clean(tags.get("contact:facebook")  or tags.get("facebook"))
        instagram = _clean(tags.get("contact:instagram") or tags.get("instagram"))
        twitter   = _clean(tags.get("contact:twitter")   or tags.get("twitter"))
        linkedin  = _clean(tags.get("contact:linkedin")  or tags.get("linkedin"))
        youtube   = _clean(tags.get("contact:youtube")   or tags.get("youtube"))
        wikipedia = _clean(tags.get("wikipedia"))
        tripadvisor = _clean(tags.get("contact:tripadvisor") or tags.get("tripadvisor"))

        # Normalise to full URLs where only a handle was given
        def _fb_url(v):
            if v and not v.startswith("http"):
                return f"https://facebook.com/{v.lstrip('@').lstrip('/')}"
            return v

        def _ig_url(v):
            if v and not v.startswith("http"):
                return f"https://instagram.com/{v.lstrip('@')}"
            return v

        def _tw_url(v):
            if v and not v.startswith("http"):
                return f"https://twitter.com/{v.lstrip('@')}"
            return v

        return {
            "Facebook URL":    _fb_url(facebook),
            "Instagram URL":   _ig_url(instagram),
            "Twitter URL":     _tw_url(twitter),
            "LinkedIn URL":    linkedin,
            "YouTube URL":     youtube,
            "Wikipedia URL":   wikipedia,
            "TripAdvisor URL": tripadvisor,
        }

    def search_businesses(self, industry, location, max_results=20):
        """
        Searches for businesses using OSM Nominatim + Overpass API.
        Returns a list of dicts matching the existing data schema, enriched with
        social-media presence fields.
        """
        print(f"Geocoding location '{location}' via Nominatim...")
        bbox = self._geocode_location(location)
        if not bbox:
            return []

        south, west, north, east = bbox
        tag_filter = self._get_overpass_filter(industry)
        print(f"Searching OSM for '{industry}' in bounding box ({south},{west},{north},{east})...")

        time.sleep(1)  # Nominatim rate limit

        overpass_query = f"""
        [out:json][timeout:45];
        (
          node[{tag_filter}]({south},{west},{north},{east});
          way[{tag_filter}]({south},{west},{north},{east});
          relation[{tag_filter}]({south},{west},{north},{east});
        );
        out center body {max_results};
        """

        try:
            logger.info("Calling Overpass search for %s", industry)
            resp = requests.post(
                self.OVERPASS_URL, data={"data": overpass_query},
                headers=self.HEADERS, timeout=60
            )
            logger.info("Returned from Overpass search for %s", industry)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            print(f"Overpass API request failed: {e}")
            return []

        elements = data.get("elements", [])
        print(f"Found {len(elements)} results from OpenStreetMap.")

        results = []
        for el in elements[:max_results]:
            tags = el.get("tags", {})
            name = tags.get("name", "Unknown Business")

            # Build address from OSM tags
            addr_parts = []
            for part in ["addr:housenumber", "addr:street", "addr:city", "addr:state", "addr:postcode"]:
                if part in tags:
                    addr_parts.append(tags[part])
            address = ", ".join(addr_parts) if addr_parts else location

            # Coordinates
            lat = el.get("lat") or el.get("center", {}).get("lat")
            lon = el.get("lon") or el.get("center", {}).get("lon")

            osm_type = el.get("type", "node")
            osm_id   = el.get("id", "")
            osm_link = f"https://www.openstreetmap.org/{osm_type}/{osm_id}"

            social = self._extract_social(tags)

            record = {
                "Business Name":        name,
                "Category":             industry,
                "Location":             address,
                "Google Maps Profile Link": osm_link,
                "Website URL":          tags.get("website") or tags.get("contact:website"),
                "Phone Number":         tags.get("phone") or tags.get("contact:phone"),
                "Email Address":        tags.get("email") or tags.get("contact:email"),
            }
            record.update(social)
            results.append(record)

        print(f"Successfully processed {len(results)} businesses via OpenStreetMap.")
        return results

    def close(self):
        """Compatibility method — no resources to release."""
        pass


if __name__ == "__main__":
    scraper = OSMScraper()
    data = scraper.search_businesses("Hotels", "Indore", 5)
    for d in data:
        print(d)
