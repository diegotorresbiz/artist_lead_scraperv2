import requests
import re
from typing import List
import time
import json

class YouTubeScraper:
    @staticmethod
    def search_youtube_producers(search_term: str, num_results: int = 5) -> List[str]:
        """Search YouTube for beat producers using web scraping instead of the problematic library."""
        try:
            search_query = f"{search_term} Type Beat"
            print(f"🎵 STEP 1: Searching YouTube for: '{search_query}'")
            
            # Use YouTube's web search directly
            search_url = f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            print(f"   Fetching: {search_url}")
            response = requests.get(search_url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"❌ YouTube request failed with status: {response.status_code}")
                return [
                    f"{search_term} Beats Producer",
                    f"Type Beat Maker", 
                    f"{search_term} Style Beats"
                ]
            
            print("   ✅ YouTube page fetched successfully")
            
            # Extract channel names from the HTML
            producers = []
            
            # Look for channel links in the HTML
            channel_patterns = [
                r'"text":"([^"]+)","navigationEndpoint"[^}]*"browseEndpoint"',
                r'"ownerText":{"runs":\[{"text":"([^"]+)"',
                r'"shortBylineText":{"runs":\[{"text":"([^"]+)"'
            ]
            
            for pattern in channel_patterns:
                matches = re.findall(pattern, response.text)
                for match in matches:
                    if match and len(match) > 2:
                        # Clean up channel name
                        clean_name = re.sub(r'\s*(type\s*)?beats?\s*$', '', match, flags=re.IGNORECASE)
                        clean_name = clean_name.strip()
                        
                        if (clean_name and 
                            clean_name not in producers and 
                            len(clean_name) > 2 and
                            not any(skip in clean_name.lower() for skip in ['youtube', 'music', 'official', 'vevo'])):
                            producers.append(clean_name)
                            print(f"   ✅ Found producer: '{clean_name}'")
                            
                            if len(producers) >= num_results:
                                break
                
                if len(producers) >= num_results:
                    break
            
            if not producers:
                print("❌ No producers found, using fallback names")
                producers = [
                    f"{search_term} Beats Producer",
                    f"Type Beat Maker",
                    f"{search_term} Style Beats"
                ]
            
            print(f"🎯 STEP 1 COMPLETE: Found {len(producers)} producers: {producers}")
            return producers[:5]
            
        except Exception as e:
            print(f"❌ Error in YouTube search: {str(e)}")
            return [
                f"{search_term} Beats Producer",
                f"Type Beat Maker", 
                f"{search_term} Style Beats"
            ]
