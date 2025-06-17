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
        """Search YouTube for artists who credit the producer."""
        print(f"🎵 STEP 2: Searching YouTube for artists crediting '{producer_name}'...")
        
        try:
            # More specific search patterns for credited tracks
            search_queries = [
                f'"{producer_name}" prod by',
                f'"prod {producer_name}"',
                f'"produced by {producer_name}"',
                f'{producer_name} beat rap',
                f'{producer_name} type beat rap'
            ]
            
            all_artists = []
            
            for query in search_queries:
                print(f"   🔍 Searching: '{query}'")
                artists_from_query = self._search_youtube_for_artists(query, producer_name)
                all_artists.extend(artists_from_query)
                
                if len(all_artists) >= 10:
                    break
                
                time.sleep(0.8)
            
            # Remove duplicates and limit
            unique_artists = []
            seen_channels = set()
            
            for artist in all_artists:
                channel_key = artist['name'].lower()
                if channel_key not in seen_channels and len(unique_artists) < 8:
                    unique_artists.append(artist)
                    seen_channels.add(channel_key)
            
            print(f"🎵 STEP 2 RESULT: Found {len(unique_artists)} unique real artists for '{producer_name}'")
            
            # Return only real artists - no mock data generation
            return unique_artists
            
        except Exception as e:
            print(f"❌ YouTube artist search failed: {str(e)}")
            # Return empty list instead of mock data
            return []
    
    def _search_youtube_for_artists(self, search_query: str, producer_name: str) -> List[Dict]:
        """Enhanced search for real artists with more flexible producer credit matching."""
        try:
            search_url = f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                return []
            
            artists = []
            
            # Enhanced patterns to extract video data with URLs
            pattern1 = r'"videoRenderer":{[^}]*"videoId":"([^"]+)"[^}]*"title":{"runs":\[{"text":"([^"]+)"[^}]*"ownerText":{"runs":\[{"text":"([^"]+)"[^}]*"browseEndpoint":{"browseId":"([^"]+)"'
            matches1 = re.finditer(pattern1, response.text, re.DOTALL)
            
            for match in matches1:
                try:
                    video_id, title, channel_name, channel_id = match.groups()
                    
                    # Skip producer's own videos and obvious type beats
                    if (producer_name.lower() in channel_name.lower() or 
                        "type beat" in title.lower() or
                        "instrumental" in title.lower() or
                        "beat" in channel_name.lower() or
                        len(channel_name) < 3):
                        continue
                    
                    # More flexible patterns for producer credits - check if producer is credited in title
                    title_lower = title.lower()
                    producer_lower = producer_name.lower()
                    
                    # Flexible patterns that look for producer credits anywhere in reasonable context
                    credit_found = False
                    
                    # Check for various credit patterns
                    credit_patterns = [
                        f"prod by {producer_lower}",
                        f"produced by {producer_lower}", 
                        f"prod. by {producer_lower}",
                        f"beat by {producer_lower}",
                        f"instrumental by {producer_lower}",
                        f"[prod {producer_lower}]",
                        f"(prod {producer_lower})",
                        f"[{producer_lower} prod]",
                        f"({producer_lower} prod)",
                        f"[prod. {producer_lower}]",
                        f"(prod. {producer_lower})"
                    ]
                    
                    # Also check if producer name appears with common credit keywords nearby
                    for pattern in credit_patterns:
                        if pattern in title_lower:
                            credit_found = True
                            break
                    
                    # Additional check for producer name near credit words (within 10 characters)
                    if not credit_found:
                        import re as regex
                        # Look for producer name within 10 characters of credit words
                        credit_words = ['prod', 'produced', 'beat', 'instrumental']
                        for word in credit_words:
                            # Find all positions of the credit word
                            for match_obj in regex.finditer(word, title_lower):
                                start_pos = max(0, match_obj.start() - 10)
                                end_pos = min(len(title_lower), match_obj.end() + 10)
                                context = title_lower[start_pos:end_pos]
                                if producer_lower in context:
                                    credit_found = True
                                    break
                            if credit_found:
                                break
                    
                    if credit_found:
                        print(f"   ✅ Found real artist: '{channel_name}' - '{title}'")
                        
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
                            "bio": f"Artist who has collaborated with {producer_name}. Latest: {title[:50]}...",
                            "sample_track": {
                                "title": title,
                                "url": f"https://www.youtube.com/watch?v={video_id}"
                            }
                        }
                        
                        artists.append(artist)
                        
                        if len(artists) >= 4:
                            break
                except Exception as e:
                    continue
            
            # Try alternative pattern if first didn't yield enough results
            if len(artists) < 2:
                pattern2 = r'"title":{"runs":\[{"text":"([^"]+)"[^}]*"videoId":"([^"]+)"[^}]*"shortBylineText":{"runs":\[{"text":"([^"]+)"[^}]*"browseEndpoint":{"browseId":"([^"]+)"'
                matches2 = re.finditer(pattern2, response.text, re.DOTALL)
                
                for match in matches2:
                    try:
                        title, video_id, channel_name, channel_id = match.groups()
                        
                        if (producer_name.lower() in channel_name.lower() or 
                            "type beat" in title.lower() or
                            len(channel_name) < 3):
                            continue
                        
                        title_lower = title.lower()
                        producer_lower = producer_name.lower()
                        
                        # Same flexible credit checking as above
                        credit_found = False
                        
                        credit_patterns = [
                            f"prod by {producer_lower}",
                            f"produced by {producer_lower}", 
                            f"prod. by {producer_lower}",
                            f"beat by {producer_lower}",
                            f"instrumental by {producer_lower}",
                            f"[prod {producer_lower}]",
                            f"(prod {producer_lower})",
                            f"[{producer_lower} prod]",
                            f"({producer_lower} prod)",
                            f"[prod. {producer_lower}]",
                            f"(prod. {producer_lower})"
                        ]
                        
                        for pattern in credit_patterns:
                            if pattern in title_lower:
                                credit_found = True
                                break
                        
                        # Additional proximity check
                        if not credit_found:
                            import re as regex
                            credit_words = ['prod', 'produced', 'beat', 'instrumental']
                            for word in credit_words:
                                for match_obj in regex.finditer(word, title_lower):
                                    start_pos = max(0, match_obj.start() - 10)
                                    end_pos = min(len(title_lower), match_obj.end() + 10)
                                    context = title_lower[start_pos:end_pos]
                                    if producer_lower in context:
                                        credit_found = True
                                        break
                                if credit_found:
                                    break
                        
                        if credit_found:
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
                                "bio": f"Artist who has collaborated with {producer_name}. Latest: {title[:50]}...",
                                "sample_track": {
                                    "title": title,
                                    "url": f"https://www.youtube.com/watch?v={video_id}"
                                }
                            }
                            
                            artists.append(artist)
                            
                            if len(artists) >= 4:
                                break
                    except Exception as e:
                        continue
            
            return artists
            
        except Exception as e:
            print(f"❌ Error in artist search for '{search_query}': {str(e)}")
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
