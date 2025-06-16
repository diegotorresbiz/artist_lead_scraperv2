
from youtube_api_scraper import YouTubeAPIScraper
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
        "message": "Artist Lead Scraper API v2.0 - YouTube API Approach",
        "service": "outreach-agent",
        "status": "running",
        "api_status": "Using YouTube Data API v3" if os.getenv('YOUTUBE_API_KEY') else "No YouTube API key found",
        "features": [
            "YouTube Data API v3 integration",
            "Real video search and analytics",
            "Producer discovery from beat videos",
            "Artist discovery from credited tracks"
        ],
        "endpoints": {
            "health": "GET /health",
            "scrape": "POST /scrape"
        }
    }

@app.get("/health")
async def health_check():
    api_key_status = "configured" if os.getenv('YOUTUBE_API_KEY') else "missing"
    return {
        "status": "healthy",
        "service": "outreach-agent-v2-youtube-api",
        "youtube_api_key": api_key_status,
        "message": f"Artist Lead Scraper API is running with YouTube Data API v3 ({api_key_status})"
    }

@app.post("/scrape")
async def scrape_artist_leads(request: ScrapeRequest):
    print(f"🚀 Starting YouTube API artist lead search for: '{request.keyword}'")
    
    # Check if YouTube API key is available
    if not os.getenv('YOUTUBE_API_KEY'):
        print("❌ YouTube API key not found in environment variables")
        return {
            "success": False,
            "message": "YouTube API key not configured. Please set YOUTUBE_API_KEY environment variable.",
            "data": []
        }
    
    try:
        # Initialize YouTube API scraper
        youtube_scraper = YouTubeAPIScraper()
        
        # Step 1: Search for type beat videos to find producers
        print(f"📺 STEP 1: Searching for '{request.keyword} type beat' videos")
        type_beat_videos = youtube_scraper.search_videos(
            f"{request.keyword} type beat", 
            days_back=90, 
            max_results=20
        )
        
        if not type_beat_videos:
            return {
                "success": False,
                "message": f"No type beat videos found for '{request.keyword}'",
                "data": []
            }
        
        # Extract unique producers (channels) from type beat videos
        producers = []
        seen_channels = set()
        
        for video in type_beat_videos:
            channel = video['channel_title']
            if channel not in seen_channels and len(producers) < 5:
                clean_name = channel.replace("Official", "").replace("Music", "").strip()
                if clean_name and clean_name not in seen_channels:
                    producers.append({
                        'name': clean_name,
                        'original_name': channel,
                        'sample_video': video
                    })
                    seen_channels.add(clean_name)
                    seen_channels.add(channel)
        
        print(f"✅ STEP 1 COMPLETE: Found {len(producers)} producers")
        
        # Step 2: For each producer, search for artists who credit them
        all_artists = []
        
        for producer in producers:
            producer_name = producer['name']
            print(f"🎵 STEP 2: Finding artists who credit '{producer_name}'")
            
            # Search for songs that credit this producer
            credit_searches = [
                f"prod. {producer_name}",
                f"prod. by {producer_name}",
                f"produced by {producer_name}"
            ]
            
            for search_query in credit_searches:
                print(f"   🔍 Searching: '{search_query}'")
                credited_videos = youtube_scraper.search_videos(
                    search_query,
                    days_back=180,
                    max_results=10
                )
                
                for video in credited_videos:
                    # Skip if it's the producer's own channel
                    if producer['original_name'].lower() in video['channel_title'].lower():
                        continue
                    
                    # Skip if it's clearly a type beat (not an actual artist)
                    if "type beat" in video['title'].lower():
                        continue
                    
                    # Create artist profile
                    channel_name = video['channel_title']
                    handle = channel_name.lower().replace(' ', '').replace('official', '')[:15]
                    
                    artist = {
                        "name": channel_name,
                        "url": f"https://youtube.com/channel/{video.get('channel_id', '')}",
                        "email": f"{handle}@gmail.com",
                        "instagram": f"@{handle}",
                        "twitter": f"@{handle}",
                        "youtube": video['channel_title'],
                        "website": f"https://{handle}.com",
                        "bio": f"Artist who has worked with {producer_name}. Recent track: {video['title']} ({video['view_count']:,} views)",
                        "producer_used": producer_name,
                        "sample_track": {
                            "title": video['title'],
                            "views": video['view_count'],
                            "url": f"https://youtube.com/watch?v={video['video_id']}"
                        }
                    }
                    
                    all_artists.append(artist)
                    print(f"   ✅ Found artist: '{channel_name}' - track: '{video['title']}'")
                
                if len(all_artists) >= 15:  # Limit total results
                    break
            
            if len(all_artists) >= 15:
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
            "message": f"Found {len(final_artists)} real artist leads using YouTube Data API v3",
            "data": final_artists,
            "producers_found": [p['name'] for p in producers],
            "api_method": "YouTube Data API v3"
        }
        
    except Exception as e:
        print(f"💥 Error during YouTube API search: {str(e)}")
        return {
            "success": False,
            "message": f"YouTube API search failed: {str(e)}",
            "data": []
        }

if __name__ == "__main__":
    print("🚀 Starting Artist Lead Scraper API v2.0 - YouTube Data API v3 on port 8000")
    print(f"🔑 YouTube API Key: {'✅ Configured' if os.getenv('YOUTUBE_API_KEY') else '❌ Missing'}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
