#!/usr/bin/env python3
"""
Phase 3: Job Scoring with V2 System

Reads Phase 2 jobs, applies V2 scoring (100 points across 6 categories),
calculates match threshold (≥40 = matched, <40 = unmatched).

Input: phase2_jobs.json
Output: phase3_scored.json, phase3_scored.csv
"""

import json
import csv
import re
from pathlib import Path
from typing import Dict, List, Optional


class JobScorer:
    """Applies V2 scoring system to jobs."""
    
    def __init__(self, user_preferences: Optional[Dict] = None):
        """
        Initialize scorer with user preferences.
        
        Args:
            user_preferences: User preferences dict with:
                - preferred_city: str
                - target_seniority: "junior"|"pm"|"senior"|"head"
                - min_salary: int
                - priority_skills: List[str]
                - cv_skills: List[str]
                - trusted_sources: Dict[str, bool]
        """
        self.prefs = user_preferences or self._default_preferences()
    
    def _default_preferences(self) -> Dict:
        """Default preferences for testing."""
        return {
            "preferred_city": "lille",
            "target_seniority": "senior",
            "min_salary": 60000,
            "priority_skills": ["python", "ai", "ml", "product strategy", "agile", "scrum"],
            "cv_skills": ["api", "rest", "sql", "analytics", "data", "product management"],
            "trusted_sources": {
                "linkedin": True,
                "glassdoor": True,
                "indeed": False,
                "wttj": True
            }
        }
    
    def score_role(self, job: Dict) -> Dict:
        """Score role/seniority (35 points max)."""
        title = job.get("title", "").lower()
        
        # Detection patterns (order matters: Head → Senior → PM → Junior)
        if any(kw in title for kw in ["head of product", "vp product", "director of product", "cpo"]):
            level = "head"
            points = 35
            label = "Head/VP"
        elif any(kw in title for kw in ["senior product manager", "sr. pm", "sr pm", "lead pm", "staff pm"]):
            level = "senior"
            points = 25
            label = "Senior"
        elif any(kw in title for kw in ["product manager", "product owner", " pm "]):
            level = "pm"
            points = 15
            label = "PM"
        elif any(kw in title for kw in ["junior product manager", "associate pm", "apm", "product analyst"]):
            level = "junior"
            points = 8
            label = "Junior"
        else:
            level = "unknown"
            points = 0
            label = "Unknown"
        
        # Check if matches target
        target = self.prefs.get("target_seniority", "senior")
        matches_target = (level == target)
        
        return {
            "points": points,
            "max": 35,
            "level": level,
            "label": label,
            "matches_target": matches_target,
            "details": f"{label} {'✓' if matches_target else '(target: ' + target + ')'}"
        }
    
    def score_geography(self, job: Dict) -> Dict:
        """Score geography/remote (25 points max)."""
        location = job.get("location", "").lower()
        is_remote = job.get("is_remote", False)
        is_target_city = job.get("is_target_city", False)
        preferred_city = self.prefs.get("preferred_city", "lille").lower()
        
        # Determine scenario
        if is_remote and (is_target_city or "remote" in location):
            points = 25
            geo_type = "full_remote"
            details = "Full remote 🏠"
        elif is_target_city and is_remote:
            points = 22
            geo_type = "hybrid_preferred"
            details = f"Hybrid in {preferred_city.title()} 🏠🏢"
        elif is_target_city:
            points = 20
            geo_type = "office_preferred"
            details = f"Office in {preferred_city.title()} 🏢"
        elif is_remote:
            points = 15
            geo_type = "hybrid_other"
            details = "Hybrid other city 🏠🏢"
        else:
            points = 10
            geo_type = "office_other"
            details = "Office other city 🏢"
        
        return {
            "points": points,
            "max": 25,
            "type": geo_type,
            "details": details
        }
    
    def score_salary(self, job: Dict) -> Dict:
        """Score salary (15 points max)."""
        salary_str = job.get("salary")
        
        if not salary_str:
            return {
                "points": 7,
                "max": 15,
                "salary": None,
                "details": "Not disclosed (neutral)"
            }
        
        # Extract numeric value
        numbers = re.findall(r'\d+', salary_str.replace(' ', '').replace(',', ''))
        if not numbers:
            return {
                "points": 7,
                "max": 15,
                "salary": None,
                "details": "Not disclosed (neutral)"
            }
        
        # Take first number (or average if range)
        if len(numbers) >= 2:
            salary = (int(numbers[0]) + int(numbers[1])) / 2
        else:
            salary = int(numbers[0])
        
        # Handle "k" notation (50k = 50000)
        if salary < 1000:
            salary = salary * 1000
        
        # Linear interpolation
        if salary >= 80000:
            points = 15
        elif salary >= 60000:
            # 10-15 points for 60k-80k
            points = 10 + ((salary - 60000) / 20000) * 5
        elif salary >= 50000:
            # 5-10 points for 50k-60k
            points = 5 + ((salary - 50000) / 10000) * 5
        else:
            # 0-5 points for <50k
            points = max(0, (salary / 50000) * 5)
        
        return {
            "points": round(points, 1),
            "max": 15,
            "salary": int(salary),
            "details": f"€{int(salary/1000)}k"
        }
    
    def score_skills(self, job: Dict) -> Dict:
        """Score skills match (20 points max)."""
        # Get user skills
        user_skills = set(
            [s.lower() for s in self.prefs.get("priority_skills", [])] +
            [s.lower() for s in self.prefs.get("cv_skills", [])]
        )
        
        # Get job skills from list and description
        job_skills = job.get("skills", [])
        if isinstance(job_skills, str):
            job_skills = [s.strip() for s in job_skills.split(',')]
        
        job_skills_text = ' '.join(job_skills).lower()
        description = job.get("description", "").lower()
        combined_job_text = job_skills_text + ' ' + description
        
        # Count matches
        matched_skills = []
        for skill in user_skills:
            if skill in combined_job_text:
                matched_skills.append(skill)
        
        matched_count = len(matched_skills)
        
        # Calculate points
        if matched_count >= 10:
            points = 20
        elif matched_count >= 5:
            # 15-20 for 5-9 matches
            points = 15 + ((matched_count - 5) / 4) * 5
        elif matched_count >= 2:
            # 10-15 for 2-4 matches
            points = 10 + ((matched_count - 2) / 2) * 5
        else:
            # 0-10 for <2 matches
            points = (matched_count / 2) * 10
        
        # Format matched skills for display (show first 3 + count)
        if len(matched_skills) <= 3:
            skills_display = ', '.join(matched_skills[:3])
        else:
            skills_display = f"{', '.join(matched_skills[:3])} (+{len(matched_skills)-3} more)"
        
        return {
            "points": round(points, 1),
            "max": 20,
            "matched": matched_count,
            "matched_skills": matched_skills[:5],  # Keep first 5 for JSON
            "details": skills_display if matched_count > 0 else "No matches"
        }
    
    def score_attractiveness(self, job: Dict) -> Dict:
        """Score attractiveness (10 points max)."""
        title = job.get("title", "").lower()
        company = job.get("company", "").lower()
        description = job.get("description", "").lower()
        
        combined = f"{title} {company} {description}"
        
        # High keywords (10 points)
        high_keywords = [
            "ai", "ml", "machine learning", "climate", "sustainability",
            "impact", "healthtech", "biotech", "unicorn", "series b", "series c"
        ]
        
        # Medium keywords (6 points)
        medium_keywords = [
            "startup", "scale-up", "scale up", "series a", "fintech",
            "edtech", "fast-growing", "fast growing", "innovative"
        ]
        
        # Check for matches
        matched_high = [kw for kw in high_keywords if kw in combined]
        matched_medium = [kw for kw in medium_keywords if kw in combined]
        
        if matched_high:
            points = 10
            level = "high"
            details = f"Mission-driven: {', '.join(matched_high[:2])}"
        elif matched_medium:
            points = 6
            level = "medium"
            details = f"Growing startup: {', '.join(matched_medium[:2])}"
        else:
            points = 2
            level = "low"
            details = "Regular company"
        
        return {
            "points": points,
            "max": 10,
            "level": level,
            "matched_keywords": (matched_high or matched_medium)[:3],
            "details": details
        }
    
    def score_penalties(self, job: Dict) -> Dict:
        """Calculate penalties (-10 max)."""
        penalties = []
        total_penalty = 0
        
        # No posting date (-5)
        if not job.get("posted_date"):
            penalties.append("No posting date (-5)")
            total_penalty -= 5
        
        # Short description (-3)
        description = job.get("description", "")
        if len(description) < 100:
            penalties.append("Short description (-3)")
            total_penalty -= 3
        
        # Untrusted source (-2)
        platform = job.get("platform", "").lower()
        trusted_sources = self.prefs.get("trusted_sources", {})
        if platform in trusted_sources and not trusted_sources[platform]:
            penalties.append(f"Untrusted source: {platform} (-2)")
            total_penalty -= 2
        
        return {
            "points": max(total_penalty, -10),  # Cap at -10
            "max": -10,
            "reasons": penalties,
            "details": '; '.join(penalties) if penalties else "None"
        }
    
    def score_job(self, job: Dict) -> Dict:
        """Calculate complete V2 score for a job."""
        # Calculate each category
        role = self.score_role(job)
        geography = self.score_geography(job)
        salary = self.score_salary(job)
        skills = self.score_skills(job)
        attractiveness = self.score_attractiveness(job)
        penalties = self.score_penalties(job)
        
        # Calculate total
        total_score = (
            role["points"] +
            geography["points"] +
            salary["points"] +
            skills["points"] +
            attractiveness["points"] +
            penalties["points"]
        )
        
        # Determine match status
        is_matched = total_score >= 40
        match_tag = "✅ Match" if is_matched else "📋 À revoir"
        
        return {
            "job_id": job.get("url"),  # Use URL as unique ID
            "score": round(total_score, 1),
            "is_matched": is_matched,
            "match_tag": match_tag,
            "breakdown": {
                "role": role,
                "geography": geography,
                "salary": salary,
                "skills": skills,
                "attractiveness": attractiveness,
                "penalties": penalties
            },
            # Keep original job data
            "job_data": job
        }


