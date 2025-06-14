from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import uvicorn
from artist_lead_scraper import ArtistLeadScraper

app = FastAPI(
    title="Artist Lead Scraper API",
    description="Scrape artist leads from YouTube and SoundCloud",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://agent-dashboard-drab.vercel.app", 
        "http://localhost:3000",
        "*"  # Allow all origins for Railway deployment
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScrapeRequest(BaseModel):
    searchTerm: str

class ArtistLead(BaseModel):
    url: str
    name: str
    email: str
    instagram: str
    twitter: str
    youtube: str
    website: str
    bio: str

class ScrapeResponse(BaseModel):
    success: bool
    data: List[ArtistLead]
    count: int

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Artist Lead Scraper API",
        "endpoints": {
            "root": "GET /",
            "health": "GET /health",
            "scrape": "POST /scrape"
        },
        "usage": {
            "scrape": {
                "method": "POST",
                "url": "/scrape",
                "body": {
                    "searchTerm": "string (required)"
                },
                "example": {
                    "searchTerm": "Drake"
                }
            }
        }
    }

@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_leads(request: ScrapeRequest):
    try:
        search_term = request.searchTerm
        
        if not search_term:
            raise HTTPException(status_code=400, detail="Search term is required")

        print(f'\n🚀 STARTING SCRAPE PROCESS FOR: "{search_term}"')
        print("=" * 60)
        
        scraper = ArtistLeadScraper()
        
        try:
            # STEP 1: Get top 5 producers from YouTube
            print(f'🎵 STEP 1: Searching YouTube for "{search_term} Type Beat" producers...')
            producers = scraper.search_youtube_producers(search_term, num_results=5)
            print(f"📺 Found {len(producers)} producers: {producers}")
            
            if not producers:
                print("❌ No producers found on YouTube!")
                return ScrapeResponse(success=True, data=[], count=0)
            
            # STEP 2-3: For each producer, search SoundCloud and scrape artists
            all_artists = []
            for i, producer in enumerate(producers):
                print(f'\n🔍 STEP 2-3: Processing producer {i+1}/{len(producers)}: "{producer}"')
                artists = scraper.search_soundcloud_artists(producer)
                all_artists.extend(artists)
                print(f"Found {len(artists)} artists for producer '{producer}'")
            
            print(f"\n📊 TOTAL ARTISTS FOUND: {len(all_artists)}")
            
            # STEP 4: Filter for artists with Instagram
            leads_with_instagram = []
            for artist in all_artists:
                if (artist and 
                    artist.get('instagram') and 
                    isinstance(artist['instagram'], str) and 
                    artist['instagram'].strip() != '' and 
                    'instagram.com' in artist['instagram'].lower()):
                    leads_with_instagram.append(artist)
                    print(f"✅ FINAL LEAD: {artist.get('name')} - {artist.get('instagram')}")
            
            print(f"\n🎯 FINAL RESULTS: {len(leads_with_instagram)} artists with Instagram")
            print("=" * 60)
            
            return ScrapeResponse(
                success=True,
                data=leads_with_instagram,
                count=len(leads_with_instagram)
            )
            
        finally:
            scraper.close()
            
    except Exception as e:
        print(f"❌ ERROR DURING SCRAPING: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred during scraping")

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "timestamp": "2024-01-01T00:00:00Z",
        "uptime": 0
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)