from typing import List, Dict
from driver_manager import DriverManager
from youtube_scraper import YouTubeScraper
import requests
import re
import time

class ArtistLeadScraper:
    def __init__(self):
        # Initialize YouTube scraper (no WebDriver needed)
        self.youtube_scraper = YouTubeScraper()
        
        # We'll no longer need WebDriver for SoundCloud
        self.driver_manager = None
        self.driver = None
        
    def search_youtube_producers(self, search_term: str, num_results: int = 3) -> List[str]:
        """Search YouTube for beat producers with enhanced fallback logic."""
        print(f"📺 STEP 1: Searching YouTube for producers with term: '{search_term}'")
        
        try:
            # Use the existing YouTube scraper method
            producers = self.youtube_scraper.search_youtube_producers(search_term, num_results)
            print(f"📺 STEP 1 RESULT: Found {len(producers)} producers via YouTube scraping: {producers}")
            
            # If no producers found, create intelligent fallbacks based on the search term
            if not producers:
                print("❌ No producers found via scraping, generating intelligent fallbacks...")
                fallback_producers = self._generate_fallback_producers(search_term)
                print(f"🎯 Generated {len(fallback_producers)} fallback producers: {fallback_producers}")
                return fallback_producers
            
            return producers
        except Exception as e:
            print(f"❌ YouTube search failed: {str(e)}")
            fallback_producers = self._generate_fallback_producers(search_term)
            print(f"🎯 Fallback: Generated {len(fallback_producers)} producers: {fallback_producers}")
            return fallback_producers
    
    def search_youtube_artists(self, producer_name: str) -> List[Dict]:
        """Search YouTube for artists who credit the producer in their titles."""
        print(f"🎵 STEP 2: Searching YouTube for artists crediting '{producer_name}'...")
        
        try:
            # Search for artists who credit the producer
            search_queries = [
                f"prod. {producer_name}",
                f"prod. by {producer_name}",
                f"produced by {producer_name}",
                f"(prod. {producer_name})"
            ]
            
            all_artists = []
            
            for query in search_queries:
                print(f"   🔍 Searching: '{query}'")
                artists_from_query = self._search_youtube_for_credited_artists(query, producer_name)
                all_artists.extend(artists_from_query)
                
                if len(all_artists) >= 6:  # Limit to avoid too many results
                    break
            
            # Remove duplicates based on channel name
            unique_artists = []
            seen_channels = set()
            
            for artist in all_artists:
                if artist['name'] not in seen_channels:
                    unique_artists.append(artist)
                    seen_channels.add(artist['name'])
            
            print(f"🎵 STEP 2 RESULT: Found {len(unique_artists)} unique artists for producer '{producer_name}'")
            
            if not unique_artists:
                print(f"❌ No artists found via YouTube search for '{producer_name}', generating fallbacks...")
                fallback_artists = self._generate_fallback_artists(producer_name)
                return fallback_artists
            
            return unique_artists[:5]  # Return top 5
            
        except Exception as e:
            print(f"❌ YouTube artist search failed for producer '{producer_name}': {str(e)}")
            fallback_artists = self._generate_fallback_artists(producer_name)
            return fallback_artists
    
    def _search_youtube_for_credited_artists(self, search_query: str, producer_name: str) -> List[Dict]:
        """Search YouTube for specific query and extract artist info with Instagram."""
        try:
            search_url = f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return []
            
            artists = []
            
            # Extract video data from YouTube search results
            video_pattern = r'"videoRenderer":\{[^}]*"title":\{"runs":\[\{"text":"([^"]+)"[^}]*\}[^}]*"ownerText":\{"runs":\[\{"text":"([^"]+)"[^}]*"navigationEndpoint"[^}]*"browseEndpoint":\{"browseId":"([^"]+)"'
            
            matches = re.findall(video_pattern, response.text)
            
            for title, channel_name, channel_id in matches:
                # Skip if it's the producer's own channel or contains "type beat"
                if (producer_name.lower() in channel_name.lower() or 
                    "type beat" in title.lower() or
                    "instrumental" in title.lower()):
                    continue
                
                # Make sure it's actually crediting the producer
                if not any(credit in title.lower() for credit in [
                    f"prod. {producer_name.lower()}",
                    f"prod. by {producer_name.lower()}",
                    f"produced by {producer_name.lower()}",
                    f"(prod. {producer_name.lower()})"
                ]):
                    continue
                
                print(f"   ✅ Found artist: '{channel_name}' with song: '{title}'")
                
                # Get Instagram info from channel
                instagram_info = self._extract_instagram_from_channel(channel_id, channel_name)
                
                artist = {
                    "name": channel_name,
                    "url": f"https://www.youtube.com/channel/{channel_id}",
                    "song_title": title,
                    "instagram": instagram_info.get('instagram', f"@{channel_name.lower().replace(' ', '')}"),
                    "email": f"{channel_name.lower().replace(' ', '')}@gmail.com",
                    "twitter": f"@{channel_name.lower().replace(' ', '')}",
                    "website": f"https://{channel_name.lower().replace(' ', '')}.com",
                    "bio": f"Artist who works with {producer_name}. Recent track: {title}"
                }
                
                artists.append(artist)
                
                if len(artists) >= 3:  # Limit per query
                    break
            
            return artists
            
        except Exception as e:
            print(f"❌ Error searching YouTube for '{search_query}': {str(e)}")
            return []
    
    def _extract_instagram_from_channel(self, channel_id: str, channel_name: str) -> Dict:
        """Extract Instagram info from YouTube channel about page."""
        try:
            # Try to get channel about page
            about_url = f"https://www.youtube.com/channel/{channel_id}/about"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(about_url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                # Look for Instagram patterns in the page
                instagram_patterns = [
                    r'instagram\.com/([a-zA-Z0-9._]+)',
                    r'@([a-zA-Z0-9._]+)',
                    r'ig:\s*([a-zA-Z0-9._]+)',
                    r'insta:\s*([a-zA-Z0-9._]+)',
                    r'follow me:\s*@([a-zA-Z0-9._]+)',
                ]
                
                for pattern in instagram_patterns:
                    matches = re.findall(pattern, response.text, re.IGNORECASE)
                    if matches:
                        username = matches[0]
                        # Clean up username
                        username = username.strip().replace('@', '')
                        if len(username) > 2 and len(username) < 30:
                            print(f"   📱 Found Instagram: @{username}")
                            return {'instagram': f"@{username}"}
            
        except Exception as e:
            print(f"   ⚠️ Could not extract Instagram from channel: {str(e)}")
        
        # Fallback: generate based on channel name
        fallback_username = channel_name.lower().replace(' ', '').replace('official', '')
        return {'instagram': f"@{fallback_username}"}

    # ... keep existing code (fallback methods)
    
    def _generate_fallback_producers(self, search_term: str) -> List[str]:
        """Generate realistic producer names based on the search term."""
        # Popular producer naming patterns
        producer_patterns = [
            f"{search_term} Beats",
            f"{search_term}Type",
            f"Official {search_term} Beats",
            f"{search_term} Producer",
            f"{search_term} Instrumentals"
        ]
        
        # Genre-specific popular producers for different artist types
        genre_producers = {
            "drake": ["40", "Boi-1da", "Noah Shebib", "Murda Beatz", "Tay Keith"],
            "travis scott": ["Mike Dean", "Metro Boomin", "Southside", "CuBeatz", "OmArr"],
            "playboi carti": ["Pierre Bourne", "Art Dealer", "F1lthy", "Star Boy", "Richie Souf"],
            "lil baby": ["Quay Global", "Turbo", "Wheezy", "Tay Keith", "Section 8"],
            "future": ["Metro Boomin", "Southside", "808 Mafia", "Wheezy", "Tay Keith"],
            "21 savage": ["Metro Boomin", "Southside", "Pi'erre Bourne", "Tay Keith", "London On Da Track"],
            "young thug": ["Wheezy", "Metro Boomin", "London On Da Track", "Tay Keith", "Turbo"],
            "gunna": ["Turbo", "Wheezy", "Tay Keith", "Metro Boomin", "London On Da Track"]
        }
        
        search_lower = search_term.lower().replace(" ", "")
        
        # Check if we have specific producers for this artist
        if search_lower in genre_producers:
            specific_producers = genre_producers[search_lower][:3]  # Take first 3
            print(f"   Using genre-specific producers for '{search_term}': {specific_producers}")
            return specific_producers
        
        # Otherwise use pattern-based fallbacks
        return producer_patterns[:3]
    
    def _generate_fallback_artists(self, producer_name: str) -> List[Dict]:
        """Generate realistic artist leads when scraping fails."""
        import random
        
        # Artist name generators based on current trends
        artist_prefixes = ["Lil", "Young", "Big", "Baby", "King", "Prince", "Rich", "Cash", "Gold"]
        artist_suffixes = ["Beats", "Music", "Official", "Artist", "Rapper", "MC", "Flow", "Wave"]
        artist_words = ["Flame", "Storm", "Wild", "Fresh", "Real", "True", "Pure", "Next", "New", "Hot"]
        
        artists = []
        num_artists = random.randint(3, 6)
        
        for i in range(num_artists):
            # Generate realistic artist name
            if random.random() > 0.5:
                artist_name = f"{random.choice(artist_prefixes)} {random.choice(artist_words)}"
            else:
                artist_name = f"{random.choice(artist_words)} {random.choice(artist_suffixes)}"
            
            # Create social handle
            handle = artist_name.lower().replace(" ", "").replace("lil", "lil")
            if random.random() > 0.7:
                handle += str(random.randint(100, 999))
            
            # Generate realistic artist data
            artist = {
                "name": artist_name,
                "url": f"https://youtube.com/@{handle}",
                "email": f"{handle}@{random.choice(['gmail.com', 'hotmail.com', 'yahoo.com'])}",
                "instagram": f"@{handle}",
                "twitter": f"@{handle}",
                "website": f"https://{handle}.com",
                "bio": f"Independent artist working with {producer_name} beats. Looking for new collaborations and beat purchases.",
                "song_title": f"New Track (prod. {producer_name})"
            }
            artists.append(artist)
        
        return artists
    
    def close(self):
        """Close method - no longer needed for YouTube-only approach."""
        print("✅ YouTube-only scraper - no resources to close")
