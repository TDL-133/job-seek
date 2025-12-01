"""
Complete scraping test for Product Manager jobs in Bordeaux
across Indeed, Glassdoor, and WTTJ using Firecrawl
"""
import asyncio
import httpx
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import json
from urllib.parse import quote_plus

load_dotenv()

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")


async def scrape_with_firecrawl(url: str, platform: str):
    """Scrape a URL with Firecrawl and return HTML"""
    print(f"\n📡 Calling Firecrawl for {platform}...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.firecrawl.dev/v1/scrape",
            headers={
                "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "url": url,
                "formats": ["html"],
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                actual_data = data.get("data", {})
                html = actual_data.get("html", "")
                return html
        
        print(f"⚠️  Firecrawl failed: {response.status_code}")
        return None


def parse_indeed_jobs(html: str):
    """Parse Indeed HTML to extract job offers"""
    soup = BeautifulSoup(html, "lxml")
    
    job_cards = soup.find_all("div", class_="job_seen_beacon")[:10]
    if not job_cards:
        job_cards = soup.find_all("div", {"data-testid": "slider_item"})[:10]
    
    jobs = []
    for card in job_cards:
        try:
            title_elem = card.find("h2", class_="jobTitle") or card.find("span", {"data-testid": "jobTitle"})
            company_elem = card.find("span", {"data-testid": "company-name"}) or card.find("span", class_="companyName")
            location_elem = card.find("div", {"data-testid": "text-location"}) or card.find("div", class_="companyLocation")
            salary_elem = card.find("div", class_="salary-snippet-container")
            snippet_elem = card.find("div", class_="job-snippet")
            
            if title_elem:
                job = {
                    "title": title_elem.get_text(strip=True),
                    "company": company_elem.get_text(strip=True) if company_elem else "N/A",
                    "location": location_elem.get_text(strip=True) if location_elem else "N/A",
                    "salary": salary_elem.get_text(strip=True) if salary_elem else "N/A",
                    "snippet": snippet_elem.get_text(strip=True)[:200] + "..." if snippet_elem else "N/A",
                }
                
                # Get URL
                link_elem = card.find("a", href=True)
                if link_elem:
                    href = link_elem.get("href", "")
                    job["url"] = f"https://www.indeed.com{href}" if href.startswith("/") else href
                else:
                    job["url"] = "N/A"
                
                # Detect remote type
                loc_text = job["location"].lower()
                if "remote" in loc_text or "télétravail" in loc_text:
                    job["remote_type"] = "Remote"
                elif "hybrid" in loc_text or "hybride" in loc_text:
                    job["remote_type"] = "Hybrid"
                else:
                    job["remote_type"] = "Onsite"
                
                jobs.append(job)
        except Exception as e:
            print(f"  ⚠️  Error parsing job: {e}")
            continue
    
    return jobs


def parse_glassdoor_jobs(html: str):
    """Parse Glassdoor HTML to extract job offers"""
    soup = BeautifulSoup(html, "lxml")
    
    job_cards = soup.find_all("li", class_="react-job-listing")[:10]
    if not job_cards:
        job_cards = soup.find_all("div", {"data-test": "jobListing"})[:10]
    
    jobs = []
    for card in job_cards:
        try:
            title_elem = card.find("a", {"data-test": "job-link"}) or card.find("a", class_="jobLink")
            company_elem = card.find("div", {"data-test": "employer-short-name"})
            location_elem = card.find("span", {"data-test": "emp-location"})
            salary_elem = card.find("span", {"data-test": "detailSalary"})
            
            if title_elem:
                job = {
                    "title": title_elem.get_text(strip=True),
                    "company": company_elem.get_text(strip=True) if company_elem else "N/A",
                    "location": location_elem.get_text(strip=True) if location_elem else "N/A",
                    "salary": salary_elem.get_text(strip=True) if salary_elem else "N/A",
                    "snippet": "N/A",
                }
                
                href = title_elem.get("href", "")
                job["url"] = f"https://www.glassdoor.com{href}" if href.startswith("/") else href
                
                loc_text = job["location"].lower()
                if "remote" in loc_text:
                    job["remote_type"] = "Remote"
                elif "hybrid" in loc_text:
                    job["remote_type"] = "Hybrid"
                else:
                    job["remote_type"] = "Onsite"
                
                jobs.append(job)
        except Exception as e:
            print(f"  ⚠️  Error parsing job: {e}")
            continue
    
    return jobs


def parse_wttj_jobs(html: str):
    """Parse WTTJ HTML to extract job offers"""
    soup = BeautifulSoup(html, "lxml")
    
    job_cards = soup.find_all("article", {"data-testid": "search-results-list-item-wrapper"})[:10]
    if not job_cards:
        job_cards = soup.find_all("div", class_="ais-Hits-item")[:10]
    
    jobs = []
    for card in job_cards:
        try:
            title_elem = card.find("h4") or card.find("span", class_="job-title")
            company_elem = card.find("span", {"data-testid": "search-results-list-item-company-name"})
            location_elem = card.find("span", {"data-testid": "search-results-list-item-contract-location"})
            link_elem = card.find("a", href=True)
            
            if title_elem:
                job = {
                    "title": title_elem.get_text(strip=True),
                    "company": company_elem.get_text(strip=True) if company_elem else "N/A",
                    "location": location_elem.get_text(strip=True) if location_elem else "N/A",
                    "salary": "N/A",
                    "snippet": "N/A",
                }
                
                if link_elem:
                    href = link_elem.get("href", "")
                    job["url"] = f"https://www.welcometothejungle.com{href}" if href.startswith("/") else href
                else:
                    job["url"] = "N/A"
                
                loc_text = job["location"].lower()
                if "remote" in loc_text or "télétravail" in loc_text:
                    job["remote_type"] = "Remote"
                elif "hybrid" in loc_text or "hybride" in loc_text:
                    job["remote_type"] = "Hybrid"
                else:
                    job["remote_type"] = "Onsite"
                
                jobs.append(job)
        except Exception as e:
            print(f"  ⚠️  Error parsing job: {e}")
            continue
    
    return jobs


async def test_platform(platform_name: str, url: str, parser_func):
    """Test scraping for a platform"""
    print(f"\n{'='*80}")
    print(f"🔍 {platform_name}")
    print('='*80)
    print(f"URL: {url}\n")
    
    html = await scrape_with_firecrawl(url, platform_name)
    
    if not html:
        print(f"❌ No HTML returned")
        return []
    
    print(f"✅ HTML received: {len(html):,} characters\n")
    
    jobs = parser_func(html)
    print(f"📊 Found {len(jobs)} jobs\n")
    
    return jobs


def display_jobs(platform: str, jobs: list):
    """Display jobs in a structured format"""
    if not jobs:
        print(f"⚠️  No jobs found for {platform}\n")
        return
    
    print(f"\n{'='*80}")
    print(f"📋 {platform.upper()} - {len(jobs)} OFFRES TROUVÉES")
    print('='*80)
    
    for i, job in enumerate(jobs, 1):
        print(f"\n{i}. {job.get('title', 'N/A')}")
        print(f"   🏢 Entreprise: {job.get('company', 'N/A')}")
        print(f"   📍 Localisation: {job.get('location', 'N/A')}")
        print(f"   🏠 Type: {job.get('remote_type', 'N/A')}")
        if job.get('salary') != 'N/A':
            print(f"   💰 Salaire: {job.get('salary', 'N/A')}")
        if job.get('snippet') != 'N/A':
            print(f"   📝 Aperçu: {job.get('snippet', 'N/A')}")
        print(f"   🔗 URL: {job.get('url', 'N/A')[:80]}...")


async def main():
    keywords = "Product Manager"
    location = "Bordeaux"
    
    print("="*80)
    print(f"🎯 RECHERCHE: {keywords} à {location}")
    print("="*80)
    print(f"API Key: {FIRECRAWL_API_KEY[:30]}...\n")
    
    # Build URLs (French versions)
    urls = {
        "Indeed": f"https://fr.indeed.com/emplois?q={quote_plus(keywords)}&l={quote_plus(location)}",
        "Glassdoor": f"https://www.glassdoor.fr/Job/bordeaux-product-manager-jobs-SRCH_IL.0,8_IC2490183_KO9,24.htm",
        "WTTJ": f"https://www.welcometothejungle.com/fr/jobs?query={quote_plus(keywords)}&aroundQuery={quote_plus(location)}&refinementList%5Boffices.country_code%5D%5B%5D=FR",
    }
    
    parsers = {
        "Indeed": parse_indeed_jobs,
        "Glassdoor": parse_glassdoor_jobs,
        "WTTJ": parse_wttj_jobs,
    }
    
    all_jobs = {}
    
    # Test each platform
    for platform, url in urls.items():
        jobs = await test_platform(platform, url, parsers[platform])
        all_jobs[platform] = jobs
        await asyncio.sleep(2)  # Rate limiting
    
    # Display results
    print("\n" + "="*80)
    print("📊 RÉSULTATS DÉTAILLÉS")
    print("="*80)
    
    for platform, jobs in all_jobs.items():
        display_jobs(platform, jobs)
    
    # Summary
    total = sum(len(jobs) for jobs in all_jobs.values())
    print(f"\n{'='*80}")
    print(f"🎯 RÉSUMÉ")
    print('='*80)
    for platform, jobs in all_jobs.items():
        emoji = "✅" if len(jobs) > 0 else "❌"
        print(f"{emoji} {platform}: {len(jobs)} offres")
    print(f"\n📊 TOTAL: {total} offres trouvées")


if __name__ == "__main__":
    asyncio.run(main())
