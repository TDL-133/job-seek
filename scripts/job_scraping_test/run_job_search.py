#!/usr/bin/env python3
"""
Job Search Orchestrator - Complete Workflow

Runs the complete job search pipeline:
1. Phase 1: Multi-platform URL collection (parallel_scraper.py)
2. Phase 2: Job details extraction & location validation (extract_job_details.py)
3. Phase 3: V2 scoring system (score_jobs.py)

Usage:
    python run_job_search.py "Product Designer" "Lille" "Hauts-de-France"
    python run_job_search.py "Product Manager" "Lyon" "Auvergne-Rhône-Alpes" --limit 20
"""

import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional


class JobSearchOrchestrator:
    """Orchestrates the complete job search workflow."""
    
    def __init__(self, job_title: str, city: str, region: str, limit: int = 10):
        self.job_title = job_title
        self.city = city
        self.region = region
        self.limit = limit
        
        # Setup paths
        self.script_dir = Path(__file__).parent
        self.results_dir = self.script_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
        
        # Timestamped run
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = self.results_dir / f"{self.timestamp}_{city.lower()}_{job_title.lower().replace(' ', '_')}"
        self.run_dir.mkdir(exist_ok=True)
        
        print(f"🎯 Job Search Orchestrator")
        print(f"{'='*60}")
        print(f"Query: {job_title} in {city}, {region}")
        print(f"Limit per source: {limit}")
        print(f"Output directory: {self.run_dir}")
        print(f"{'='*60}\n")
    
    def run_phase1(self) -> bool:
        """Run Phase 1: URL collection."""
        print(f"\n{'='*60}")
        print("PHASE 1: MULTI-PLATFORM URL COLLECTION")
        print(f"{'='*60}\n")
        
        # Use test_phase1_only.py which already outputs JSON
        cmd = [
            sys.executable,
            str(self.script_dir / "test_phase1_only.py"),
            self.job_title,
            self.city,
            self.region,
            str(self.limit)
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.script_dir),
                capture_output=False,
                text=True,
                check=True
            )
            
            # Move output to run directory
            phase1_file = self.script_dir / "phase1_urls.md"
            if phase1_file.exists():
                import shutil
                shutil.move(str(phase1_file), str(self.run_dir / "phase1_urls.md"))
            
            # Create JSON format for Phase 2
            urls_md = self.run_dir / "phase1_urls.md"
            if urls_md.exists():
                jobs = self._parse_phase1_md(str(urls_md))
                json_path = self.run_dir / "phase1_urls.json"
                with open(json_path, 'w') as f:
                    json.dump({"jobs": jobs, "query": f"{self.job_title} in {self.city}"}, f, indent=2)
                print(f"\n✅ Phase 1 complete: {len(jobs)} URLs collected")
                return True
            else:
                print("\n❌ Phase 1 failed: No output file generated")
                return False
            
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Phase 1 failed with error code {e.returncode}")
            return False
    
    def _parse_phase1_md(self, filepath: str) -> list:
        """Parse phase1_urls.md into JSON format."""
        jobs = []
        current_platform = None
        
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                
                if line.startswith("## "):
                    # Platform header: "## LinkedIn (13)"
                    import re
                    match = re.match(r'## (\w+)', line)
                    if match:
                        current_platform = match.group(1)
                
                elif line.startswith("- https://"):
                    # URL line
                    url = line.split()[1]
                    if current_platform:
                        jobs.append({
                            "url": url,
                            "platform": current_platform
                        })
        
        return jobs
    
    def run_phase2(self) -> bool:
        """Run Phase 2: Job details extraction."""
        print(f"\n{'='*60}")
        print("PHASE 2: JOB DETAILS EXTRACTION & LOCATION VALIDATION")
        print(f"{'='*60}\n")
        
        phase1_json = self.run_dir / "phase1_urls.json"
        if not phase1_json.exists():
            print("❌ Phase 1 output not found")
            return False
        
        cmd = [
            sys.executable,
            str(self.script_dir / "extract_job_details.py"),
            self.city,
            str(phase1_json)
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.script_dir),
                capture_output=False,
                text=True,
                check=True
            )
            
            # Check output
            phase2_json = self.run_dir / "phase2_jobs.json"
            if phase2_json.exists():
                with open(phase2_json) as f:
                    jobs = json.load(f)
                print(f"\n✅ Phase 2 complete: {len(jobs)} jobs extracted")
                return True
            else:
                print("\n❌ Phase 2 failed: No output generated")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Phase 2 failed with error code {e.returncode}")
            return False
    
    def run_phase3(self, user_prefs: Optional[str] = None) -> bool:
        """Run Phase 3: Job scoring."""
        print(f"\n{'='*60}")
        print("PHASE 3: V2 SCORING SYSTEM")
        print(f"{'='*60}\n")
        
        phase2_json = self.run_dir / "phase2_jobs.json"
        if not phase2_json.exists():
            print("❌ Phase 2 output not found")
            return False
        
        cmd = [
            sys.executable,
            str(self.script_dir / "score_jobs.py"),
            str(phase2_json)
        ]
        
        if user_prefs:
            cmd.append(user_prefs)
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.script_dir),
                capture_output=False,
                text=True,
                check=True
            )
            
            # Check output
            phase3_json = self.run_dir / "phase3_scored.json"
            if phase3_json.exists():
                with open(phase3_json) as f:
                    scored_jobs = json.load(f)
                print(f"\n✅ Phase 3 complete: {len(scored_jobs)} jobs scored")
                return True
            else:
                print("\n❌ Phase 3 failed: No output generated")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Phase 3 failed with error code {e.returncode}")
            return False
    
    def generate_summary_report(self):
        """Generate final summary report."""
        print(f"\n{'='*60}")
        print("FINAL SUMMARY REPORT")
        print(f"{'='*60}\n")
        
        # Load all data
        try:
            with open(self.run_dir / "phase1_urls.json") as f:
                phase1_data = json.load(f)
                total_urls = len(phase1_data["jobs"])
            
            with open(self.run_dir / "phase2_jobs.json") as f:
                phase2_jobs = json.load(f)
                total_extracted = len(phase2_jobs)
                city_jobs = [j for j in phase2_jobs if j.get("is_target_city")]
                remote_jobs = [j for j in phase2_jobs if j.get("is_remote")]
            
            with open(self.run_dir / "phase3_scored.json") as f:
                scored_jobs = json.load(f)
                matched_jobs = [j for j in scored_jobs if j["is_matched"]]
                unmatched_jobs = [j for j in scored_jobs if not j["is_matched"]]
                top_5 = sorted(scored_jobs, key=lambda x: x["score"], reverse=True)[:5]
            
            # Print summary
            print(f"🎯 Query: {self.job_title} in {self.city}")
            print(f"📅 Date: {self.timestamp}")
            print(f"📁 Output: {self.run_dir}\n")
            
            print(f"📊 Phase 1 - URL Collection:")
            print(f"   Total URLs found: {total_urls}")
            by_platform = {}
            for job in phase1_data["jobs"]:
                platform = job["platform"]
                by_platform[platform] = by_platform.get(platform, 0) + 1
            for platform, count in sorted(by_platform.items(), key=lambda x: x[1], reverse=True):
                print(f"   - {platform}: {count}")
            
            print(f"\n📊 Phase 2 - Extraction & Location:")
            print(f"   Successfully extracted: {total_extracted}/{total_urls} ({total_extracted/total_urls*100:.1f}%)")
            print(f"   {self.city} jobs: {len(city_jobs)} ({len(city_jobs)/total_extracted*100:.1f}%)")
            print(f"   Remote jobs: {len(remote_jobs)} ({len(remote_jobs)/total_extracted*100:.1f}%)")
            
            print(f"\n📊 Phase 3 - Scoring (V2 System):")
            print(f"   ✅ Matched (score ≥ 40): {len(matched_jobs)} ({len(matched_jobs)/len(scored_jobs)*100:.1f}%)")
            print(f"   📋 À revoir (score < 40): {len(unmatched_jobs)} ({len(unmatched_jobs)/len(scored_jobs)*100:.1f}%)")
            
            if matched_jobs:
                avg_matched = sum(j["score"] for j in matched_jobs) / len(matched_jobs)
                print(f"   Average matched score: {avg_matched:.1f}")
            
            print(f"\n🏆 Top 5 Jobs:")
            for i, job in enumerate(top_5, 1):
                data = job["job_data"]
                print(f"   {i}. [{job['score']:.1f}] {data.get('title', 'Unknown')[:45]}")
                print(f"      {data.get('company', 'Unknown')[:30]} | {data.get('location_tag')} | {data.get('platform')}")
            
            print(f"\n📁 Output Files:")
            print(f"   {self.run_dir}/phase1_urls.md")
            print(f"   {self.run_dir}/phase1_urls.json")
            print(f"   {self.run_dir}/phase2_jobs.json")
            print(f"   {self.run_dir}/phase2_jobs.csv")
            print(f"   {self.run_dir}/phase3_scored.json")
            print(f"   {self.run_dir}/phase3_scored.csv")
            
            # Save report
            report_path = self.run_dir / "SUMMARY.md"
            with open(report_path, 'w') as f:
                f.write(f"# Job Search Summary Report\n\n")
                f.write(f"**Query**: {self.job_title} in {self.city}, {self.region}\n")
                f.write(f"**Date**: {self.timestamp}\n")
                f.write(f"**Total URLs**: {total_urls}\n")
                f.write(f"**Extracted**: {total_extracted}\n")
                f.write(f"**{self.city} jobs**: {len(city_jobs)}\n")
                f.write(f"**Remote jobs**: {len(remote_jobs)}\n")
                f.write(f"**Matched (≥40)**: {len(matched_jobs)}\n\n")
                
                f.write(f"## Top {min(len(top_5), 5)} Jobs\n\n")
                for i, job in enumerate(top_5, 1):
                    data = job["job_data"]
                    f.write(f"{i}. **{data.get('title')}** at {data.get('company')}\n")
                    f.write(f"   - Score: {job['score']:.1f}\n")
                    f.write(f"   - Location: {data.get('location_tag')}\n")
                    f.write(f"   - Platform: {data.get('platform')}\n")
                    f.write(f"   - URL: {data.get('url')}\n\n")
            
            print(f"   {report_path}")
            
        except Exception as e:
            print(f"\n⚠️  Could not generate complete summary: {e}")
    
    def run(self, user_prefs: Optional[str] = None):
        """Run complete workflow."""
        start_time = datetime.now()
        
        # Phase 1
        if not self.run_phase1():
            print("\n❌ Workflow aborted at Phase 1")
            return False
        
        # Phase 2
        if not self.run_phase2():
            print("\n❌ Workflow aborted at Phase 2")
            return False
        
        # Phase 3
        if not self.run_phase3(user_prefs):
            print("\n❌ Workflow aborted at Phase 3")
            return False
        
        # Summary
        self.generate_summary_report()
        
        # Duration
        duration = datetime.now() - start_time
        print(f"\n⏱️  Total duration: {duration.total_seconds():.1f}s")
        print(f"\n✅ Complete workflow finished successfully!")
        print(f"🎯 Results ready for integration into Job Seek app\n")
        
        return True


def main():
    """Main entry point."""
    if len(sys.argv) < 4:
        print("Usage: python run_job_search.py <job_title> <city> <region> [--limit N] [--prefs FILE]")
        print()
        print("Examples:")
        print("  python run_job_search.py \"Product Designer\" \"Lille\" \"Hauts-de-France\"")
        print("  python run_job_search.py \"Product Manager\" \"Lyon\" \"Auvergne-Rhône-Alpes\" --limit 20")
        print("  python run_job_search.py \"Data Analyst\" \"Paris\" \"Île-de-France\" --prefs user_prefs.json")
        return
    
    job_title = sys.argv[1]
    city = sys.argv[2]
    region = sys.argv[3]
    
    # Parse optional arguments
    limit = 10
    user_prefs = None
    
    i = 4
    while i < len(sys.argv):
        if sys.argv[i] == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == "--prefs" and i + 1 < len(sys.argv):
            user_prefs = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    
    # Run orchestrator
    orchestrator = JobSearchOrchestrator(job_title, city, region, limit)
    orchestrator.run(user_prefs)


if __name__ == "__main__":
    main()
