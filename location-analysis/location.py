from serpapi import GoogleSearch
import json
import math
from datetime import datetime
import time
import os
from typing import Dict, List, Optional, Tuple

class HotspotFinder:
    def __init__(self, api_key: str):
        """Initialize the hotspot finder with API key"""
        self.api_key = api_key
        
        # Define categories of hotspots to search for
        self.hotspot_categories = {
            "tourist_attractions": ["tourist attraction", "monument", "museum", "temple", "church", "historical place"],
            "restaurants": ["restaurant", "cafe", "food court", "bar", "pub"],
            "shopping": ["shopping mall", "market", "shopping center", "store"],
            "entertainment": ["movie theater", "amusement park", "night club", "sports complex"],
            "accommodation": ["hotel", "resort", "guest house"],
            "services": ["hospital", "bank", "ATM", "gas station", "pharmacy"],
            "parks": ["park", "garden", "zoo", "lake", "beach"]
        }
    
    def get_restaurant_location(self, identifier: str, id_type: str = "auto") -> Optional[Dict]:
        """Get restaurant location from data_id or place_id"""
        print(f"🔍 Getting location for {id_type}: {identifier}")
        
        try:
            if id_type == "auto":
                # Auto-detect ID type
                if identifier.startswith("0x") or ":" in identifier:
                    id_type = "data_id"
                else:
                    id_type = "place_id"
            
            if id_type == "data_id":
                # Use Google Maps Reviews API to get place info
                params = {
                    "engine": "google_maps_reviews",
                    "data_id": identifier,
                    "api_key": self.api_key
                }
            else:
                # Use Google Maps API with place_id
                params = {
                    "engine": "google_maps",
                    "place_id": identifier,
                    "api_key": self.api_key
                }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            # Extract location info
            if id_type == "data_id" and "place_info" in results:
                place_info = results["place_info"]
                location_data = {
                    "name": place_info.get("title", "Unknown Restaurant"),
                    "address": place_info.get("address", "Unknown Address"),
                    "latitude": place_info.get("gps_coordinates", {}).get("latitude"),
                    "longitude": place_info.get("gps_coordinates", {}).get("longitude"),
                    "rating": place_info.get("rating"),
                    "reviews_count": place_info.get("reviews"),
                    "data_id": identifier,
                    "place_id": place_info.get("place_id")
                }
            elif "local_results" in results and results["local_results"]:
                place = results["local_results"][0]
                location_data = {
                    "name": place.get("title", "Unknown Restaurant"),
                    "address": place.get("address", "Unknown Address"),
                    "latitude": place.get("gps_coordinates", {}).get("latitude"),
                    "longitude": place.get("gps_coordinates", {}).get("longitude"),
                    "rating": place.get("rating"),
                    "reviews_count": place.get("reviews"),
                    "data_id": place.get("data_id"),
                    "place_id": identifier if id_type == "place_id" else place.get("place_id")
                }
            else:
                print("❌ Could not find location information")
                return None
            
            if not location_data["latitude"] or not location_data["longitude"]:
                print("❌ Could not get GPS coordinates")
                return None
            
            print(f"✅ Found: {location_data['name']}")
            print(f"📍 Location: {location_data['latitude']}, {location_data['longitude']}")
            
            return location_data
            
        except Exception as e:
            print(f"❌ Error getting restaurant location: {e}")
            return None
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in kilometers using Haversine formula"""
        R = 6371  # Earth's radius in kilometers
        
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def search_nearby_places(self, center_lat: float, center_lon: float, 
                           query: str, radius_km: int = 10) -> List[Dict]:
        """Search for places near the given coordinates"""
        print(f"🔍 Searching for '{query}' within {radius_km}km...")
        
        try:
            params = {
                "engine": "google_maps",
                "q": query,
                "ll": f"@{center_lat},{center_lon},{radius_km}km",
                "type": "search",
                "api_key": self.api_key
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            places = []
            if "local_results" in results:
                for place in results["local_results"]:
                    # Get coordinates
                    coords = place.get("gps_coordinates", {})
                    if coords.get("latitude") and coords.get("longitude"):
                        distance = self.calculate_distance(
                            center_lat, center_lon,
                            coords["latitude"], coords["longitude"]
                        )
                        
                        # Only include places within radius
                        if distance <= radius_km:
                            place_data = {
                                "name": place.get("title", "Unknown"),
                                "address": place.get("address", "Unknown Address"),
                                "rating": place.get("rating"),
                                "reviews_count": place.get("reviews"),
                                "price_level": place.get("price"),
                                "type": place.get("type", "Unknown"),
                                "latitude": coords["latitude"],
                                "longitude": coords["longitude"],
                                "distance_km": round(distance, 2),
                                "data_id": place.get("data_id"),
                                "place_id": place.get("place_id"),
                                "phone": place.get("phone"),
                                "website": place.get("website"),
                                "hours": place.get("hours"),
                                "category": query
                            }
                            places.append(place_data)
            
            return places
            
        except Exception as e:
            print(f"❌ Error searching for {query}: {e}")
            return []
    
    def find_all_hotspots(self, restaurant_location: Dict, radius_km: int = 10, 
                         categories: List[str] = None) -> Dict:
        """Find all types of hotspots around the restaurant"""
        print(f"\n🌟 Finding hotspots within {radius_km}km of {restaurant_location['name']}")
        print("=" * 60)
        
        center_lat = restaurant_location["latitude"]
        center_lon = restaurant_location["longitude"]
        
        all_hotspots = {}
        total_places = 0
        
        # Use specified categories or all categories
        categories_to_search = categories or list(self.hotspot_categories.keys())
        
        for category in categories_to_search:
            print(f"\n📍 Searching {category.replace('_', ' ').title()}...")
            all_hotspots[category] = []
            
            # Search for each subcategory
            for query in self.hotspot_categories[category]:
                places = self.search_nearby_places(center_lat, center_lon, query, radius_km)
                
                # Avoid duplicates by checking name and address
                for place in places:
                    is_duplicate = False
                    for existing in all_hotspots[category]:
                        if (existing["name"].lower() == place["name"].lower() and 
                            existing["address"].lower() == place["address"].lower()):
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        all_hotspots[category].append(place)
                
                # Small delay to avoid rate limiting
                time.sleep(0.5)
            
            # Sort by distance
            all_hotspots[category].sort(key=lambda x: x["distance_km"])
            category_count = len(all_hotspots[category])
            total_places += category_count
            
            print(f"   Found {category_count} {category.replace('_', ' ')}")
        
        print(f"\n✅ Total hotspots found: {total_places}")
        return all_hotspots
    
    def print_hotspots_summary(self, hotspots: Dict, restaurant_location: Dict):
        """Print a formatted summary of found hotspots"""
        print(f"\n{'='*80}")
        print(f"🏢 HOTSPOTS NEAR {restaurant_location['name'].upper()}")
        print(f"📍 Base Location: {restaurant_location['address']}")
        print(f"{'='*80}")
        
        for category, places in hotspots.items():
            if not places:
                continue
                
            print(f"\n🎯 {category.replace('_', ' ').upper()} ({len(places)} found)")
            print("-" * 50)
            
            for i, place in enumerate(places[:10], 1):  # Show top 10 per category
                print(f"{i:2d}. {place['name']}")
                print(f"    📍 {place['address']}")
                print(f"    📏 {place['distance_km']}km away")
                
                if place['rating']:
                    print(f"    ⭐ {place['rating']} ({place['reviews_count']} reviews)")
                
                if place['type']:
                    print(f"    🏷️  {place['type']}")
                
                if place['phone']:
                    print(f"    📞 {place['phone']}")
                
                if place['website']:
                    print(f"    🌐 {place['website']}")
                
                print()
    
    def save_hotspots_data(self, hotspots: Dict, restaurant_location: Dict, 
                          radius_km: int) -> str:
        """Save hotspots data to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = restaurant_location['name'].replace(' ', '_').replace('/', '_')
        filename = f"hotspots_near_{safe_name}_{radius_km}km_{timestamp}.json"
        
        try:
            # Create directory if it doesn't exist
            os.makedirs("hotspot_data", exist_ok=True)
            filepath = os.path.join("hotspot_data", filename)
            
            # Prepare data for saving
            data_to_save = {
                "restaurant_info": restaurant_location,
                "search_radius_km": radius_km,
                "search_timestamp": datetime.now().isoformat(),
                "total_hotspots": sum(len(places) for places in hotspots.values()),
                "hotspots_by_category": hotspots,
                "summary": {
                    category: len(places) 
                    for category, places in hotspots.items()
                }
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Saved hotspot data to: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ Error saving file: {e}")
            return ""
    
    def find_hotspots_by_id(self, identifier: str, id_type: str = "auto", 
                           radius_km: int = 10, categories: List[str] = None) -> Optional[Dict]:
        """Main method to find hotspots by restaurant ID"""
        print(f"🚀 Starting hotspot search for ID: {identifier}")
        print("-" * 60)
        
        # Step 1: Get restaurant location
        restaurant_location = self.get_restaurant_location(identifier, id_type)
        if not restaurant_location:
            return None
        
        # Step 2: Find hotspots
        hotspots = self.find_all_hotspots(restaurant_location, radius_km, categories)
        
        # Step 3: Display results
        self.print_hotspots_summary(hotspots, restaurant_location)
        
        # Step 4: Save data
        filepath = self.save_hotspots_data(hotspots, restaurant_location, radius_km)
        
        return {
            "restaurant_location": restaurant_location,
            "hotspots": hotspots,
            "saved_file": filepath
        }

def main():
    """Main function with user interface"""
    print("🌟 RESTAURANT HOTSPOT FINDER")
    print("Find interesting places near any restaurant!")
    print("=" * 50)
    
    # API key
    API_KEY = "27a0a1f71c847bfb0af9e970b2cfcc77badbb10fe456d4a9ac758d2b6190be19"
    
    # Initialize finder
    finder = HotspotFinder(API_KEY)
    
    while True:
        print("\n" + "="*50)
        
        # Get restaurant identifier
        identifier = input("Enter restaurant data_id or place_id (or 'quit' to exit): ").strip()
        
        if identifier.lower() in ['quit', 'exit', 'q']:
            print("👋 Thanks for using the hotspot finder!")
            break
        
        if not identifier:
            print("❌ Please enter a valid ID.")
            continue
        
        # Get ID type
        print("\nID Type:")
        print("1. Auto-detect (default)")
        print("2. data_id (format: 0x...)")
        print("3. place_id (Google Place ID)")
        
        id_type_choice = input("Choose ID type (1-3, default 1): ").strip()
        id_type_map = {"1": "auto", "2": "data_id", "3": "place_id"}
        id_type = id_type_map.get(id_type_choice, "auto")
        
        # Get search radius
        radius_input = input("Enter search radius in km (default 10): ").strip()
        try:
            radius_km = int(radius_input) if radius_input else 10
            radius_km = max(1, min(radius_km, 50))  # Limit between 1-50 km
        except ValueError:
            radius_km = 10
        
        # Get categories to search
        print("\nCategories to search:")
        print("1. All categories (default)")
        print("2. Tourist attractions only")
        print("3. Restaurants & food only")
        print("4. Shopping only")
        print("5. Entertainment only")
        
        category_choice = input("Choose categories (1-5, default 1): ").strip()
        category_map = {
            "1": None,  # All categories
            "2": ["tourist_attractions"],
            "3": ["restaurants"],
            "4": ["shopping"],
            "5": ["entertainment"]
        }
        categories = category_map.get(category_choice, None)
        
        try:
            # Find hotspots
            result = finder.find_hotspots_by_id(identifier, id_type, radius_km, categories)
            
            if result:
                print(f"\n✅ Successfully found hotspots!")
                print(f"📂 Data saved to: {result['saved_file']}")
            else:
                print(f"\n❌ Could not find hotspots for the given ID")
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Search interrupted by user.")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
        
        # Ask if user wants to continue
        if input("\n🔄 Search for another location? (y/n): ").strip().lower().startswith('n'):
            break
    
    print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()