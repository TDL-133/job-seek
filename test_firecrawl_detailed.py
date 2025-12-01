"""
Test Firecrawl API with multiple URLs to verify it returns data
"""
import asyncio
import httpx
import os
from dotenv import load_dotenv
import json

load_dotenv()

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

# Test different types of URLs
TEST_URLS = [
    ("Simple website", "https://example.com"),
    ("Indeed job search", "https://www.indeed.com/jobs?q=Product+Manager&l=Paris"),
    ("Glassdoor job search", "https://www.glassdoor.com/Job/jobs.htm?sc.keyword=Product+Manager"),
    ("WTTJ job search", "https://www.welcometothejungle.com/fr/jobs?query=Product+Manager"),
]


async def test_firecrawl_url(name: str, url: str):
    """Test Firecrawl with a specific URL"""
    print(f"\n{'='*60}")
    print(f"🧪 Testing: {name}")
    print(f"URL: {url}")
    print('='*60)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers={
                    "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "url": url,
                    "formats": ["html", "markdown"],  # Try both formats
                }
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check what's in the response
                print(f"\n📦 Response keys: {list(data.keys())}")
                print(f"\n📋 Full response:\n{json.dumps(data, indent=2)[:1000]}...")
                
                # Try to get data from nested structure
                actual_data = data.get("data", {})
                if actual_data:
                    print(f"\n📦 Data keys: {list(actual_data.keys()) if isinstance(actual_data, dict) else 'not a dict'}")
                
                # Check HTML (both at root and in data)
                html = data.get("html") or actual_data.get("html", "")
                print(f"\n📄 HTML length: {len(html) if html else 0} chars")
                if html:
                    print(f"First 300 chars of HTML:\n{html[:300]}")
                else:
                    print("⚠️  No HTML returned")
                
                # Check Markdown
                markdown = data.get("markdown", "")
                print(f"\n📝 Markdown length: {len(markdown)} chars")
                if markdown:
                    print(f"First 300 chars of Markdown:\n{markdown[:300]}")
                else:
                    print("⚠️  No Markdown returned")
                
                # Check metadata
                metadata = data.get("metadata", {})
                if metadata:
                    print(f"\n📊 Metadata:")
                    print(f"  - Title: {metadata.get('title', 'N/A')}")
                    print(f"  - Description: {metadata.get('description', 'N/A')[:100]}")
                
                # Full response structure
                print(f"\n🗂️  Full response structure:")
                for key, value in data.items():
                    if isinstance(value, str):
                        print(f"  - {key}: {len(value)} chars")
                    else:
                        print(f"  - {key}: {type(value).__name__}")
                
                return True
                
            else:
                print(f"❌ Failed with status {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error response: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"Response text: {response.text[:500]}")
                return False
                
    except Exception as e:
        print(f"❌ Exception: {type(e).__name__}: {e}")
        return False


async def main():
    print("="*60)
    print("🔍 FIRECRAWL DETAILED TESTING")
    print("="*60)
    print(f"API Key: {FIRECRAWL_API_KEY[:30]}...")
    
    if not FIRECRAWL_API_KEY:
        print("\n⚠️  FIRECRAWL_API_KEY not found in .env")
        return
    
    results = []
    for name, url in TEST_URLS:
        success = await test_firecrawl_url(name, url)
        results.append((name, success))
        await asyncio.sleep(2)  # Rate limiting
    
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}")
    
    success_count = sum(1 for _, s in results if s)
    print(f"\nSuccess rate: {success_count}/{len(results)}")


if __name__ == "__main__":
    asyncio.run(main())
