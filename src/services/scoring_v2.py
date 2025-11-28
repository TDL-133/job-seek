"""
Job Scoring Service V2 - Fixed Point System for Product Manager Jobs

Categories (100 pts max + penalties):
- Role/Seniority: 35 pts
- Geography/Remote: 25 pts
- Salary: 15 pts
- Skills Match: 20 pts
- Attractiveness: 10 pts
- Penalties: -10 pts max
"""

from typing import Dict, Any, List, Optional, Tuple
import re


class ScoringServiceV2:
    """
    Fixed-point scoring system for job matching.
    Total possible: 100 points (with up to -10 penalty)
    """
    
    # Point allocations
    MAX_ROLE_POINTS = 35
    MAX_GEO_POINTS = 25
    MAX_SALARY_POINTS = 15
    MAX_SKILLS_POINTS = 20
    MAX_ATTRACTIVENESS_POINTS = 10
    MAX_PENALTY_POINTS = -10
    
    # Seniority detection patterns (checked in order: Head → Senior → PM → Junior)
    SENIORITY_PATTERNS = {
        "head": {
            "patterns": [
                r"\bhead\s+of\s+product\b",
                r"\bvp\s+of?\s+product\b",
                r"\bvice\s+president.*product\b",
                r"\bdirector\s+of\s+product\b",
                r"\bchief\s+product\s+officer\b",
                r"\bcpo\b",
                r"\bproduct\s+director\b",
            ],
            "points": 35,
            "label": "Head/VP"
        },
        "senior": {
            "patterns": [
                r"\bsenior\s+product\s+manager\b",
                r"\bsr\.?\s+product\s+manager\b",
                r"\bstaff\s+product\s+manager\b",
                r"\bprincipal\s+product\s+manager\b",
                r"\blead\s+product\s+manager\b",
                r"\bproduct\s+lead\b",
            ],
            "points": 25,
            "label": "Senior"
        },
        "mid": {
            "patterns": [
                r"\bproduct\s+manager\b",
                r"\bproduct\s+owner\b",
                r"\bpm\b",
            ],
            "points": 15,
            "label": "PM"
        },
        "junior": {
            "patterns": [
                r"\bjunior\s+product\s+manager\b",
                r"\bjr\.?\s+product\s+manager\b",
                r"\bassociate\s+product\s+manager\b",
                r"\bapm\b",
                r"\bproduct\s+analyst\b",
            ],
            "points": 8,
            "label": "Junior"
        }
    }
    
    # Attractiveness keywords
    DEFAULT_ATTRACTIVENESS_KEYWORDS = {
        "high": [  # 10 pts - Mission-driven / Hot tech
            "ai", "artificial intelligence", "machine learning", "ml",
            "climate", "sustainability", "impact", "mission-driven",
            "healthtech", "medtech", "biotech", "greentech",
            "series b", "series c", "unicorn",
        ],
        "medium": [  # 6 pts - Growing startup
            "series a", "startup", "scale-up", "scaleup",
            "fintech", "edtech", "proptech",
            "fast-growing", "hypergrowth", "high-growth",
            "innovative", "disruptive",
        ],
        "low": [  # 2 pts - Regular company (default)
        ]
    }
    
    def calculate_total_score(
        self,
        job: Dict[str, Any],
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate total job score based on user preferences.
        
        Args:
            job: Job data dict with title, location, salary_min, salary_max, 
                 description, remote_type, source, posted_at, skills
            preferences: User preferences with preferred_city, min_salary,
                        target_seniority, priority_skills, cv_skills,
                        trusted_sources, attractiveness_keywords
        
        Returns:
            {
                "score": 0-100,
                "breakdown": {
                    "role": {"points": 25, "max": 35, "level": "Senior", "details": "..."},
                    "geography": {"points": 25, "max": 25, "details": "Full remote"},
                    "salary": {"points": 10, "max": 15, "details": "€60k"},
                    "skills": {"points": 15, "max": 20, "matched": 5, "details": "..."},
                    "attractiveness": {"points": 6, "max": 10, "details": "..."},
                    "penalties": {"points": -5, "reasons": ["No posting date"]}
                }
            }
        """
        breakdown = {}
        
        # 1. Role/Seniority (35 pts)
        role_result = self.score_role_seniority(
            job.get("title", ""),
            preferences.get("target_seniority")
        )
        breakdown["role"] = role_result
        
        # 2. Geography (25 pts)
        geo_result = self.score_geography(
            job.get("location", ""),
            job.get("remote_type", ""),
            preferences.get("preferred_city", "")
        )
        breakdown["geography"] = geo_result
        
        # 3. Salary (15 pts)
        salary_result = self.score_salary(
            job.get("salary_min"),
            job.get("salary_max"),
            preferences.get("min_salary")
        )
        breakdown["salary"] = salary_result
        
        # 4. Skills (20 pts)
        all_user_skills = list(set(
            (preferences.get("cv_skills") or []) + 
            (preferences.get("priority_skills") or [])
        ))
        skills_result = self.score_skills_match(
            job.get("skills") or [],
            job.get("description", ""),
            all_user_skills
        )
        breakdown["skills"] = skills_result
        
        # 5. Attractiveness (10 pts)
        attractiveness_result = self.score_attractiveness(
            job.get("description", ""),
            job.get("company", {}),
            preferences.get("attractiveness_keywords") or self.DEFAULT_ATTRACTIVENESS_KEYWORDS
        )
        breakdown["attractiveness"] = attractiveness_result
        
        # 6. Penalties (-10 pts max)
        penalties_result = self.calculate_penalties(
            job,
            preferences.get("trusted_sources") or {}
        )
        breakdown["penalties"] = penalties_result
        
        # Calculate total
        total_score = (
            role_result["points"] +
            geo_result["points"] +
            salary_result["points"] +
            skills_result["points"] +
            attractiveness_result["points"] +
            penalties_result["points"]
        )
        
        # Clamp to 0-100
        total_score = max(0, min(100, total_score))
        
        return {
            "score": round(total_score, 1),
            "breakdown": breakdown
        }
    
    def score_role_seniority(
        self,
        job_title: str,
        target_seniority: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Score role/seniority level (35 pts max).
        
        Detection order: Head/VP → Senior → PM → Junior
        """
        title_lower = job_title.lower()
        
        detected_level = None
        detected_points = 0
        detected_label = "Unknown"
        
        # Check patterns in order of seniority (highest first)
        for level in ["head", "senior", "mid", "junior"]:
            config = self.SENIORITY_PATTERNS[level]
            for pattern in config["patterns"]:
                if re.search(pattern, title_lower):
                    detected_level = level
                    detected_points = config["points"]
                    detected_label = config["label"]
                    break
            if detected_level:
                break
        
        # If no match, give base points
        if not detected_level:
            detected_points = 8  # Same as junior
            detected_label = "Unknown"
        
        # Bonus if matches target seniority
        details = f"Detected: {detected_label}"
        if target_seniority and detected_level == target_seniority:
            details += " ✓ (matches target)"
        
        return {
            "points": detected_points,
            "max": self.MAX_ROLE_POINTS,
            "level": detected_level or "unknown",
            "label": detected_label,
            "details": details
        }
    
    def score_geography(
        self,
        job_location: str,
        remote_type: str,
        preferred_city: str
    ) -> Dict[str, Any]:
        """
        Score geography/remote (25 pts max).
        
        - Full remote anywhere → 25 pts
        - Office in preferred city → 20 pts
        - Office in distant city → 10 pts
        """
        location_lower = (job_location or "").lower()
        remote_lower = (remote_type or "").lower()
        city_lower = (preferred_city or "").lower()
        
        # Check for full remote
        is_remote = (
            "remote" in remote_lower or
            "remote" in location_lower or
            "télétravail" in location_lower or
            "full remote" in location_lower
        )
        
        is_hybrid = (
            "hybrid" in remote_lower or
            "hybride" in location_lower
        )
        
        if is_remote and not is_hybrid:
            return {
                "points": 25,
                "max": self.MAX_GEO_POINTS,
                "type": "remote",
                "details": "Full remote 🏠"
            }
        
        # Check if in preferred city
        if city_lower and city_lower in location_lower:
            points = 20 if not is_hybrid else 22  # Small bonus for hybrid in preferred city
            return {
                "points": min(25, points),
                "max": self.MAX_GEO_POINTS,
                "type": "local" if not is_hybrid else "hybrid_local",
                "details": f"In {preferred_city}" + (" (hybrid)" if is_hybrid else "")
            }
        
        # Hybrid in other city
        if is_hybrid:
            return {
                "points": 15,
                "max": self.MAX_GEO_POINTS,
                "type": "hybrid_distant",
                "details": f"Hybrid - {job_location or 'Unknown'}"
            }
        
        # Office in different city
        return {
            "points": 10,
            "max": self.MAX_GEO_POINTS,
            "type": "onsite_distant",
            "details": f"Office - {job_location or 'Unknown'}"
        }
    
    def score_salary(
        self,
        salary_min: Optional[int],
        salary_max: Optional[int],
        user_min_salary: Optional[int]
    ) -> Dict[str, Any]:
        """
        Score salary (15 pts max).
        
        - €50k → 5 pts
        - €60k → 10 pts  
        - €80k+ → 15 pts
        - Linear interpolation between ranges
        """
        # If no salary info, neutral score
        if not salary_min and not salary_max:
            return {
                "points": 7,  # Middle ground
                "max": self.MAX_SALARY_POINTS,
                "salary": None,
                "details": "Salary not disclosed"
            }
        
        # Use max salary if available, else min
        job_salary = salary_max or salary_min or 0
        
        # Calculate points based on ranges
        if job_salary >= 80000:
            points = 15
        elif job_salary >= 60000:
            # Linear from 60k (10pts) to 80k (15pts)
            points = 10 + (job_salary - 60000) / 20000 * 5
        elif job_salary >= 50000:
            # Linear from 50k (5pts) to 60k (10pts)
            points = 5 + (job_salary - 50000) / 10000 * 5
        else:
            # Below 50k
            points = max(0, job_salary / 50000 * 5)
        
        # Format salary for display
        salary_display = f"€{job_salary // 1000}k"
        if salary_min and salary_max and salary_min != salary_max:
            salary_display = f"€{salary_min // 1000}k - €{salary_max // 1000}k"
        
        # Check against user minimum
        details = salary_display
        if user_min_salary:
            if job_salary >= user_min_salary:
                details += " ✓"
            else:
                details += f" (below €{user_min_salary // 1000}k target)"
        
        return {
            "points": round(points, 1),
            "max": self.MAX_SALARY_POINTS,
            "salary": job_salary,
            "details": details
        }
    
    def score_skills_match(
        self,
        job_skills: List[str],
        job_description: str,
        user_skills: List[str]
    ) -> Dict[str, Any]:
        """
        Score skills match (20 pts max).
        
        - 2 skills matched → 10 pts
        - 5 skills matched → 15 pts
        - 10+ skills matched → 20 pts
        """
        if not user_skills:
            return {
                "points": 10,  # Default
                "max": self.MAX_SKILLS_POINTS,
                "matched": 0,
                "matched_skills": [],
                "details": "No skills configured"
            }
        
        # Normalize for comparison
        job_skills_lower = set(s.lower().strip() for s in job_skills)
        desc_lower = (job_description or "").lower()
        user_skills_lower = [s.lower().strip() for s in user_skills]
        
        # Find matches
        matched = []
        for skill in user_skills_lower:
            if skill in job_skills_lower:
                matched.append(skill)
            elif skill in desc_lower:
                matched.append(skill)
        
        matched = list(set(matched))  # Dedupe
        match_count = len(matched)
        
        # Calculate points
        if match_count >= 10:
            points = 20
        elif match_count >= 5:
            # Linear from 5 (15pts) to 10 (20pts)
            points = 15 + (match_count - 5) / 5 * 5
        elif match_count >= 2:
            # Linear from 2 (10pts) to 5 (15pts)
            points = 10 + (match_count - 2) / 3 * 5
        else:
            # Less than 2 matches
            points = match_count * 5
        
        # Format details
        if matched:
            display_skills = matched[:3]
            details = ", ".join(display_skills)
            if len(matched) > 3:
                details += f" (+{len(matched) - 3} more)"
        else:
            details = "No matches found"
        
        return {
            "points": round(points, 1),
            "max": self.MAX_SKILLS_POINTS,
            "matched": match_count,
            "matched_skills": matched,
            "details": details
        }
    
    def score_attractiveness(
        self,
        job_description: str,
        company_info: Dict[str, Any],
        keywords: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """
        Score company attractiveness (10 pts max).
        
        - Regular company → 2 pts
        - Fast-growing startup → 6 pts
        - Mission-driven/AI company → 10 pts
        """
        desc_lower = (job_description or "").lower()
        
        # Also check company info if available
        company_desc = ""
        if isinstance(company_info, dict):
            company_desc = (
                (company_info.get("description") or "") + " " +
                (company_info.get("industry") or "")
            ).lower()
        
        all_text = desc_lower + " " + company_desc
        
        # Check high-value keywords (10 pts)
        high_keywords = keywords.get("high", self.DEFAULT_ATTRACTIVENESS_KEYWORDS["high"])
        high_matches = [kw for kw in high_keywords if kw.lower() in all_text]
        
        if high_matches:
            return {
                "points": 10,
                "max": self.MAX_ATTRACTIVENESS_POINTS,
                "level": "high",
                "matched_keywords": high_matches[:3],
                "details": f"Mission-driven: {', '.join(high_matches[:2])}"
            }
        
        # Check medium-value keywords (6 pts)
        medium_keywords = keywords.get("medium", self.DEFAULT_ATTRACTIVENESS_KEYWORDS["medium"])
        medium_matches = [kw for kw in medium_keywords if kw.lower() in all_text]
        
        if medium_matches:
            return {
                "points": 6,
                "max": self.MAX_ATTRACTIVENESS_POINTS,
                "level": "medium",
                "matched_keywords": medium_matches[:3],
                "details": f"Growing: {', '.join(medium_matches[:2])}"
            }
        
        # Default - regular company (2 pts)
        return {
            "points": 2,
            "max": self.MAX_ATTRACTIVENESS_POINTS,
            "level": "low",
            "matched_keywords": [],
            "details": "Regular company"
        }
    
    def calculate_penalties(
        self,
        job: Dict[str, Any],
        trusted_sources: Dict[str, bool]
    ) -> Dict[str, Any]:
        """
        Calculate penalties (-10 pts max).
        
        - No posting date → -5 pts
        - Short description (<100 chars) → -3 pts
        - Untrusted source → -2 pts
        """
        penalties = 0
        reasons = []
        
        # Check posting date
        posted_at = job.get("posted_at") or job.get("posted_date")
        if not posted_at:
            penalties -= 5
            reasons.append("No posting date (-5)")
        
        # Check description length
        description = job.get("description") or ""
        if len(description) < 100:
            penalties -= 3
            reasons.append("Short description (-3)")
        
        # Check source trust
        source = (job.get("source") or "").lower()
        if source and trusted_sources:
            # If source is explicitly marked as untrusted
            if source in trusted_sources and not trusted_sources[source]:
                penalties -= 2
                reasons.append(f"Untrusted source: {source} (-2)")
        
        # Cap at -10
        penalties = max(-10, penalties)
        
        return {
            "points": penalties,
            "max": self.MAX_PENALTY_POINTS,
            "reasons": reasons,
            "details": ", ".join(reasons) if reasons else "No penalties"
        }


# Singleton instance
scoring_service_v2 = ScoringServiceV2()