def load_phase2_jobs(filepath: str) -> List[Dict]:
    """Load jobs from Phase 2 JSON."""
    with open(filepath, 'r') as f:
        return json.load(f)


def save_json(data: List[Dict], filepath: str):
    """Save scored jobs to JSON."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_csv(data: List[Dict], filepath: str):
    """Save scored jobs to CSV."""
    if not data:
        return
    
    # Flatten for CSV
    rows = []
    for item in data:
        job = item["job_data"]
        breakdown = item["breakdown"]
        
        row = {
            "score": item["score"],
            "match_tag": item["match_tag"],
            "title": job.get("title"),
            "company": job.get("company"),
            "location": job.get("location"),
            "location_tag": job.get("location_tag"),
            "salary": job.get("salary"),
            "contract_type": job.get("contract_type"),
            "platform": job.get("platform"),
            "url": job.get("url"),
            # Score breakdown
            "role_points": breakdown["role"]["points"],
            "role_level": breakdown["role"]["label"],
            "geo_points": breakdown["geography"]["points"],
            "geo_type": breakdown["geography"]["type"],
            "salary_points": breakdown["salary"]["points"],
            "skills_points": breakdown["skills"]["points"],
            "skills_matched": breakdown["skills"]["matched"],
            "attractiveness_points": breakdown["attractiveness"]["points"],
            "attractiveness_level": breakdown["attractiveness"]["level"],
            "penalties": breakdown["penalties"]["points"],
        }
        rows.append(row)
    
    # Write CSV
    columns = list(rows[0].keys())
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main():
    """Main scoring function."""
    import sys
    
    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage: python score_jobs.py <phase2_json_path> [user_prefs_json]")
        print("Example: python score_jobs.py phase2_jobs.json")
        print("         python score_jobs.py results/phase2_jobs.json user_preferences.json")
        return
    
    phase2_file = sys.argv[1]
    prefs_file = sys.argv[2] if len(sys.argv) >= 3 else None
    
    # Check input
    if not Path(phase2_file).exists():
        print(f"❌ Error: {phase2_file} not found!")
        print("Run Phase 2 first (extract_job_details.py)")
        return
    
    # Load user preferences if provided
    user_prefs = None
    if prefs_file and Path(prefs_file).exists():
        with open(prefs_file, 'r') as f:
            user_prefs = json.load(f)
        print(f"📋 Loaded user preferences from {prefs_file}")
    else:
        print("📋 Using default preferences (Product Manager, Senior, Lille)")
    
    print(f"{'='*60}")
    print("PHASE 3: JOB SCORING (V2 SYSTEM)")
    print(f"{'='*60}")
    print(f"Input: {phase2_file}")
    print()
    
    # Load jobs
    jobs = load_phase2_jobs(phase2_file)
    print(f"📊 Loaded {len(jobs)} jobs from Phase 2\n")
    
    # Score all jobs
    scorer = JobScorer(user_prefs)
    scored_jobs = []
    
    for i, job in enumerate(jobs, 1):
        print(f"[{i}/{len(jobs)}] Scoring: {job.get('title', 'Unknown')[:50]}...")
        scored = scorer.score_job(job)
        scored_jobs.append(scored)
    
    # Sort by score (descending)
    scored_jobs.sort(key=lambda x: x["score"], reverse=True)
    
    # Summary
    print(f"\n{'='*60}")
    print("SCORING SUMMARY")
    print(f"{'='*60}")
    
    matched = [j for j in scored_jobs if j["is_matched"]]
    unmatched = [j for j in scored_jobs if not j["is_matched"]]
    
    print(f"\n✅ Matched (score ≥ 40): {len(matched)} ({len(matched)/len(scored_jobs)*100:.1f}%)")
    print(f"📋 À revoir (score < 40): {len(unmatched)} ({len(unmatched)/len(scored_jobs)*100:.1f}%)")
    
    # Score distribution
    print(f"\n📊 Score Distribution:")
    print(f"   Top score: {scored_jobs[0]['score']}")
    print(f"   Avg matched: {sum(j['score'] for j in matched) / len(matched):.1f}" if matched else "   Avg matched: N/A")
    print(f"   Avg unmatched: {sum(j['score'] for j in unmatched) / len(unmatched):.1f}" if unmatched else "   Avg unmatched: N/A")
    
    # Top 5 jobs
    print(f"\n🏆 Top 5 Jobs:")
    for i, job in enumerate(scored_jobs[:5], 1):
        data = job["job_data"]
        print(f"   {i}. {data.get('title', 'Unknown')[:40]} - {data.get('company', 'Unknown')[:20]}")
        print(f"      Score: {job['score']} | {data.get('location_tag')} | {data.get('platform')}")
    
    # Save outputs
    output_dir = Path(phase2_file).parent
    json_path = output_dir / "phase3_scored.json"
    csv_path = output_dir / "phase3_scored.csv"
    
    save_json(scored_jobs, str(json_path))
    save_csv(scored_jobs, str(csv_path))
    
    print(f"\n💾 Outputs saved:")
    print(f"   JSON: {json_path}")
    print(f"   CSV: {csv_path}")
    
    print(f"\n✅ Phase 3 complete!")
    print(f"🎯 Ready for integration into Job Seek app")


if __name__ == "__main__":
    main()
