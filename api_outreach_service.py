from artist_lead_scraper import ArtistLeadScraper
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScrapeRequest(BaseModel):
    keyword: str

@app.get("/")
async def root():
    return {
        "message": "Artist Lead Scraper API v2.0 - YouTube-Only Approach",
        "service": "outreach-agent",
        "status": "running",
        "features": [
            "YouTube producer search",
            "YouTube artist discovery with producer credits",
            "Instagram profile extraction from YouTube channels",
            "Real contact information extraction"
        ],
        "endpoints": {
            "health": "GET /health",
            "scrape": "POST /scrape"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "outreach-agent-v2-youtube-only",
        "scraper_status": "initialized",
        "message": "Artist Lead Scraper API is running with YouTube-only scraping"
    }

@app.post("/scrape")
async def scrape_artist_leads(request: ScrapeRequest):
    print(f"🚀 Starting YouTube-only artist lead scraping for: '{request.keyword}'")
    
    scraper = ArtistLeadScraper()
    all_artists = []
    
    try:
        # Step 1: Find producers for the keyword
        print(f"📺 STEP 1: Finding producers for '{request.keyword}'")
        producers = scraper.search_youtube_producers(request.keyword, num_results=3)
        
        if not producers:
            print("❌ No producers found")
            return {
                "success": False,
                "message": "No producers found for the given keyword",
                "data": []
            }
        
        print(f"✅ STEP 1 COMPLETE: Found {len(producers)} producers")
        
        # Step 2: For each producer, find artists who credit them
        for producer in producers:
            print(f"🎵 STEP 2: Finding artists for producer '{producer}'")
            # Use the new YouTube-only method
            artists = scraper.search_youtube_artists(producer)
            
            for artist in artists:
                artist['producer_used'] = producer
            
            all_artists.extend(artists)
            print(f"   Found {len(artists)} artists for '{producer}'")
        
        # Remove duplicates and limit results
        unique_artists = []
        seen_names = set()
        
        for artist in all_artists:
            if artist['name'] not in seen_names:
                unique_artists.append(artist)
                seen_names.add(artist['name'])
        
        final_artists = unique_artists[:10]  # Limit to top 10
        
        print(f"🎯 FINAL RESULT: {len(final_artists)} unique artist leads found")
        
        return {
            "success": True,
            "message": f"Found {len(final_artists)} artist leads using YouTube-only approach",
            "data": final_artists,
            "producers_searched": producers
        }
        
    except Exception as e:
        print(f"💥 Error during scraping: {str(e)}")
        return {
            "success": False,
            "message": f"Scraping failed: {str(e)}",
            "data": []
        }
    
    finally:
        scraper.close()

if __name__ == "__main__":
    print("🚀 Starting Artist Lead Scraper API v2.0 - YouTube-Only Approach on port 8000")
    print("🌐 Using YouTube-only scraping with Instagram extraction")
    uvicorn.run(app, host="0.0.0.0", port=8000)
