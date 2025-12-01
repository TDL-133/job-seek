"""
Enhanced scraping test with full job details extraction
"""
import asyncio
import httpx
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import json
from urllib.parse import quote_plus
import re

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
                "formats": ["html", "markdown"],
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                actual_data = data.get("data", {})
                html = actual_data.get("html", "")
                markdown = actual_data.get("markdown", "")
                return html, markdown
        
        print(f"⚠️  Firecrawl failed: {response.status_code}")
        return None, None


def parse_indeed_jobs(html: str):
    """Parse Indeed HTML to extract job offers with maximum details"""
    soup = BeautifulSoup(html, "lxml")
    
    # Try multiple selectors
    job_cards = soup.find_all("div", class_="job_seen_beacon")[:15]
    if not job_cards:
        job_cards = soup.find_all("div", {"data-testid": "slider_item"})[:15]
    if not job_cards:
        job_cards = soup.find_all("div", class_="jobsearch-ResultsList")[:15]
    
    print(f"  🔍 Found {len(job_cards)} job cards")
    
    jobs = []
    for idx, card in enumerate(job_cards, 1):
        try:
            # Title
            title_elem = card.find("h2", class_="jobTitle") or card.find("span", {"data-testid": "jobTitle"})
            if not title_elem:
                continue
            
            # Company
            company_elem = card.find("span", {"data-testid": "company-name"}) or card.find("span", class_="companyName")
            
            # Location
            location_elem = card.find("div", {"data-testid": "text-location"}) or card.find("div", class_="companyLocation")
            
            # Salary
            salary_elem = card.find("div", class_="salary-snippet-container")
            if not salary_elem:
                salary_elem = card.find("span", class_="salary-snippet")
            
            # Job snippet/description
            snippet_elem = card.find("div", class_="job-snippet")
            if not snippet_elem:
                snippet_elem = card.find("div", {"data-testid": "job-snippet"})
            
            # Job metadata
            metadata_elem = card.find("div", class_="metadata")
            
            job = {
                "title": title_elem.get_text(strip=True),
                "company": company_elem.get_text(strip=True) if company_elem else "N/A",
                "location": location_elem.get_text(strip=True) if location_elem else "N/A",
                "salary": salary_elem.get_text(strip=True) if salary_elem else "Non communiqué",
                "description": snippet_elem.get_text(strip=True) if snippet_elem else "N/A",
                "metadata": metadata_elem.get_text(strip=True) if metadata_elem else "",
            }
            
            # Extract URL
            link_elem = card.find("a", href=True)
            if link_elem:
                href = link_elem.get("href", "")
                job["url"] = f"https://fr.indeed.com{href}" if href.startswith("/") else href
            else:
                job["url"] = "N/A"
            
            # Detect remote type
            loc_text = job["location"].lower()
            desc_text = job["description"].lower()
            combined = f"{loc_text} {desc_text}"
            
            if "remote" in combined or "télétravail" in combined or "full remote" in combined:
                job["remote_type"] = "🏠 Full Remote"
            elif "hybrid" in combined or "hybride" in combined or "partiel" in combined:
                job["remote_type"] = "🔄 Hybride"
            else:
                job["remote_type"] = "🏢 Sur site"
            
            # Extract job type from metadata or description
            if "cdi" in combined:
                job["contract_type"] = "CDI"
            elif "cdd" in combined:
                job["contract_type"] = "CDD"
            elif "stage" in combined or "internship" in combined:
                job["contract_type"] = "Stage"
            elif "alternance" in combined:
                job["contract_type"] = "Alternance"
            else:
                job["contract_type"] = "Non spécifié"
            
            # Extract seniority hints
            title_lower = job["title"].lower()
            if "senior" in title_lower or "lead" in title_lower or "head" in title_lower:
                job["seniority"] = "Senior"
            elif "junior" in title_lower or "junior" in desc_text:
                job["seniority"] = "Junior"
            else:
                job["seniority"] = "Intermédiaire"
            
            jobs.append(job)
            print(f"  ✅ Job {idx}: {job['title'][:50]}")
            
        except Exception as e:
            print(f"  ⚠️  Error parsing job {idx}: {e}")
            continue
    
    return jobs


