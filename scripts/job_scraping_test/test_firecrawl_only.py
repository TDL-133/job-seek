import asyncio
import os
import httpx
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path("/Users/lopato/Documents/DAGORSEY/Geek/Job Seek/.env")
load_dotenv(env_path)

async def test_firecrawl_indeed():
    api_key = os.getenv("FIRECRAWL_API_KEY")
    print(f"🔑 Testing Firecrawl with key ending in: ...{api_key[-5:] if api_key else 'NONE'}")
    
    if not api_key:
        print("❌ No API Key found!")
        return

    job_title = "Product Manager"
    city = "Lyon"
    region = "Auvergne-Rhône-Alpes"
    
    # Query format from parallel_scraper.py
    query = f"{job_title} {city} {region} site:fr.indeed.com"
    print(f"🔥 Sending query to Firecrawl: '{query}'")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.firecrawl.dev/v1/search",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "query": query,
                    "limit": 5,
                    "scrapeOptions": {
                        "formats": ["markdown"],
                        "onlyMainContent": True
                    }
                }
            )

            print(f"📡 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("data", [])
                print(f"✅ Success! Found {len(results)} raw results.")
                
                print("\n📋 Results:")
                for i, res in enumerate(results, 1):
                    url = res.get('url', 'No URL')
                    title = res.get('title', 'No Title')
                    print(f"{i}. {title}")
                    print(f"   🔗 {url}")
                    
                    # Simulate filtering logic
                    if city.lower() in url.lower():
                         print("   ✅ Valid Location Match")
                    else:
                         print("   ⚠️  Location Mismatch (would be filtered)")
            else:
                print(f"❌ Error Response: {response.text}")

    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_firecrawl_indeed())