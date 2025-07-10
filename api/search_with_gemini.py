import re
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
import os
import logging
from dotenv import load_dotenv
from google import genai
from google.genai import types
from collections import defaultdict

load_dotenv()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

router = APIRouter()

grounding_tool = types.Tool(
    google_search=types.GoogleSearch()
)

config = types.GenerateContentConfig(
    tools=[grounding_tool]
)


def parse_full_response(response):
    try:
        text = response.candidates[0].content.parts[0].text
        
        result = {
            "price_comparison": [],
            "price_trend_analysis": "",
            "shopping_timing_advice": "",
            "comprehensive_summary": ""
        }
        
        # Extract grounding metadata
        grounding_metadata = response.candidates[0].grounding_metadata
        grounding_chunks = grounding_metadata.grounding_chunks
        grounding_supports = grounding_metadata.grounding_supports
        
        # Create multiple mappings for better URL matching
        segment_to_url = {}
        retailer_to_url = {}
        
        # Process grounding supports
        for support in grounding_supports:
            segment_text = support.segment.text.strip()
            if support.grounding_chunk_indices:
                first_index = support.grounding_chunk_indices[0]
                if first_index < len(grounding_chunks):
                    uri = grounding_chunks[first_index].web.uri
                    title = grounding_chunks[first_index].web.title
                    
                    # Map segment text to URL
                    segment_to_url[segment_text] = uri
                    
                    # Extract retailer name from title and map to URL
                    if title:
                        # Clean up title (remove .com, .de, etc.)
                        clean_title = re.sub(r'\.(com|de|in|co\.uk|fr|it)$', '', title.lower())
                        retailer_to_url[clean_title] = uri
        
        # Create a comprehensive URL mapping from all grounding chunks
        all_urls = {}
        title_variations = {}
        
        for i, chunk in enumerate(grounding_chunks):
            if chunk.web and chunk.web.title:
                original_title = chunk.web.title
                title_lower = original_title.lower()
                
                # Remove common domain extensions
                clean_title = re.sub(r'\.(com|de|in|co\.uk|fr|it|org|net)$', '', title_lower)
                
                # Store multiple variations of the title
                variations = [
                    original_title,
                    title_lower,
                    clean_title,
                    # Extract main domain name (everything before first dot)
                    clean_title.split('.')[0] if '.' in clean_title else clean_title
                ]
                
                # Add all variations to mapping
                for variation in variations:
                    if variation and variation.strip():
                        all_urls[variation.strip()] = chunk.web.uri
                        title_variations[variation.strip()] = original_title
        
        # More flexible price pattern
        price_pattern = r'\*\s*\*{2}([^*]+)\*{2}:\s*(.+?)\s*-\s*([^\n]+)'
        
        # Extract Price Comparison
        for line in text.split('\n'):
            line = line.strip()
            # More flexible check for retailer pattern
            if line.startswith('*') and '**' in line and ':' in line and '-' in line:
                match = re.search(price_pattern, line)
                if match:
                    retailer = match.group(1).strip()
                    product = match.group(2).strip()
                    price = match.group(3).strip()
                    
                    # Try multiple strategies to find the URL
                    url = "URL not found"
                    
                    # Strategy 1: Direct segment match
                    if line in segment_to_url:
                        url = segment_to_url[line]
                    
                    # Strategy 2: Check if any segment contains this line or vice versa
                    if url == "URL not found":
                        for segment_text, segment_url in segment_to_url.items():
                            if line in segment_text or segment_text in line:
                                url = segment_url
                                break
                    
                    # Strategy 3: Match by retailer name using fuzzy matching
                    if url == "URL not found":
                        retailer_lower = retailer.lower().strip()
                        retailer_clean = re.sub(r'\.(com|de|in|co\.uk|fr|it|org|net)$', '', retailer_lower)
                        
                        # Try exact matches first
                        for stored_name in all_urls.keys():
                            if retailer_clean == stored_name or retailer_lower == stored_name:
                                url = all_urls[stored_name]
                                break
                        
                        # If no exact match, try partial matches
                        if url == "URL not found":
                            best_match = None
                            best_score = 0
                            
                            for stored_name in all_urls.keys():
                                # Calculate similarity score
                                score = 0
                                
                                # Check if retailer name contains stored name or vice versa
                                if len(stored_name) > 2:  # Avoid matching very short names
                                    if stored_name in retailer_clean:
                                        score = len(stored_name) / len(retailer_clean)
                                    elif retailer_clean in stored_name:
                                        score = len(retailer_clean) / len(stored_name)
                                
                                # Check for word overlap
                                retailer_words = set(retailer_clean.split())
                                stored_words = set(stored_name.split())
                                common_words = retailer_words.intersection(stored_words)
                                
                                if common_words:
                                    word_score = len(common_words) / max(len(retailer_words), len(stored_words))
                                    score = max(score, word_score)
                                
                                # Use best match if score is high enough
                                if score > best_score and score > 0.6:  # Threshold for similarity
                                    best_score = score
                                    best_match = stored_name
                            
                            if best_match:
                                url = all_urls[best_match]
                    
                    # Strategy 4: Extract price and product info to match with segments
                    if url == "URL not found":
                        # Look for segments that contain the price or product name
                        for segment_text, segment_url in segment_to_url.items():
                            # Check if price appears in segment
                            if price.replace('€', '').replace('₹', '').replace('$', '').strip() in segment_text:
                                url = segment_url
                                break
                            # Check if key words from product appear in segment
                            product_words = product.split()[:3]  # Take first 3 words
                            if len(product_words) > 0 and any(word.lower() in segment_text.lower() for word in product_words if len(word) > 3):
                                url = segment_url
                                break
                    
                    result["price_comparison"].append({
                        "retailer": retailer,
                        "product": product,
                        "price": price,
                        "source_url": url
                    })
        print("before sorting", result["price_comparison"])
        result["price_comparison"] = sorted(result["price_comparison"], key=lambda x: x["price"])
        print("after sorting", result["price_comparison"])
        
        # Extract other sections
        sections = defaultdict(str)
        current_section = None
        section_headers = {
            "Price Trend Analysis": "price_trend_analysis",
            "Shopping Timing Advice": "shopping_timing_advice",
            "Comprehensive Summary": "comprehensive_summary"
        }
        
        for line in text.split('\n'):
            line = line.strip()
            
            # Detect section headers
            if line.startswith('### '):
                header = line[4:].strip()
                if header in section_headers:
                    current_section = section_headers[header]
                else:
                    current_section = None
                continue
                
            # Accumulate section content
            if current_section:
                sections[current_section] += line + "\n"
        
        # Add section text to result
        for section_key, section_text in sections.items():
            result[section_key] = section_text.strip()
        
        # Debug logging
        logger.info(f"Found {len(result['price_comparison'])} price entries")
        logger.info(f"Available URLs: {list(all_urls.keys())}")
        for entry in result['price_comparison']:
            logger.info(f"Retailer: {entry['retailer']} -> URL: {'Found' if entry['source_url'] != 'URL not found' else 'Not Found'}")
            logger.info(f"Price: {entry['price']}")
        return result
        
    except Exception as e:
        logger.error(f"Error parsing response: {str(e)}")
        return {
            "price_comparison": [],
            "price_trend_analysis": "",
            "shopping_timing_advice": "",
            "comprehensive_summary": "",
            "error": str(e)
        }
        
@router.get("/search_with_gemini")
async def search_with_gemini(q: str, location: str = ""):
    logger.info(f"Received Gemini search - Query: '{q}' | Location: '{location}'")
    
    try:
        # Load prompt template
        with open("prompts/gemini_search_prompt.txt", "r") as f:
            prompt = f.read().format(q=q, location=location)
        
        # Send prompt to Gemini
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=config
        )
        logger.info("Response received")
        logger.info(response)
        price_data = parse_full_response(response)
        return price_data
        
        
    except Exception as e:
        logger.error(f"Error generating price analysis: {e}")
        return {"error": "Failed to generate price analysis."}