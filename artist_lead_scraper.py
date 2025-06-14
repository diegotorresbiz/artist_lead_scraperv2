
from typing import List, Dict
from driver_manager import DriverManager
from youtube_scraper import YouTubeScraper
from soundcloud_scraper import SoundCloudScraper

class ArtistLeadScraper:
    def __init__(self):
        self.driver_manager = DriverManager()
        self.driver = self.driver_manager.get_driver()
        self.youtube_scraper = YouTubeScraper()
        self.soundcloud_scraper = SoundCloudScraper(self.driver)
        
    def search_youtube_producers(self, search_term: str, num_results: int = 3) -> List[str]:
        """Search YouTube for beat producers and extract their names from channel names."""
        return self.youtube_scraper.search_youtube_producers(search_term, num_results)
    
    def search_soundcloud_artists(self, producer_name: str) -> List[Dict]:
        """Search SoundCloud for artists using beats from the producer."""
        return self.soundcloud_scraper.search_soundcloud_artists(producer_name)
    
    def close(self):
        """Close the WebDriver."""
        self.driver_manager.close()
