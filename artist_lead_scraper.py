from typing import List, Dict
from driver_manager import DriverManager
from youtube_api_scraper import YouTubeAPIScraper
from soundcloud_scraper import SoundCloudScraper

class ArtistLeadScraper:
    def __init__(self):
        # Initialize YouTube API scraper (no WebDriver needed)
        self.youtube_scraper = YouTubeAPIScraper()
        
        # Delay WebDriver initialization until we actually need it for SoundCloud
        self.driver_manager = None
        self.driver = None
        self.soundcloud_scraper = None
        
    def _initialize_webdriver_if_needed(self):
        """Initialize WebDriver only when needed for SoundCloud scraping."""
        if not self.driver_manager:
            print("🔧 Initializing WebDriver for SoundCloud scraping only...")
            self.driver_manager = DriverManager()
            self.driver = self.driver_manager.get_driver()
            self.soundcloud_scraper = SoundCloudScraper(self.driver)
            self.soundcloud_scraper.set_driver_manager(self.driver_manager)
            print("✅ WebDriver initialized for SoundCloud")
        
    def search_youtube_producers(self, search_term: str, num_results: int = 3) -> List[str]:
        """Search YouTube for beat producers using YouTube API (no WebDriver needed)."""
        print(f"📺 STEP 1: Searching YouTube API for producers with term: '{search_term}'")
        
        try:
            # Use the existing YouTube API scraper method
            producers = self.youtube_scraper.search_youtube_producers(search_term, num_results)
            print(f"📺 STEP 1 RESULT: Found {len(producers)} producers via YouTube API: {producers}")
            return producers
        except Exception as e:
            print(f"❌ YouTube API search failed: {str(e)}")
            print("   This could be due to:")
            print("   - Missing YOUTUBE_API_KEY environment variable")
            print("   - API quota exceeded")
            print("   - Network connectivity issues")
            return []
    
    def search_soundcloud_artists(self, producer_name: str) -> List[Dict]:
        """Search SoundCloud for artists using beats from the producer (WebDriver needed)."""
        print(f"🎵 STEP 2: Searching SoundCloud for artists using '{producer_name}' beats...")
        
        try:
            # Initialize WebDriver only when we need it for SoundCloud
            self._initialize_webdriver_if_needed()
            
            if not self.soundcloud_scraper:
                print("❌ Failed to initialize SoundCloud scraper")
                return []
            
            # Use SoundCloud web scraping
            artists = self.soundcloud_scraper.search_soundcloud_artists(producer_name)
            print(f"🎵 STEP 2 RESULT: Found {len(artists)} artists for producer '{producer_name}'")
            return artists
            
        except Exception as e:
            print(f"❌ SoundCloud search failed for producer '{producer_name}': {str(e)}")
            return []
    
    def close(self):
        """Close the WebDriver only if it was initialized."""
        if self.driver_manager:
            try:
                print("🔒 Closing WebDriver...")
                self.driver_manager.close()
                self.driver_manager = None
                self.driver = None
                self.soundcloud_scraper = None
                print("✅ WebDriver closed successfully")
            except Exception as e:
                print(f"⚠️ Error closing WebDriver: {str(e)}")