def debug_html_structure(html: str, platform: str):
    """Debug HTML structure to find job elements"""
    soup = BeautifulSoup(html, "lxml")
    
    print(f"\n🔍 DEBUG: Analyzing {platform} HTML structure")
    
    # Look for common job listing patterns
    patterns = [
        ("div", {"class": re.compile("job|listing|card|result", re.I)}),
        ("article", {}),
        ("li", {"class": re.compile("job|listing|result", re.I)}),
        ("div", {"data-test": re.compile("job", re.I)}),
        ("div", {"data-testid": re.compile("job|listing", re.I)}),
    ]
    
    for tag, attrs in patterns:
        elements = soup.find_all(tag, attrs)
        if elements:
            print(f"  Found {len(elements)} <{tag}> elements with pattern {attrs}")
            if len(elements) > 0:
                first = elements[0]
                print(f"  Sample classes: {first.get('class', [])}")
                print(f"  Sample data-*: {[k for k in first.attrs.keys() if k.startswith('data-')]}")


def parse_glassdoor_jobs(html: str):
    """Parse Glassdoor HTML - enhanced version"""
    soup = BeautifulSoup(html, "lxml")
    
    # Debug first
    debug_html_structure(html, "Glassdoor")
    
    # Try multiple selectors
    selectors = [
        ("li", {"class": "react-job-listing"}),
        ("div", {"data-test": "jobListing"}),
        ("article", {"data-test": re.compile("job", re.I)}),
        ("div", {"class": re.compile("JobCard", re.I)}),
    ]
    
    job_cards = []
    for tag, attrs in selectors:
        job_cards = soup.find_all(tag, attrs)[:15]
        if job_cards:
            print(f"  ✅ Found {len(job_cards)} jobs with selector: {tag} {attrs}")
            break
    
    jobs = []
    for idx, card in enumerate(job_cards, 1):
        try:
            # Multiple selector attempts
            title_elem = (
                card.find("a", {"data-test": "job-link"}) or
                card.find("a", class_="jobLink") or
                card.find("h3") or
                card.find("h2")
            )
            
            if not title_elem:
                continue
            
            job = {
                "title": title_elem.get_text(strip=True),
                "company": "N/A",
                "location": "N/A",
                "salary": "Non communiqué",
                "description": "N/A",
                "remote_type": "🏢 Sur site",
                "contract_type": "Non spécifié",
                "seniority": "Non spécifié",
            }
            
            # Try to extract more details
            company_elem = card.find("div", {"data-test": "employer-short-name"})
            if company_elem:
                job["company"] = company_elem.get_text(strip=True)
            
            location_elem = card.find("span", {"data-test": "emp-location"})
            if location_elem:
                job["location"] = location_elem.get_text(strip=True)
            
            salary_elem = card.find("span", {"data-test": "detailSalary"})
            if salary_elem:
                job["salary"] = salary_elem.get_text(strip=True)
            
            # URL
            href = title_elem.get("href", "")
            job["url"] = f"https://www.glassdoor.fr{href}" if href.startswith("/") else href
            
            jobs.append(job)
            print(f"  ✅ Job {idx}: {job['title'][:50]}")
            
        except Exception as e:
            print(f"  ⚠️  Error parsing job {idx}: {e}")
            continue
    
    return jobs


def parse_wttj_jobs(html: str):
    """Parse WTTJ HTML - enhanced version"""
    soup = BeautifulSoup(html, "lxml")
    
    # Debug first
    debug_html_structure(html, "WTTJ")
    
    # Try multiple selectors
    selectors = [
        ("article", {"data-testid": "search-results-list-item-wrapper"}),
        ("div", {"class": "ais-Hits-item"}),
        ("li", {"class": re.compile("sc-.*-SearchResultItem", re.I)}),
        ("div", {"class": re.compile("JobCard", re.I)}),
    ]
    
    job_cards = []
    for tag, attrs in selectors:
        job_cards = soup.find_all(tag, attrs)[:15]
        if job_cards:
            print(f"  ✅ Found {len(job_cards)} jobs with selector: {tag} {attrs}")
            break
    
    jobs = []
    for idx, card in enumerate(job_cards, 1):
        try:
            title_elem = (
                card.find("h4") or
                card.find("h3") or
                card.find("span", class_="job-title") or
                card.find("a", {"data-testid": re.compile("job.*title", re.I)})
            )
            
            if not title_elem:
                continue
            
            job = {
                "title": title_elem.get_text(strip=True),
                "company": "N/A",
                "location": "N/A",
                "salary": "Non communiqué",
                "description": "N/A",
                "remote_type": "🏢 Sur site",
                "contract_type": "Non spécifié",
                "seniority": "Non spécifié",
            }
            
            # Company
            company_elem = card.find("span", {"data-testid": "search-results-list-item-company-name"})
            if company_elem:
                job["company"] = company_elem.get_text(strip=True)
            
            # Location
            location_elem = card.find("span", {"data-testid": "search-results-list-item-contract-location"})
            if location_elem:
                job["location"] = location_elem.get_text(strip=True)
            
            # URL
            link_elem = card.find("a", href=True)
            if link_elem:
                href = link_elem.get("href", "")
                job["url"] = f"https://www.welcometothejungle.com{href}" if href.startswith("/") else href
            else:
                job["url"] = "N/A"
            
            jobs.append(job)
            print(f"  ✅ Job {idx}: {job['title'][:50]}")
            
        except Exception as e:
            print(f"  ⚠️  Error parsing job {idx}: {e}")
            continue
    
    return jobs


