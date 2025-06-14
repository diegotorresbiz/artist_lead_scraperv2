from bs4 import BeautifulSoup
import time
from typing import List, Dict
from artist_info_extractor import ArtistInfoExtractor

class SoundCloudScraper:
    def __init__(self, driver):
        self.driver = driver
        self.artist_extractor = ArtistInfoExtractor(driver)
    
    def search_soundcloud_artists(self, producer_name: str) -> List[Dict]:
        """Search SoundCloud for artists using beats from the producer."""
        try:
            print(f"\n🔍 STEP 2: Searching SoundCloud for producer: '{producer_name}'")
            
            # More comprehensive search patterns
            search_patterns = [
                f"{producer_name}",  # Direct name search
                f"prod {producer_name}",
                f"prod. {producer_name}",
                f"produced by {producer_name}",
                f"{producer_name} type beat",
                f"{producer_name} beat",
                f"ft {producer_name}",  # Featured producer
                f"x {producer_name}",   # Collaboration format
            ]
            
            all_artist_urls = set()
            
            for pattern_index, search_pattern in enumerate(search_patterns):
                if len(all_artist_urls) >= 20:  # Increased target
                    break
                    
                search_url = f"https://soundcloud.com/search?q={search_pattern.replace(' ', '%20')}"
                
                print(f"   Pattern {pattern_index + 1}/{len(search_patterns)}: '{search_pattern}'")
                
                try:
                    self.driver.get(search_url)
                    time.sleep(2)
                    
                    # Get page source and parse
                    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    
                    # More comprehensive link selectors
                    track_selectors = [
                        'a[href^="/"][title]',  # Original working selector
                        'article a[href^="/"]',  # Article links
                        '.trackItem a[href^="/"]',  # Track items
                        '.soundTitle a[href^="/"]',  # Sound titles
                        '.userItem a[href^="/"]',  # User items
                        'h2 a[href^="/"]',  # Headers
                        '.sc-link-primary[href^="/"]',  # SoundCloud primary links
                    ]
                    
                    pattern_links = []
                    for selector in track_selectors:
                        try:
                            links = soup.select(selector)
                            pattern_links.extend(links)
                        except Exception:
                            continue
                    
                    print(f"   Found {len(pattern_links)} potential links")
                    
                    # Process links to extract artist profiles
                    pattern_artists = 0
                    for link in pattern_links[:30]:  # Process more links per pattern
                        try:
                            href = link.get('href', '')
                            if not href or not href.startswith('/'):
                                continue
                            
                            # More comprehensive system path filtering
                            system_paths = [
                                '/search', '/tracks', '/sets', '/discover', '/you', '/stream', 
                                '/feed', '/upload', '/terms-of-use', '/pages', '/imprint', 
                                '/charts', '/premium', '/pro', '/mobile', '/apps', '/help',
                                '/jobs', '/developers', '/blog', '/creators', '/copyright',
                                '/privacy', '/community-guidelines', '/advertising', '/legal'
                            ]
                            
                            if any(skip in href.lower() for skip in system_paths):
                                continue
                            
                            # Extract artist profile URL - handle both direct profiles and track URLs
                            url_parts = href.strip('/').split('/')
                            if len(url_parts) >= 1:
                                artist_path = url_parts[0]
                                
                                # Validate artist path
                                if (artist_path and 
                                    len(artist_path) > 1 and 
                                    not artist_path.isdigit() and
                                    not any(skip in artist_path.lower() for skip in ['track', 'set', 'playlist', 'likes', 'reposts', 'followers', 'following'])):
                                    
                                    artist_url = f"https://soundcloud.com/{artist_path}"
                                    
                                    if artist_url not in all_artist_urls:
                                        all_artist_urls.add(artist_url)
                                        pattern_artists += 1
                                        print(f"   🎤 Found artist: {artist_url}")
                                        
                                        if len(all_artist_urls) >= 20:
                                            break
                                
                        except Exception:
                            continue
                    
                    print(f"   Added {pattern_artists} new artists from this pattern")
                    
                except Exception as e:
                    print(f"   ❌ Error with pattern '{search_pattern}': {str(e)}")
                    continue
            
            print(f"   🎯 Total unique artists found: {len(all_artist_urls)}")
            
            if not all_artist_urls:
                print(f"   ❌ No valid artist profiles found for producer '{producer_name}'")
                return []
            
            # STEP 3: Scrape each artist's info
            print(f"\n📊 STEP 3: Scraping artist information...")
            
            processed_artists = []
            for i, artist_url in enumerate(list(all_artist_urls)[:15]):  # Process more artists
                try:
                    print(f"   Scraping artist {i+1}/{min(15, len(all_artist_urls))}: {artist_url}")
                    artist_info = self.artist_extractor.scrape_artist_info(artist_url)
                    
                    if artist_info and artist_info.get('name'):
                        processed_artists.append(artist_info)
                        instagram_status = artist_info.get('instagram', 'None')
                        print(f"   ✅ Added: {artist_info.get('name')} - Instagram: {instagram_status}")
                    else:
                        print(f"   ❌ No valid info extracted")
                        
                except Exception as e:
                    print(f"   ❌ Error scraping artist {i+1}: {str(e)}")
                    continue
            
            print(f"🎯 STEP 2-3 COMPLETE: Found {len(processed_artists)} valid artists for producer '{producer_name}'")
            return processed_artists
            
        except Exception as e:
            print(f"❌ Error searching SoundCloud for '{producer_name}': {str(e)}")
            return []