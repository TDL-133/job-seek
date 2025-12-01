#!/usr/bin/env python3
"""
Run full scraping pipeline (Phase 1-3) to verify end-to-end functionality
with the new filtering and expansion logic.
"""
import asyncio
import os
from parallel_scraper import ParallelScraper
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent.parent / ".env")

async def run_full_scrape():
    api_key = os.getenv("PARALLEL_API_KEY")
    scraper = ParallelScraper(api_key)
    
    # Parameters matching user request
    job_title = "Customer Success Manager"
    city = "Marseille"
    region = "Provence-Alpes-Côte d'Azur"
    
    # Run full pipeline
    csv_path = await scraper.run(job_title, city, region, limit_per_source=20)
    
    if csv_path:
        print(f"\n✅ Full scrape completed successfully!")
        print(f"📄 Results saved to: {csv_path}")
    else:
        print(f"\n❌ Scrape failed or returned no results.")

if __name__ == "__main__":
    asyncio.run(run_full_scrape())
