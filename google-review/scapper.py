from serpapi import GoogleSearch
import json
from datetime import datetime

def fetch_reviews_by_data_id(data_id, language="en", api_key=None):
    """Fetch reviews for a given data_id"""
    params = {
        "engine": "google_maps_reviews",
        "data_id": data_id,
        "hl": language,
        "api_key": api_key
    }
    
    search = GoogleSearch(params)
    results = search.get_dict()
    
    if "reviews" in results:
        return results
    else:
        print("No reviews found or there was an error.")
        return None

def print_formatted_reviews(results):
    """Print reviews in a readable format"""
    if not results or "reviews" not in results:
        print("No reviews data available.")
        return
    
    reviews = results["reviews"]
    place_info = results.get("place_info", {})
    
    print(f"\n===== REVIEWS FOR {place_info.get('name', 'Tea se tandoor')} =====")
    print(f"Address: {place_info.get('address', 'Address not available')}")
    print(f"Found {len(reviews)} reviews.\n")
    
    for i, review in enumerate(reviews, 1):
        print(f"\n===== REVIEW #{i} =====")
        print(f"Rating: {review['rating']} stars")
        print(f"Date: {review['date']}")
        print(f"User: {review['user']['name']}")
        
        print("\nReview:")
        print(f"  {review['snippet']}")
        
        if 'details' in review:
            print("\nDetails:")
            for key, value in review['details'].items():
                print(f"  {key}: {value}")
        
        if 'response' in review:
            print("\nResponse:")
            print(f"  Date: {review['response']['date']}")
            print(f"  {review['response']['snippet']}")
        
        print("\n" + "-" * 50)

def main():
    # Your API key
    API_KEY = "27a0a1f71c847bfb0af9e970b2cfcc77badbb10fe456d4a9ac758d2b6190be19"
    
    # Data ID from the URL for Tea se tandoor
    DATA_ID = "0x3bae193ae55bccef:0x9868969a476d8ec3"
    
    # Get language preference from user (default to English for Indian reviews)
    language = input("Enter language code (e.g., 'en' for English, 'hi' for Hindi, default is 'en'): ") or "en"
    
    print(f"\nFetching reviews for Tea se tandoor...")
    
    # Get reviews using the data_id
    results = fetch_reviews_by_data_id(DATA_ID, language, API_KEY)
    
    if not results:
        print("Could not fetch reviews. Check the data_id or API key.")
        return
    
    # Print formatted reviews
    print_formatted_reviews(results)
    
    # Save full JSON for further processing
    if results and "reviews" in results:
        filename = "tea_se_tandoor_reviews.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"Saved full review data to {filename}")

if __name__ == "__main__":
    main()