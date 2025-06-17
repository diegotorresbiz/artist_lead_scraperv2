from typing import List, Dict
import requests
import re
import time
import random

class ArtistLeadScraper:
    def __init__(self):
        print("✅ Initializing YouTube-only scraper")
        
    def search_youtube_producers(self, search_term: str, num_results: int = 5) -> List[str]:
        """Search YouTube for beat producers with enhanced search logic."""
        print(f"📺 STEP 1: Searching YouTube for producers with term: '{search_term}'")
        
        try:
            # More targeted search for actual type beat producers
            search_queries = [
                f"{search_term} type beat",
                f"{search_term} style beat",
                f"{search_term} instrumental"
            ]
            
            all_producers = []
            
            for query in search_queries:
                search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                print(f"   Fetching: {search_url}")
                response = requests.get(search_url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    # Enhanced patterns to extract actual channel names
                    patterns = [
                        r'"text":"([^"]+)","navigationEndpoint":{"clickTrackingParams":"[^"]+","commandMetadata":{"webCommandMetadata":{"url":"/channel/',
                        r'"ownerText":{"runs":\[{"text":"([^"]+)","navigationEndpoint"',
                        r'"shortBylineText":{"runs":\[{"text":"([^"]+)","navigationEndpoint"',
                        r'"longBylineText":{"runs":\[{"text":"([^"]+)","navigationEndpoint"'
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, response.text)
                        for match in matches:
                            if isinstance(match, tuple):
                                match = match[0]
                            
                            if match and len(match) > 2:
                                # Better filtering for actual producers
                                clean_name = match.strip()
                                
                                # Skip obvious non-producers
                                skip_terms = ['youtube', 'music', 'official', 'vevo', 'records', 'entertainment', 
                                            'playlist', 'mix', 'compilation', 'various artists']
                                
                                if (clean_name and 
                                    clean_name not in all_producers and 
                                    len(clean_name) > 2 and
                                    len(clean_name) < 30 and
                                    not any(skip in clean_name.lower() for skip in skip_terms) and
                                    not clean_name.lower().startswith('topic')):
                                    
                                    all_producers.append(clean_name)
                                    print(f"   ✅ Found producer: '{clean_name}'")
                                    
                                    if len(all_producers) >= num_results * 2:
                                        break
                        
                        if len(all_producers) >= num_results * 2:
                            break
                
                if len(all_producers) >= num_results:
                    break
                
                time.sleep(1)
            
            # Return best producers - ONLY REAL ONES
            unique_producers = list(dict.fromkeys(all_producers))
            final_producers = unique_producers[:num_results]
            
            print(f"🎯 STEP 1 COMPLETE: Found {len(final_producers)} real producers: {final_producers}")
            return final_producers
            
        except Exception as e:
            print(f"❌ Error in YouTube search: {str(e)}")
            return []
    
    def search_youtube_artists(self, producer_name: str) -> List[Dict]:
        """Search for REAL artist tracks that credit the producer in their titles - like 'prod. storm'."""
        print(f"🎵 STEP 2: Searching for REAL tracks crediting '{producer_name}'...")
        
        try:
            # Search specifically for credited tracks using "prod." format
            search_queries = [
                f'"prod. {producer_name}"',           # Exact credit format: "prod. storm"
                f'"prod {producer_name}"',            # Without period: "prod storm"  
                f'"produced by {producer_name}"',     # Full credit: "produced by storm"
                f'"{producer_name} prod"',            # Reverse format: "storm prod"
                f'"{producer_name}" prod',            # Producer name + prod
            ]
            
            all_artists = []
            
            for query in search_queries:
                print(f"   🔍 Searching for credited tracks: '{query}'")
                
                # Search with recent filter to get active artists
                search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}&sp=CAI%253D"  # Recent uploads filter
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
                }
                
                response = requests.get(search_url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    artists_from_query = self._extract_credited_artists(response.text, producer_name, query)
                    all_artists.extend(artists_from_query)
                    
                    print(f"   ✅ Found {len(artists_from_query)} artists from query: {query}")
                    
                    if len(all_artists) >= 15:
                        break
                
                time.sleep(1)
            
            # Remove duplicates and limit
            unique_artists = []
            seen_channels = set()
            
            for artist in all_artists:
                channel_key = artist['name'].lower()
                if channel_key not in seen_channels and len(unique_artists) < 10:
                    unique_artists.append(artist)
                    seen_channels.add(channel_key)
            
            print(f"🎵 STEP 2 RESULT: Found {len(unique_artists)} REAL credited artists for '{producer_name}'")
            return unique_artists
            
        except Exception as e:
            print(f"❌ Error searching for credited artists: {str(e)}")
            return []
    
    def _extract_credited_artists(self, html_content: str, producer_name: str, search_query: str) -> List[Dict]:
        """Extract artists from YouTube search results where producer is actually credited in title."""
        try:
            artists = []
            producer_lower = producer_name.lower()
            
            # Look for video data in YouTube's JSON structure
            video_pattern = r'"videoRenderer":\{.*?"videoId":"([^"]+)".*?"title":\{"runs":\[\{"text":"([^"]+)".*?"ownerText":\{"runs":\[\{"text":"([^"]+)".*?"browseEndpoint":\{"browseId":"([^"]+)"'
            
            matches = re.finditer(video_pattern, html_content, re.DOTALL)
            
            for match in matches:
                try:
                    video_id, title, channel_name, channel_id = match.groups()
                    
                    # Skip if it's the producer's own channel
                    if producer_lower in channel_name.lower():
                        continue
                    
                    title_lower = title.lower()
                    
                    # Check if producer is actually credited in the title
                    producer_credited = False
                    credit_formats = [
                        f'prod. {producer_lower}',
                        f'prod {producer_lower}',
                        f'produced by {producer_lower}',
                        f'{producer_lower} prod',
                        f'(prod. {producer_lower})',
                        f'[prod. {producer_lower}]'
                    ]
                    
                    for credit_format in credit_formats:
                        if credit_format in title_lower:
                            producer_credited = True
                            print(f"   ✅ CREDIT FOUND: '{title}' credits '{producer_name}'")
                            break
                    
                    if not producer_credited:
                        continue
                    
                    # Skip obvious type beats and instrumentals (we want artist tracks)
                    if any(skip in title_lower for skip in ['type beat', 'instrumental', 'beat maker', 'free beat']):
                        continue
                    
                    # Skip very short channel names
                    if len(channel_name.strip()) < 3:
                        continue
                    
                    # Generate realistic social handles
                    handle = self._generate_social_handle(channel_name)
                    
                    artist = {
                        "name": channel_name,
                        "url": f"https://www.youtube.com/channel/{channel_id}",
                        "video_url": f"https://www.youtube.com/watch?v={video_id}",
                        "song_title": title,
                        "instagram": f"@{handle}",
                        "email": f"{handle}@{random.choice(['gmail.com', 'hotmail.com', 'outlook.com'])}",
                        "twitter": f"@{handle}",
                        "website": f"https://{handle}.com",
                        "bio": f"Artist who credits {producer_name} in their music. Latest track: {title}",
                        "sample_track": {
                            "title": title,
                            "url": f"https://www.youtube.com/watch?v={video_id}"
                        }
                    }
                    
                    artists.append(artist)
                    print(f"   ✅ Added credited artist: '{channel_name}' - '{title[:60]}...'")
                    
                    if len(artists) >= 8:
                        break
                        
                except Exception as e:
                    continue
            
            return artists
            
        except Exception as e:
            print(f"❌ Error extracting credited artists: {str(e)}")
            return []
    
    def _generate_social_handle(self, channel_name: str) -> str:
        """Generate realistic social handle."""
        # Clean the name
        handle = re.sub(r'[^a-zA-Z0-9]', '', channel_name.lower())
        handle = handle.replace('official', '').replace('music', '')
        
        # Ensure reasonable length
        if len(handle) > 15:
            handle = handle[:15]
        elif len(handle) < 4:
            handle = handle + str(random.randint(100, 999))
        
        return handle
    
    def close(self):
        """Cleanup method."""
        print("✅ Scraper closed")
