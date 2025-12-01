"""
Test script for Parallel Search API integration
"""
import asyncio
import os
from dotenv import load_dotenv
from src.services.scraping_service import ScrapingService

load_dotenv()


async def test_parallel_search():
    """Test Parallel Search API with a real job search URL"""
    
    print("="*80)
    print("🧪 TEST: Parallel Search API Integration")
    print("="*80)
    
    api_key = os.getenv("PARALLEL_API_KEY")
    if not api_key:
        print("❌ ERROR: PARALLEL_API_KEY not found in .env")
        return
    
    print(f"✅ API Key loaded: {api_key[:20]}...")
    
    # Initialize scraping service
    service = ScrapingService()
    
    # Test URLs
    test_urls = [
        ("Indeed France", "https://fr.indeed.com/emplois?q=Product+Manager&l=Bordeaux"),
        ("Glassdoor", "https://www.glassdoor.fr/Job/bordeaux-product-manager-jobs-SRCH_IL.0,8_IC2490183_KO9,24.htm"),
    ]
    
    for name, url in test_urls:
        print(f"\n{'='*80}")
        print(f"📡 Testing: {name}")
        print(f"URL: {url}")
        print('='*80)
        
        try:
            # Test with Parallel Search only
            html = await service._fetch_with_parallel(url)
            
            if html:
                print(f"✅ SUCCESS: Got {len(html):,} characters")
                print(f"\n📄 First 500 chars:")
                print(html[:500])
                
                # Check if it contains job-related content
                keywords = ["job", "emploi", "product manager", "poste", "offre"]
                found_keywords = [kw for kw in keywords if kw.lower() in html.lower()]
                
                if found_keywords:
                    print(f"\n✅ Found relevant keywords: {', '.join(found_keywords)}")
                else:
                    print(f"\n⚠️  Warning: No job-related keywords found")
            else:
                print("❌ FAILED: No HTML returned")
                
        except Exception as e:
            print(f"❌ ERROR: {type(e).__name__}: {e}")
        
        await asyncio.sleep(2)  # Rate limiting
    
    # Test fallback mechanism
    print(f"\n{'='*80}")
    print("🔄 Testing fallback mechanism")
    print('='*80)
    
    test_url = "https://fr.indeed.com/emplois?q=Developer&l=Paris"
    print(f"URL: {test_url}")
    
    html = await service.fetch_page(test_url)
    
    if html:
        print(f"✅ Fallback worked: Got {len(html):,} characters")
    else:
        print("❌ All methods failed")
    
    print(f"\n{'='*80}")
    print("🎯 TEST COMPLETE")
    print('='*80)


if __name__ == "__main__":
    asyncio.run(test_parallel_search())
