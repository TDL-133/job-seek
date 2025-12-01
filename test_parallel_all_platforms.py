"""
Test Parallel Search on all 3 platforms: Indeed, Glassdoor, WTTJ
"""
import asyncio
import httpx
import json

PARALLEL_API_KEY = "TDevMkqIQNpuo5aTwTn5FAJ9BcKRpSk394Otl5pv"


async def fetch_with_parallel(url: str, platform: str):
    """Fetch URL with Parallel Search MCP"""
    print(f"\n{'='*80}")
    print(f"📡 Testing: {platform}")
    print('='*80)
    print(f"URL: {url}\n")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://search-mcp.parallel.ai/mcp",
                headers={
                    "Authorization": f"Bearer {PARALLEL_API_KEY}",
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                },
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "web_fetch",
                        "arguments": {
                            "urls": [url],
                        }
                    }
                }
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if "result" in data:
                    result = data["result"]
                    is_error = result.get("isError", False)
                    
                    if is_error:
                        print(f"❌ ERROR from MCP")
                        content = result.get("content", [])
                        if content:
                            error_text = content[0].get("text", "Unknown error")
                            print(f"Error: {error_text[:500]}")
                        return None
                    
                    # Extract content
                    content = result.get("content", [])
                    if content and len(content) > 0:
                        text = content[0].get("text", "")
                        
                        print(f"✅ SUCCESS: {len(text):,} characters")
                        
                        # Parse JSON if it's structured
                        try:
                            parsed = json.loads(text)
                            if isinstance(parsed, dict) and "results" in parsed:
                                results = parsed["results"]
                                if results and len(results) > 0:
                                    first_result = results[0]
                                    print(f"\n📊 Extract ID: {parsed.get('extract_id', 'N/A')}")
                                    print(f"📄 Title: {first_result.get('title', 'N/A')[:100]}")
                                    print(f"🔗 URL: {first_result.get('url', 'N/A')[:80]}")
                                    
                                    excerpts = first_result.get("excerpts", [])
                                    if excerpts:
                                        print(f"\n📝 First excerpt (500 chars):")
                                        print(excerpts[0][:500])
                                    
                                    return text
                        except json.JSONDecodeError:
                            print(f"\n⚠️  Not JSON, raw text (first 500 chars):")
                            print(text[:500])
                            return text
                        
                        return text
                    else:
                        print("❌ No content in result")
                        return None
                elif "error" in data:
                    print(f"❌ MCP Error: {data['error']}")
                    return None
                else:
                    print(f"⚠️  Unexpected response format")
                    return None
            else:
                print(f"❌ HTTP Error {response.status_code}")
                print(f"Response: {response.text[:500]}")
                return None
                
    except Exception as e:
        print(f"❌ Exception: {type(e).__name__}: {e}")
        return None


async def main():
    print("="*80)
    print("🧪 PARALLEL SEARCH TEST - ALL PLATFORMS")
    print("="*80)
    print(f"API Key: {PARALLEL_API_KEY[:20]}...\n")
    
    test_urls = [
        ("Indeed France", "https://fr.indeed.com/emplois?q=Product+Manager&l=Bordeaux"),
        ("Glassdoor France", "https://www.glassdoor.fr/Job/bordeaux-product-manager-jobs-SRCH_IL.0,8_IC2490183_KO9,24.htm"),
        ("WTTJ France", "https://www.welcometothejungle.com/fr/jobs?query=Product+Manager&aroundQuery=Bordeaux&refinementList%5Boffices.country_code%5D%5B%5D=FR"),
    ]
    
    results = {}
    
    for platform, url in test_urls:
        content = await fetch_with_parallel(url, platform)
        results[platform] = content
        await asyncio.sleep(2)  # Rate limiting
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 SUMMARY")
    print('='*80)
    
    for platform, content in results.items():
        status = "✅" if content else "❌"
        size = f"{len(content):,} chars" if content else "Failed"
        print(f"{status} {platform:20} {size}")
    
    # Count successes
    successful = sum(1 for c in results.values() if c)
    print(f"\n🎯 {successful}/3 platforms successful")
    print('='*80)


if __name__ == "__main__":
    asyncio.run(main())
