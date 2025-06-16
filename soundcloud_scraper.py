
from bs4 import BeautifulSoup
import time
from typing import List, Dict
from artist_info_extractor import ArtistInfoExtractor

class SoundCloudScraper:
    def __init__(self, driver):
        self.driver_manager = None  # Will be set from artist_lead_scraper
        self.driver = driver
        self.artist_extractor = ArtistInfoExtractor(driver)
        self.max_retries = 3
    
    def set_driver_manager(self, driver_manager):
        """Set the driver manager for crash recovery."""
        self.driver_manager = driver_manager
        
    def safe_get_page(self, url: str, retry_count: int = 0) -> bool:
        """Safely navigate to a page with crash recovery."""
        try:
            print(f"   🌐 Navigating to: {url}")
            self.driver.get(url)
            time.sleep(2)  # Shorter wait time
            return True
        except Exception as e:
            print(f"   ❌ Error navigating to {url}: {str(e)}")
            
            if "tab crashed" in str(e).lower() or "disconnected" in str(e).lower():
                print(f"   💥 Chrome crashed! Retry {retry_count + 1}/{self.max_retries}")
                
                if retry_count < self.max_retries and self.driver_manager:
                    print("   🔄 Attempting to restart Chrome...")
                    if self.driver_manager.restart_driver_if_crashed():
                        print("   ✅ Chrome restarted, retrying navigation...")
                        # Update driver references
                        self.driver = self.driver_manager.get_driver()
                        self.artist_extractor.driver = self.driver
                        time.sleep(3)  # Give Chrome time to stabilize
                        return self.safe_get_page(url, retry_count + 1)
                    else:
                        print("   ❌ Failed to restart Chrome")
                        return False
                else:
                    print("   ❌ Max retries reached or no driver manager available")
                    return False
            else:
                print(f"   ❌ Non-crash error: {str(e)}")
                return False
    
    def search_soundcloud_artists(self, producer_name: str) -> List[Dict]:
        """Search SoundCloud for artists using beats from the producer with crash protection."""
        try:
            print(f"\n🔍 STEP 2: Searching SoundCloud for producer: '{producer_name}'")
            
            # Reduced search patterns to minimize Chrome load
            search_patterns = [
                f"{producer_name}",  # Direct name search
                f"prod {producer_name}",
                f"prod. {producer_name}",
                f"{producer_name} type beat",
            ]
            
            all_artist_urls = set()
            
            for pattern_index, search_pattern in enumerate(search_patterns):
                if len(all_artist_urls) >= 10:  # Reduced target to minimize load
                    break
                    
                search_url = f"https://soundcloud.com/search?q={search_pattern.replace(' ', '%20')}"
                
                print(f"   Pattern {pattern_index + 1}/{len(search_patterns)}: '{search_pattern}'")
                
                # Use safe navigation with crash recovery
                if not self.safe_get_page(search_url):
                    print(f"   ❌ Failed to load search page for pattern: '{search_pattern}'")
                    continue
                
                try:
                    # Get page source and parse
                    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    
                    # Simplified link selectors to reduce processing load
                    track_selectors = [
                        'a[href^="/"][title]',  # Primary working selector
                        'article a[href^="/"]',  # Article links
                        '.trackItem a[href^="/"]',  # Track items
                    ]
                    
                    pattern_links = []
                    for selector in track_selectors:
                        try:
                            links = soup.select(selector)
                            pattern_links.extend(links)
                        except Exception:
                            continue
                    
                    print(f"   Found {len(pattern_links)} potential links")
                    
                    # Process links to extract artist profiles - reduced processing
                    pattern_artists = 0
                    for link in pattern_links[:15]:  # Process fewer links
                        try:
                            href = link.get('href', '')
                            if not href or not href.startswith('/'):
                                continue
                            
                            # System path filtering
                            system_paths = [
                                '/search', '/tracks', '/sets', '/discover', '/you', '/stream', 
                                '/feed', '/upload', '/terms-of-use', '/pages', '/imprint', 
                                '/charts', '/premium', '/pro', '/mobile', '/apps', '/help'
                            ]
                            
                            if any(skip in href.lower() for skip in system_paths):
                                continue
                            
                            # Extract artist profile URL
                            url_parts = href.strip('/').split('/')
                            if len(url_parts) >= 1:
                                artist_path = url_parts[0]
                                
                                # Validate artist path
                                if (artist_path and 
                                    len(artist_path) > 1 and 
                                    not artist_path.isdigit() and
                                    not any(skip in artist_path.lower() for skip in ['track', 'set', 'playlist', 'likes', 'reposts'])):
                                    
                                    artist_url = f"https://soundcloud.com/{artist_path}"
                                    
                                    if artist_url not in all_artist_urls:
                                        all_artist_urls.add(artist_url)
                                        pattern_artists += 1
                                        print(f"   🎤 Found artist: {artist_url}")
                                        
                                        if len(all_artist_urls) >= 10:
                                            break
                                
                        except Exception:
                            continue
                    
                    print(f"   Added {pattern_artists} new artists from this pattern")
                    
                    # Add delay to prevent overwhelming Chrome
                    time.sleep(3)
                    
                except Exception as e:
                    print(f"   ❌ Error processing search results for '{search_pattern}': {str(e)}")
                    continue
            
            print(f"   🎯 Total unique artists found: {len(all_artist_urls)}")
            
            if not all_artist_urls:
                print(f"   ❌ No valid artist profiles found for producer '{producer_name}'")
                return []
            
            # STEP 3: Scrape each artist's info with crash protection
            print(f"\n📊 STEP 3: Scraping artist information with crash protection...")
            
            processed_artists = []
            for i, artist_url in enumerate(list(all_artist_urls)[:8]):  # Process fewer artists
                try:
                    print(f"   Scraping artist {i+1}/{min(8, len(all_artist_urls))}: {artist_url}")
                    
                    # Use crash-safe artist info extraction
                    artist_info = self.safe_scrape_artist_info(artist_url)
                    
                    if artist_info and artist_info.get('name'):
                        processed_artists.append(artist_info)
                        instagram_status = artist_info.get('instagram', 'None')
                        print(f"   ✅ Added: {artist_info.get('name')} - Instagram: {instagram_status}")
                    else:
                        print(f"   ❌ No valid info extracted")
                        
                except Exception as e:
                    print(f"   ❌ Error scraping artist {i+1}: {str(e)}")
                    continue
                    
                # Add delay between artist scrapes
                time.sleep(2)
            
            print(f"🎯 STEP 2-3 COMPLETE: Found {len(processed_artists)} valid artists for producer '{producer_name}'")
            return processed_artists
            
        except Exception as e:
            print(f"❌ Error searching SoundCloud for '{producer_name}': {str(e)}")
            return []
    
    def safe_scrape_artist_info(self, artist_url: str) -> Dict:
        """Safely scrape artist info with crash recovery."""
        try:
            # Use safe navigation
            if not self.safe_get_page(artist_url):
                print(f"   ❌ Failed to load artist page: {artist_url}")
                return None
            
            # Extract info using the existing artist extractor
            return self.artist_extractor.scrape_artist_info(artist_url)
            
        except Exception as e:
            print(f"   ❌ Error in safe artist info extraction: {str(e)}")
            return None
