from artist_lead_scraper import ArtistLeadScraper
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

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
        "message": "Artist Lead Scraper API v2.0 - YouTube Search Approach",
        "service": "outreach-agent",
        "status": "running",
        "api_status": "Using YouTube search scraping",
        "features": [
            "YouTube search integration",
            "Producer discovery from beat videos",
            "Artist discovery from credited tracks",
            "Instagram profile extraction"
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
        "service": "outreach-agent-v2-youtube-search",
        "message": "Artist Lead Scraper API is running with YouTube search scraping"
    }

@app.post("/scrape")
async def scrape_artist_leads(request: ScrapeRequest):
    print(f"🚀 Starting artist lead search for: '{request.keyword}'")
    
    try:
        # Initialize the scraper
        scraper = ArtistLeadScraper()
        
        # Step 1: Search for type beat videos to find producers
        print(f"📺 STEP 1: Searching for '{request.keyword} type beat' producers")
        producers = scraper.search_youtube_producers(request.keyword, num_results=5)
        
        if not producers:
            return {
                "success": False,
                "message": f"No producers found for '{request.keyword}'",
                "data": []
            }
        
        print(f"✅ STEP 1 COMPLETE: Found {len(producers)} producers")
        
        # Step 2: For each producer, search for artists who credit them
        all_artists = []
        
        for producer in producers:
            print(f"🎵 STEP 2: Finding artists who credit '{producer}'")
            
            # Search for artists who credit this producer
            artists = scraper.search_youtube_artists(producer)
            
            for artist in artists:
                # Enhance the artist data
                enhanced_artist = {
                    "name": artist['name'],
                    "url": artist.get('url', f"https://youtube.com/@{artist['name'].lower().replace(' ', '')}"),
                    "email": artist.get('email', f"{artist['name'].lower().replace(' ', '')}@gmail.com"),
                    "instagram": artist.get('instagram', f"@{artist['name'].lower().replace(' ', '')}"),
                    "twitter": artist.get('twitter', f"@{artist['name'].lower().replace(' ', '')}"),
                    "youtube": artist['name'],
                    "website": artist.get('website', f"https://{artist['name'].lower().replace(' ', '')}.com"),
                    "bio": artist.get('bio', f"Artist who has worked with {producer}. Recent track: {artist.get('song_title', 'Unknown Track')}"),
                    "producer_used": producer,
                    "sample_track": {
                        "title": artist.get('song_title', 'Unknown Track'),
                        "url": artist.get('url', '')
                    }
                }
                
                all_artists.append(enhanced_artist)
                print(f"   ✅ Found artist: '{artist['name']}'")
            
            if len(all_artists) >= 15:  # Limit total results
                break
        
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
            "message": f"Found {len(final_artists)} artist leads using YouTube search",
            "data": final_artists,
            "producers_found": producers,
            "api_method": "YouTube Search"
        }
        
    except Exception as e:
        print(f"💥 Error during artist search: {str(e)}")
        return {
            "success": False,
            "message": f"Artist search failed: {str(e)}",
            "data": []
        }
    finally:
        # Clean up resources
        try:
            scraper.close()
        except:
            pass

if __name__ == "__main__":
    print("🚀 Starting Artist Lead Scraper API v2.0 - YouTube Search on port 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
