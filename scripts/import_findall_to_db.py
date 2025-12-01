#!/usr/bin/env python3
"""
Import FindAll CSV results into the Job Seek database.
This allows viewing FindAll results in the UI without running a new (costly) search.
"""
import csv
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import Job, Company, Base

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://jobseek:jobseek_password@localhost:5433/jobseek_db")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def import_findall_csv(csv_path: str):
    """Import FindAll results from CSV into database."""
    session = Session()
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            imported = 0
            skipped = 0
            
            for row in reader:
                # Check if job already exists by URL
                existing = session.query(Job).filter(Job.source_url == row['URL']).first()
                if existing:
                    skipped += 1
                    continue
                
                # Get or create company
                company_name = row.get('Company', 'N/A')
                if company_name and company_name != 'N/A':
                    company = session.query(Company).filter(Company.name == company_name).first()
                    if not company:
                        company = Company(name=company_name)
                        session.add(company)
                        session.flush()
                else:
                    company = None
                
                # Map source to platform
                source_map = {
                    'Glassdoor': 'glassdoor',
                    'Welcome to the Jungle': 'welcometothejungle',
                    'Indeed': 'indeed',
                    'LinkedIn': 'linkedin'
                }
                source_platform = source_map.get(row.get('Source', ''), 'findall')
                
                # Create job
                job = Job(
                    title=row['Job Title'][:200] if row['Job Title'] else 'Unknown',
                    company_id=company.id if company else None,
                    location=row.get('Location', 'Toulouse, FR'),
                    description=row.get('Description', ''),
                    source_url=row['URL'],
                    source_platform=f"findall_{source_platform}",  # Mark as FindAll source
                    job_type=row.get('Role Type', '')[:50] if row.get('Role Type') else None,
                    is_active=True
                )
                session.add(job)
                imported += 1
                print(f"✅ Imported: {job.title[:50]}... ({source_platform})")
            
            session.commit()
            print(f"\n📊 Summary:")
            print(f"   - Imported: {imported} jobs")
            print(f"   - Skipped (duplicates): {skipped} jobs")
            print(f"   - Total in CSV: {imported + skipped} jobs")
            
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    csv_path = "/app/scripts/toulouse_findall_results.csv"
    
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    
    print(f"🔄 Importing FindAll results from: {csv_path}")
    import_findall_csv(csv_path)
    print("\n✅ Done! Refresh the Dashboard to see FindAll jobs.")
