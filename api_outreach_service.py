from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
import asyncio
from typing import List, Dict
from contextlib import asynccontextmanager

# Import the web scraping components
from artist_lead_scraper import ArtistLeadScraper

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
            print(f"🔍 Starting search for producers with term: {search_term}")
            
            # Step 1: Find producers on YouTube
            print(f"📺 STEP 1: Searching YouTube for producers...")
            producers = self.scraper.search_youtube_producers(search_term, num_results=3)
            print(f"📺 STEP 1 RESULT: Found {len(producers)} producers: {producers}")
            
            if not producers:
                print("❌ CRITICAL: No producers found on YouTube!")
                print("   This means the YouTube scraping is failing.")
                print("   Possible causes:")
                print("   - YouTube blocked the request")
                print("   - Network connectivity issues")
                print("   - Search query returned no results")
                print("   - YouTube changed their HTML structure")
                return []
            
            # Step 2: Find artists using those producers' beats on SoundCloud
            all_artists = []
            for i, producer in enumerate(producers):
                print(f"🎵 STEP 2.{i+1}: Searching SoundCloud for artists using '{producer}' beats...")
                try:
                    artists = self.scraper.search_soundcloud_artists(producer)
                    print(f"🎵 STEP 2.{i+1} RESULT: Found {len(artists)} artists for producer '{producer}'")
                    
                    if not artists:
                        print(f"   ⚠️ No artists found for producer '{producer}' on SoundCloud")
                        print("   Possible causes:")
                        print("   - SoundCloud blocked the request")
                        print("   - Producer name not found on SoundCloud")
                        print("   - WebDriver crashed during SoundCloud search")
                        print("   - SoundCloud changed their HTML structure")
                    else:
                        # Log first few artists for debugging
                        for j, artist in enumerate(artists[:3]):
                            print(f"   Artist {j+1}: {artist.get('name', 'Unknown')} - Instagram: {artist.get('instagram', 'None')}")
                    
                    all_artists.extend(artists)
                    
                    # Add delay between searches to be respectful
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    print(f"❌ Error searching SoundCloud for producer '{producer}': {str(e)}")
                    print(f"   Exception type: {type(e).__name__}")
                    continue
            
            print(f"🎵 STEP 2 COMPLETE: Total artists found across all producers: {len(all_artists)}")
            
            if not all_artists:
                print("❌ CRITICAL: No artists found on SoundCloud!")
                print("   This means either:")
                print("   1. The SoundCloud scraping is completely failing")
                print("   2. The producer names from YouTube don't exist on SoundCloud")
                print("   3. All SoundCloud searches are being blocked")
                return []
            
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
                    print(f"✅ Added unique artist: {artist['name']} - {artist['instagram']}")
                    
                    if len(unique_artists) >= 10:
                        print(f"🎯 Reached target of 10 unique artists, stopping")
                        break
                else:
                    # Log why artist was filtered out
                    if not artist:
                        print(f"⚠️ Filtered out: None/empty artist object")
                    elif not artist.get('name'):
                        print(f"⚠️ Filtered out: Artist with no name")
                    elif artist['name'] in seen_names:
                        print(f"⚠️ Filtered out: Duplicate artist '{artist['name']}'")
                    elif not artist.get('instagram'):
                        print(f"⚠️ Filtered out: Artist '{artist.get('name', 'Unknown')}' has no Instagram")
            
            print(f"🎯 FINAL RESULT: Found {len(unique_artists)} unique artist leads with Instagram")
            
            if not unique_artists:
                print("❌ FINAL ISSUE: All artists were filtered out!")
                print("   This means artists were found but none had Instagram profiles")
                print("   Consider loosening the Instagram requirement or improving Instagram detection")
            
            return unique_artists
            
        except Exception as e:
            print(f"❌ Error in web scraping process: {str(e)}")
            print(f"❌ Exception type: {type(e).__name__}")
            import traceback
            print(f"❌ Full traceback: {traceback.format_exc()}")
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting up Artist Lead Scraper API...")
    await lead_api.initialize_scraper()
    yield
    # Shutdown
    print("🔒 Shutting down Artist Lead Scraper API...")
    lead_api.cleanup()

app = FastAPI(
    title="Artist Lead Scraper API", 
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        print(f"🔍 API ENDPOINT: Received request to find leads for: '{request.searchTerm}'")
        
        # Ensure scraper is initialized
        if not await lead_api.initialize_scraper():
            print(f"❌ Failed to initialize web scraper")
            raise HTTPException(status_code=500, detail="Failed to initialize web scraper")
        
        print(f"✅ Web scraper confirmed initialized, starting search...")
        
        # Search for artist leads
        artists = await lead_api.search_artist_leads(request.searchTerm)
        
        print(f"🎯 API ENDPOINT: Search completed - found {len(artists)} artist leads")
        
        if len(artists) == 0:
            print("❌ API ENDPOINT: Zero results - check the detailed logs above for the specific failure point")
            error_message = f"No artist leads found for '{request.searchTerm}'. Check server logs for detailed debugging information."
        else:
            error_message = f"Found {len(artists)} artist leads using real web scraping"
        
        return {
            "success": len(artists) > 0,
            "data": artists,
            "count": len(artists),
            "message": error_message,
            "metadata": {
                "search_term": request.searchTerm,
                "method": "web_scraping"
            }
        }
        
    except Exception as e:
        print(f"❌ API ENDPOINT ERROR: {str(e)}")
        print(f"❌ Exception type: {type(e).__name__}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
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