def display_jobs(platform: str, jobs: list):
    """Display jobs in a beautiful structured format"""
    if not jobs:
        print(f"\n⚠️  No jobs found for {platform}\n")
        return
    
    print(f"\n{'='*80}")
    print(f"📋 {platform.upper()} - {len(jobs)} OFFRES DÉTAILLÉES")
    print('='*80)
    
    for i, job in enumerate(jobs, 1):
        print(f"\n{'─'*80}")
        print(f"#{i} | {job.get('title', 'N/A')}")
        print(f"{'─'*80}")
        print(f"🏢 Entreprise:      {job.get('company', 'N/A')}")
        print(f"📍 Localisation:    {job.get('location', 'N/A')}")
        print(f"   Mode de travail: {job.get('remote_type', 'N/A')}")
        print(f"💼 Type de contrat: {job.get('contract_type', 'Non spécifié')}")
        print(f"📊 Niveau:          {job.get('seniority', 'Non spécifié')}")
        
        if job.get('salary') and job.get('salary') != 'Non communiqué':
            print(f"💰 Salaire:         {job.get('salary')}")
        
        if job.get('description') and job.get('description') != 'N/A' and len(job.get('description', '')) > 10:
            desc = job.get('description', 'N/A')
            if len(desc) > 300:
                desc = desc[:300] + "..."
            print(f"📝 Description:     {desc}")
        
        url = job.get('url', 'N/A')
        if len(url) > 80:
            url = url[:80] + "..."
        print(f"🔗 URL:             {url}")


async def main():
    keywords = "Product Manager"
    location = "Bordeaux"
    
    print("="*80)
    print(f"🎯 RECHERCHE DÉTAILLÉE: {keywords} à {location}")
    print("="*80)
    print(f"🔑 API Key: {FIRECRAWL_API_KEY[:30]}...\n")
    
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
        print(f"\n{'='*80}")
        print(f"🔍 SCRAPING: {platform}")
        print('='*80)
        print(f"URL: {url}\n")
        
        html, markdown = await scrape_with_firecrawl(url, platform)
        
        if not html:
            print(f"❌ No HTML returned")
            all_jobs[platform] = []
            continue
        
        print(f"✅ HTML: {len(html):,} chars | Markdown: {len(markdown):,} chars")
        
        jobs = parsers[platform](html)
        all_jobs[platform] = jobs
        
        print(f"\n📊 Résultat: {len(jobs)} offres extraites")
        
        await asyncio.sleep(2)  # Rate limiting
    
    # Display all results
    print("\n" + "="*80)
    print("📊 RÉSULTATS COMPLETS")
    print("="*80)
    
    for platform, jobs in all_jobs.items():
        display_jobs(platform, jobs)
    
    # Summary
    total = sum(len(jobs) for jobs in all_jobs.values())
    print(f"\n{'='*80}")
    print(f"🎯 RÉSUMÉ FINAL")
    print('='*80)
    for platform, jobs in all_jobs.items():
        emoji = "✅" if len(jobs) > 0 else "❌"
        print(f"{emoji} {platform:15} {len(jobs):2} offres")
    print(f"{'─'*80}")
    print(f"📊 TOTAL:           {total:2} offres trouvées avec informations détaillées")
    print('='*80)


if __name__ == "__main__":
    asyncio.run(main())
