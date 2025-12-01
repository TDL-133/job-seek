"""
Test script to verify Firecrawl and BrightData API keys
"""
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
BRIGHTDATA_API_KEY = os.getenv("BRIGHTDATA_API_KEY")
BRIGHTDATA_MCP_URL = os.getenv("BRIGHTDATA_MCP_URL", "https://mcp.brightdata.com/mcp")

TEST_URL = "https://www.indeed.com/jobs?q=Product+Manager&l=Paris"


async def test_firecrawl():
    """Test Firecrawl API"""
    print("\n🔍 Testing Firecrawl API...")
    print(f"API Key: {FIRECRAWL_API_KEY[:20]}...")
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers={
                    "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "url": TEST_URL,
                    "formats": ["html"],
                }
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                html = data.get("html", "")
                print(f"✅ Success! HTML length: {len(html)} chars")
                print(f"First 200 chars: {html[:200]}")
            else:
                print(f"❌ Failed: {response.status_code}")
                print(f"Response: {response.text[:500]}")
                
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")


async def test_brightdata():
    """Test BrightData MCP API"""
    print("\n🔍 Testing BrightData MCP API...")
    print(f"API Key: {BRIGHTDATA_API_KEY[:20]}...")
    print(f"MCP URL: {BRIGHTDATA_MCP_URL}")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                BRIGHTDATA_MCP_URL,
                params={
                    "token": BRIGHTDATA_API_KEY,
                },
                json={
                    "method": "scrape_as_markdown",
                    "params": {
                        "url": TEST_URL,
                    }
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success! Response type: {type(data)}")
                if isinstance(data, dict):
                    print(f"Keys: {list(data.keys())}")
                    html = data.get("content") or data.get("html") or data.get("result") or response.text
                else:
                    html = response.text
                print(f"HTML length: {len(str(html))} chars")
                print(f"First 200 chars: {str(html)[:200]}")
            else:
                print(f"❌ Failed: {response.status_code}")
                print(f"Response: {response.text[:500]}")
                
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")


async def main():
    print("=" * 60)
    print("🧪 Testing Scraping APIs")
    print("=" * 60)
    
    if FIRECRAWL_API_KEY:
        await test_firecrawl()
    else:
        print("\n⚠️  FIRECRAWL_API_KEY not found in .env")
    
    if BRIGHTDATA_API_KEY:
        await test_brightdata()
    else:
        print("\n⚠️  BRIGHTDATA_API_KEY not found in .env")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
