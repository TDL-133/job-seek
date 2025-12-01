#!/usr/bin/env python3
"""
Test Unipile LinkedIn query variants to find more jobs.
"""
import asyncio
import os
import json
from pathlib import Path
import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

async def test_linkedin_query():
    unipile_dsn = os.getenv("UNIPILE_DSN")
    unipile_api_key = os.getenv("UNIPILE_API_KEY")
    unipile_account_id = os.getenv("UNIPILE_LINKEDIN_ACCOUNT_ID")
    
    if not all([unipile_dsn, unipile_api_key, unipile_account_id]):
        print("Unipile credentials missing")
        return

    # Variants to test
    variants = [
        {
            "name": "Strict AND",
            "json": {
                "api": "classic",
                "category": "jobs",
                "keywords": "\"Customer Success Manager\" AND \"Marseille\"",
                "limit": 20
            }
        },
        {
            "name": "Loose (No quotes)",
            "json": {
                "api": "classic",
                "category": "jobs",
                "keywords": "Customer Success Manager Marseille",
                "limit": 20
            }
        },
        {
            "name": "Separate Location Param",
            "json": {
                "api": "classic",
                "category": "jobs",
                "keywords": "Customer Success Manager",
                "location": "Marseille",
                "limit": 20
            }
        },
        {
            "name": "Broad Keywords",
            "json": {
                "api": "classic",
                "category": "jobs",
                "keywords": "Customer Success Manager",
                "limit": 20
            }
        }
    ]
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for variant in variants:
            print(f"\nTesting: {variant['name']}...")
            print(f"Payload: {json.dumps(variant['json'])}")
            
            try:
                response = await client.post(
                    f"{unipile_dsn}/api/v1/linkedin/search",
                    headers={
                        "X-API-KEY": unipile_api_key,
                        "accept": "application/json",
                        "content-type": "application/json"
                    },
                    params={"account_id": unipile_account_id},
                    json=variant['json']
                )
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get("items", [])
                    jobs = [i for i in items if i.get("type") == "JOB"]
                    print(f"✅ Found {len(jobs)} jobs")
                    for job in jobs:
                        print(f"   - {job.get('title')} @ {job.get('company', {}).get('name')} ({job.get('location')})")
                else:
                    print(f"❌ Error {response.status_code}: {response.text[:100]}")
                    
            except Exception as e:
                print(f"❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_linkedin_query())
