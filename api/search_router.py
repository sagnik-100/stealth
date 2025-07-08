import json
from fastapi import APIRouter, HTTPException
import serpapi
import os
import logging
from dotenv import load_dotenv
from datetime import datetime
import re

load_dotenv()


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

router = APIRouter()


serp_api_key = os.environ.get("SERP_API_KEY")

client = serpapi.Client(api_key=serp_api_key)

@router.get("/search")
def search(q: str, location: str = ""):
    params = {
        "engine": "google_shopping",
        "q": q,
        "gl" : location
    }
    
    try:
        file_path = "google-gl-countries.json"
        with open(file_path, "r") as f:
            countries = json.load(f)
            for country in countries:
                if country["country_name"].lower() == location.lower():
                    params["gl"] = country["country_code"]
                    break
            if location == "":
                raise HTTPException(status_code=400, detail="Please provide a valid location")

        result = client.search(params=params)
        shopping_results = result.get("shopping_results", [])
        
        processed_results = []
        for item in shopping_results:
            price_string = item.get("price", "")
            match = re.match(r'^([^\d]+)', price_string)
            currency = match.group(1) if match else ""
            processed_results.append({
                # Essential product info
                "title": item.get("title"),
                "price": item.get("extracted_price"),
                "price_string": price_string,  # Original price string with currency
                "product_link": item.get("product_link"),
                "currency" : currency , 
                
                # Rating and reviews
                "rating": item.get("rating"),
                "reviews": item.get("reviews"),
                "snippet": item.get("snippet"),  # e.g., "Quality camera (962 user reviews)"
                
                # Seller information
                "source": item.get("source"),  # e.g., "eBay - wirelesssdepot"
                "source_icon": item.get("source_icon"),
                
                # Product images
                "thumbnail": item.get("thumbnail"),
                "thumbnails": item.get("thumbnails", []),
                
                # Additional useful info
                "delivery": item.get("delivery"),  # e.g., "Free delivery"
                "second_hand_condition": item.get("second_hand_condition"),  # e.g., "pre-owned"
                "position": item.get("position"),  # Search result position
                
                # Product ID for potential future use
                "product_id": item.get("product_id"),
            })
        
        # Filter out results without a price for sorting
        processed_results = [res for res in processed_results if res.get("price") is not None]
        
        # Sort by price in ascending order
        sorted_results = sorted(processed_results, key=lambda x: x["price"])
        
        logger.info("Sorted results:")
        logger.info(sorted_results)
        return sorted_results[:20]
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while fetching search results.")