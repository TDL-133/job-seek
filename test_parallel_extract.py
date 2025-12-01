"""
Test Parallel Extract API (Beta) on job search platforms
"""
import asyncio
import httpx
import json

PARALLEL_API_KEY = "TDevMkqIQNpuo5aTwTn5FAJ9BcKRpSk394Otl5pv"


async def extract_with_parallel(urls: list[str], objective: str = None):
    """Extract content using Parallel Extract API (Beta)"""
    
    print(f"\n{'='*80}")
    print(f"📡 Testing Parallel Extract API")
    print('='*80)
    print(f"URLs: {len(urls)}")
    for url in urls:
        print(f"  - {url[:80]}...")
    print(f"Objective: {objective or 'None'}\n")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.parallel.ai/v1beta/extract",
                headers={
                    "x-api-key": PARALLEL_API_KEY,
                    "Content-Type": "application/json",
                    "parallel-beta": "search-extract-2025-10-10",
                },
                json={
                    "urls": urls,
                    "objective": objective,
                    "excerpts": True,
                    "full_content": False,  # Don't need full content for now
                }
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"\n✅ SUCCESS!")
                print(f"\nExtract ID: {data.get('extract_id', 'N/A')}")
                
                results = data.get('results', [])
                errors = data.get('errors', [])
                
                print(f"\n📊 Results: {len(results)} successful")
                print(f"❌ Errors: {len(errors)} failed")
                
                # Display each result
                for i, result in enumerate(results, 1):
                    print(f"\n{'─'*80}")
                    print(f"Result #{i}")
                    print(f"{'─'*80}")
                    print(f"🔗 URL: {result.get('url', 'N/A')[:80]}...")
                    print(f"📄 Title: {result.get('title', 'N/A')[:100]}")
                    print(f"📅 Publish Date: {result.get('publish_date', 'N/A')}")
                    
                    excerpts = result.get('excerpts', [])
                    if excerpts:
                        print(f"\n📝 Excerpts ({len(excerpts)} found):")
                        for j, excerpt in enumerate(excerpts[:3], 1):  # Show first 3
                            excerpt_preview = excerpt[:300].replace('\n', ' ')
                            print(f"\n  Excerpt {j}:")
                            print(f"  {excerpt_preview}...")
                    else:
                        print("\n⚠️  No excerpts found")
                
                # Display errors
                if errors:
                    print(f"\n{'='*80}")
                    print("❌ ERRORS")
                    print('='*80)
                    for error in errors:
                        print(f"\nURL: {error.get('url', 'N/A')[:80]}")
                        print(f"Type: {error.get('error_type', 'N/A')}")
                        print(f"HTTP Status: {error.get('http_status_code', 'N/A')}")
                        if error.get('content'):
                            print(f"Details: {error.get('content')[:200]}...")
                
                return data
                
            else:
                print(f"\n❌ HTTP Error {response.status_code}")
                print(f"Response: {response.text[:500]}")
                return None
                
    except Exception as e:
        print(f"\n❌ Exception: {type(e).__name__}: {e}")
        return None


async def main():
    print("="*80)
    print("🧪 PARALLEL EXTRACT API TEST")
    print("="*80)
    print(f"API Key: {PARALLEL_API_KEY[:20]}...\n")
    
    # Test 1: Extract from Indeed with objective
    print("\n" + "="*80)
    print("TEST 1: Indeed France with Objective")
    print("="*80)
    
    indeed_urls = [
        "https://fr.indeed.com/emplois?q=Product+Manager&l=Bordeaux"
    ]
    
    objective1 = "Extract job listings for Product Manager positions including: job title, company name, location, salary if mentioned, and job description summary"
    
    result1 = await extract_with_parallel(indeed_urls, objective1)
    
    await asyncio.sleep(3)
    
    # Test 2: Extract from multiple platforms
    print("\n\n" + "="*80)
    print("TEST 2: Multiple Platforms with Objective")
    print("="*80)
    
    multi_urls = [
        "https://fr.indeed.com/emplois?q=Product+Manager&l=Bordeaux",
        "https://www.glassdoor.fr/Job/bordeaux-product-manager-jobs-SRCH_IL.0,8_IC2490183_KO9,24.htm",
        "https://www.welcometothejungle.com/fr/jobs?query=Product+Manager&aroundQuery=Bordeaux",
    ]
    
    objective2 = "Find Product Manager job postings with company names, locations, and any salary information"
    
    result2 = await extract_with_parallel(multi_urls, objective2)
    
    await asyncio.sleep(3)
    
    # Test 3: No objective (general extraction)
    print("\n\n" + "="*80)
    print("TEST 3: Indeed without Objective (General Extraction)")
    print("="*80)
    
    result3 = await extract_with_parallel(indeed_urls, objective=None)
    
    # Summary
    print(f"\n\n{'='*80}")
    print("📊 SUMMARY")
    print('='*80)
    
    tests = [
        ("Test 1: Indeed with Objective", result1),
        ("Test 2: Multi-platform with Objective", result2),
        ("Test 3: Indeed without Objective", result3),
    ]
    
    for name, result in tests:
        status = "✅" if result else "❌"
        if result:
            results_count = len(result.get('results', []))
            errors_count = len(result.get('errors', []))
            print(f"{status} {name:45} {results_count} results, {errors_count} errors")
        else:
            print(f"{status} {name:45} Failed")
    
    print('='*80)


if __name__ == "__main__":
    asyncio.run(main())
