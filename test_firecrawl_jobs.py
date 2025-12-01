"""
Test that Firecrawl returns complete job offers that can be parsed
"""
import asyncio
import sys
sys.path.insert(0, '/app')

from src.scrapers.indeed import IndeedScraper
from src.scrapers.glassdoor import GlassdoorScraper
from src.scrapers.wttj import WTTJScraper


async def test_scraper(scraper, name):
    """Test a scraper and show results"""
    print(f"\n{'='*70}")
    print(f"🧪 Testing {name}")
    print('='*70)
    
    try:
        jobs = await scraper.search(
            keywords="Product Manager",
            location="Paris",
            limit=5
        )
        
        print(f"\n📊 Found {len(jobs)} jobs\n")
        
        if jobs:
            for i, job in enumerate(jobs[:3], 1):  # Show first 3
                print(f"Job #{i}:")
                print(f"  📌 Title: {job.get('title', 'N/A')}")
                print(f"  🏢 Company: {job.get('company_name', 'N/A')}")
                print(f"  📍 Location: {job.get('location', 'N/A')}")
                print(f"  🏠 Remote: {job.get('remote_type', 'N/A')}")
                print(f"  💰 Salary: {job.get('salary_min', 'N/A')} - {job.get('salary_max', 'N/A')} {job.get('salary_currency', '')}")
                print(f"  🔗 URL: {job.get('source_url', 'N/A')[:80]}...")
                
                # Check description
                desc = job.get('description', '')
                if desc:
                    print(f"  📝 Description: {len(desc)} chars - {desc[:100]}...")
                else:
                    print(f"  ⚠️  No description")
                print()
            
            return len(jobs)
        else:
            print("⚠️  No jobs found")
            return 0
            
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 0


async def main():
    print("="*70)
    print("🔍 TESTING JOB SCRAPERS WITH FIRECRAWL")
    print("="*70)
    
    # Test each scraper
    scrapers = [
        (IndeedScraper(), "Indeed"),
        (GlassdoorScraper(), "Glassdoor"),
        (WTTJScraper(), "Welcome to the Jungle"),
    ]
    
    results = {}
    for scraper, name in scrapers:
        count = await test_scraper(scraper, name)
        results[name] = count
        await asyncio.sleep(1)  # Rate limiting
    
    # Summary
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    for name, count in results.items():
        status = "✅" if count > 0 else "❌"
        print(f"{status} {name}: {count} jobs found")
    
    total = sum(results.values())
    print(f"\n🎯 Total: {total} jobs found across all platforms")
    
    if total > 0:
        print("\n✅ Firecrawl is working and returning parseable job offers!")
    else:
        print("\n⚠️  No jobs found - check scraper selectors or Firecrawl configuration")


if __name__ == "__main__":
    asyncio.run(main())
