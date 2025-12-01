"""
Simple test for Parallel Search API (no dependencies)
"""
import asyncio
import httpx
import json

PARALLEL_API_KEY = "TDevMkqIQNpuo5aTwTn5FAJ9BcKRpSk394Otl5pv"


async def test_parallel_api():
    """Test Parallel Search API directly"""
    
    print("="*80)
    print("🧪 TEST: Parallel Search API")
    print("="*80)
    print(f"API Key: {PARALLEL_API_KEY[:20]}...\n")
    
    test_url = "https://fr.indeed.com/emplois?q=Product+Manager&l=Bordeaux"
    
    print(f"Target URL: {test_url}\n")
    print("📡 Calling Parallel Search API...")
    
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
                            "urls": [test_url],
                        }
                    }
                }
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ SUCCESS!")
                print(f"\nResponse keys: {list(data.keys())}")
                print(f"\nFull response structure:")
                print(json.dumps(data, indent=2)[:2000])
                
                # Extract from MCP JSON-RPC response
                if "result" in data:
                    result = data["result"]
                    print(f"\n✅ Result found: {type(result)}")
                    print(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'not a dict'}")
                    
                    content = None
                    if isinstance(result, dict):
                        content = result.get("content") or result.get("html") or result.get("text")
                        if isinstance(content, list) and len(content) > 0:
                            content = content[0].get("text") if isinstance(content[0], dict) else str(content[0])
                    
                    if content:
                        print(f"\n✅ Content found: {len(str(content)):,} characters")
                        print(f"\nFirst 500 chars:\n{str(content)[:500]}")
                    else:
                        print("\n⚠️  No content found in result")
                elif "error" in data:
                    print(f"\n❌ MCP Error: {data['error']}")
                else:
                    print("\n⚠️  Unexpected response format")
            else:
                print(f"\n❌ FAILED")
                print(f"Response: {response.text[:500]}")
                
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
    
    print(f"\n{'='*80}")


if __name__ == "__main__":
    asyncio.run(test_parallel_api())
