
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
import asyncio
from typing import List, Dict
import random

# Import the web scraping components
from artist_lead_scraper import ArtistLeadScraper

app = FastAPI(title="Artist Lead Scraper API", version="2.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class OutreachRequest(BaseModel):
    searchTerm: str

class ArtistLeadAPI:
    def __init__(self):
        self.scraper = None
        
    async def initialize_scraper(self):
        """Initialize the web scraper"""
        if not self.scraper:
            try:
                print("🔧 Initializing web scraper...")
                self.scraper = ArtistLeadScraper()
                print("✅ Web scraper initialized successfully")
                return True
            except Exception as e:
                print(f"❌ Web scraper initialization failed: {str(e)}")
                return False
        return True
        
    async def search_artist_leads(self, search_term: str) -> List[Dict]:
        """Search for artist leads using web scraping"""
        if not self.scraper:
            await self.initialize_scraper()
        
        try:
            print(f"🔍 Searching for producers with term: {search_term}")
            
            # Step 1: Find producers on YouTube
            producers = self.scraper.search_youtube_producers(search_term, num_results=3)
            print(f"✅ Found {len(producers)} producers: {producers}")
            
            # Step 2: Find artists using those producers' beats on SoundCloud
            all_artists = []
            for producer in producers:
                print(f"🎵 Searching SoundCloud for artists using {producer} beats...")
                artists = self.scraper.search_soundcloud_artists(producer)
                all_artists.extend(artists)
                
                # Add delay between searches to be respectful
                await asyncio.sleep(2)
            
            # Remove duplicates and filter valid results
            unique_artists = []
            seen_names = set()
            
            for artist in all_artists:
                if (artist and 
                    artist.get('name') and 
                    artist['name'] not in seen_names and
                    artist.get('instagram')):  # Only include artists with Instagram
                    seen_names.add(artist['name'])
                    unique_artists.append(artist)
                    
                    if len(unique_artists) >= 10:
                        break
            
            print(f"🎯 Found {len(unique_artists)} unique artist leads")
            return unique_artists
            
        except Exception as e:
            print(f"❌ Error in web scraping: {str(e)}")
            raise e
    
    def cleanup(self):
        """Clean up resources"""
        if self.scraper:
            try:
                self.scraper.close()
            except Exception as e:
                print(f"⚠️ Error closing scraper: {str(e)}")

# Initialize the API service
lead_api = ArtistLeadAPI()

@app.on_event("startup")
async def startup_event():
    """Initialize scraper on startup"""
    await lead_api.initialize_scraper()

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    lead_api.cleanup()

@app.get("/")
async def root():
    return {
        "message": "Artist Lead Scraper API v2.0 - Real Web Scraping",
        "service": "outreach-agent",
        "status": "running",
        "features": [
            "YouTube producer search", 
            "SoundCloud artist discovery",
            "Real contact information extraction",
            "Instagram profile filtering"
        ],
        "endpoints": {
            "health": "GET /health",
            "scrape": "POST /scrape"
        }
    }

@app.get("/health")
async def health_check():
    scraper_status = "initialized" if lead_api.scraper else "not initialized"
    
    return {
        "status": "healthy",
        "service": "outreach-agent-v2",
        "scraper_status": scraper_status,
        "message": "Artist Lead Scraper API is running with real web scraping"
    }

@app.post("/scrape")
async def scrape_artist_leads(request: OutreachRequest):
    """Find artist leads using real web scraping"""
    try:
        print(f"🔍 Finding artist leads for: {request.searchTerm}")
        
        # Ensure scraper is initialized
        if not await lead_api.initialize_scraper():
            raise HTTPException(status_code=500, detail="Failed to initialize web scraper")
        
        # Search for artist leads
        artists = await lead_api.search_artist_leads(request.searchTerm)
        
        print(f"🎯 Successfully found {len(artists)} artist leads")
        
        return {
            "success": True,
            "data": artists,
            "count": len(artists),
            "message": f"Found {len(artists)} artist leads using real web scraping",
            "metadata": {
                "search_term": request.searchTerm,
                "method": "web_scraping"
            }
        }
        
    except Exception as e:
        print(f"❌ Error finding leads: {str(e)}")
        return {
            "success": False,
            "data": [],
            "count": 0,
            "message": f"Failed to find artist leads: {str(e)}"
        }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Starting Artist Lead Scraper API v2.0 on port {port}")
    print(f"🌐 Using real web scraping - no mock data")
    
    uvicorn.run(app, host="0.0.0.0", port=port)
