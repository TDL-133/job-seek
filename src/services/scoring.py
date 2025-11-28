from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher
import re


class ScoringService:
    """
    Service for calculating job match scores based on user criteria.
    
    Formula: Σ(criterion_score × importance) / Σ(importance)
    Only enabled criteria are considered.
    """
    
    def calculate_job_score(
        self,
        job: Dict[str, Any],
        profile: Dict[str, Any],
        criteria: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate overall score for a job based on user profile and criteria.
        
        Returns:
            {
                "score": 0-100,
                "breakdown": {
                    "job_title": {"score": 80, "weight": 100, "details": "..."},
                    "location": {"score": 90, "weight": 80, "details": "..."},
                    ...
                }
            }
        """
        total_weighted_score = 0
        total_weight = 0
        breakdown = {}
        
        for criterion in criteria:
            if not criterion.get("enabled", False):
                continue
            
            criteria_type = criterion.get("criteria_type")
            importance = criterion.get("importance", 50)
            sub_criteria = criterion.get("sub_criteria", {})
            
            # Calculate score for this criterion
            score_result = self._calculate_criterion_score(
                criteria_type, job, profile, sub_criteria
            )
            
            score = score_result.get("score", 0)
            details = score_result.get("details", "")
            
            # Weighted contribution
            total_weighted_score += score * importance
            total_weight += importance
            
            breakdown[criteria_type] = {
                "score": score,
                "weight": importance,
                "details": details
            }
        
        # Calculate final score
        final_score = 0
        if total_weight > 0:
            final_score = round(total_weighted_score / total_weight, 1)
        
        return {
            "score": final_score,
            "breakdown": breakdown
        }
    
    def _calculate_criterion_score(
        self,
        criteria_type: str,
        job: Dict[str, Any],
        profile: Dict[str, Any],
        sub_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate score for a specific criterion type."""
        
        calculators = {
            "job_title": self._score_job_title,
            "location": self._score_location,
            "contract_type": self._score_contract_type,
            "salary": self._score_salary,
            "work_mode": self._score_work_mode,
            "company_size": self._score_company_size,
            "seniority": self._score_seniority,
            "skills": self._score_skills,
            "languages": self._score_languages,
            "values": self._score_values,
        }
        
        calculator = calculators.get(criteria_type)
        if calculator:
            return calculator(job, profile, sub_criteria)
        
        return {"score": 50, "details": "Unknown criterion type"}
    
    def _score_job_title(
        self,
        job: Dict[str, Any],
        profile: Dict[str, Any],
        sub_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Score job title match using fuzzy matching."""
        job_title = (job.get("title") or "").lower()
        
        # Get target titles from sub_criteria custom list or profile
        target_titles = []
        
        # From sub_criteria
        for item in sub_criteria.get("custom", []):
            if item.get("enabled", True):
                target_titles.append(item.get("name", "").lower())
        
        # From profile
        if profile.get("latest_job_title"):
            target_titles.append(profile.get("latest_job_title", "").lower())
        
        if not target_titles or not job_title:
            return {"score": 50, "details": "No target titles configured"}
        
        # Calculate best match
        best_score = 0
        best_match = ""
        
        for target in target_titles:
            # Fuzzy match
            ratio = SequenceMatcher(None, job_title, target).ratio()
            
            # Also check if target is contained in job title
            if target in job_title:
                ratio = max(ratio, 0.85)
            
            if ratio > best_score:
                best_score = ratio
                best_match = target
        
        score = round(best_score * 100)
        
        return {
            "score": score,
            "details": f"Best match: '{best_match}' ({score}%)"
        }
    
    def _score_location(
        self,
        job: Dict[str, Any],
        profile: Dict[str, Any],
        sub_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Score location match."""
        job_location = (job.get("location") or "").lower()
        target_location = (sub_criteria.get("value") or profile.get("preferred_location") or "").lower()
        
        if not target_location:
            return {"score": 100, "details": "No location preference set"}
        
        if not job_location:
            return {"score": 50, "details": "Job location not specified"}
        
        # Check for remote
        if "remote" in job_location or job.get("remote_type") == "remote":
            return {"score": 100, "details": "Remote job - location flexible"}
        
        # Check if same city
        if target_location in job_location:
            return {"score": 100, "details": f"Location match: {job_location}"}
        
        # Partial match (same country)
        common_words = set(target_location.split()) & set(job_location.split())
        if common_words:
            return {"score": 70, "details": f"Partial match: {', '.join(common_words)}"}
        
        return {"score": 30, "details": f"Different location: {job_location}"}
    
    def _score_contract_type(
        self,
        job: Dict[str, Any],
        profile: Dict[str, Any],
        sub_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Score contract type match."""
        job_type = (job.get("job_type") or "").lower()
        
        # Map common job types
        type_mapping = {
            "full-time": ["cdi", "permanent", "full-time", "full time"],
            "contract": ["cdd", "contract", "temporary"],
            "freelance": ["freelance", "contractor", "consultant"],
            "internship": ["stage", "internship", "intern"],
        }
        
        # Get enabled options
        enabled_types = []
        best_importance = 0
        
        for option in sub_criteria.get("options", []):
            if option.get("enabled"):
                name = option.get("name", "").lower()
                enabled_types.append(name)
                # Track best match importance
                for key, values in type_mapping.items():
                    if name in values or any(v in name for v in values):
                        if any(v in job_type for v in values):
                            best_importance = max(best_importance, option.get("importance", 50))
        
        if not enabled_types:
            return {"score": 100, "details": "No contract type preference"}
        
        if not job_type:
            return {"score": 50, "details": "Contract type not specified"}
        
        # Check match
        for option in sub_criteria.get("options", []):
            if not option.get("enabled"):
                continue
            name = option.get("name", "").lower()
            
            for key, values in type_mapping.items():
                if name in values or any(v in name for v in values):
                    if any(v in job_type for v in values):
                        return {
                            "score": option.get("importance", 80),
                            "details": f"Contract match: {name}"
                        }
        
        return {"score": 30, "details": f"Contract type: {job_type}"}
    
    def _score_salary(
        self,
        job: Dict[str, Any],
        profile: Dict[str, Any],
        sub_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Score salary match."""
        min_salary = sub_criteria.get("min_value")
        job_salary_min = job.get("salary_min")
        job_salary_max = job.get("salary_max")
        
        if not min_salary:
            return {"score": 100, "details": "No salary requirement set"}
        
        if not job_salary_min and not job_salary_max:
            return {"score": 50, "details": "Salary not disclosed"}
        
        job_salary = job_salary_max or job_salary_min or 0
        
        if job_salary >= min_salary:
            # Bonus for higher salary
            bonus = min(20, (job_salary - min_salary) / min_salary * 100)
            score = min(100, 80 + bonus)
            return {"score": round(score), "details": f"Salary {job_salary}€ >= {min_salary}€"}
        else:
            # Penalty for lower salary
            ratio = job_salary / min_salary
            score = max(0, ratio * 70)
            return {"score": round(score), "details": f"Salary {job_salary}€ < {min_salary}€"}
    
    def _score_work_mode(
        self,
        job: Dict[str, Any],
        profile: Dict[str, Any],
        sub_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Score work mode match (remote, hybrid, onsite)."""
        job_remote = (job.get("remote_type") or "").lower()
        
        if not job_remote:
            # Try to infer from location
            location = (job.get("location") or "").lower()
            if "remote" in location:
                job_remote = "remote"
            elif "hybrid" in location:
                job_remote = "hybrid"
        
        if not job_remote:
            return {"score": 50, "details": "Work mode not specified"}
        
        # Check options
        for option in sub_criteria.get("options", []):
            if not option.get("enabled"):
                continue
            name = option.get("name", "").lower()
            
            if name in job_remote or job_remote in name:
                return {
                    "score": option.get("importance", 80),
                    "details": f"Work mode match: {job_remote}"
                }
        
        return {"score": 40, "details": f"Work mode: {job_remote}"}
    
    def _score_company_size(
        self,
        job: Dict[str, Any],
        profile: Dict[str, Any],
        sub_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Score company size preference."""
        # Would need company info from job
        company = job.get("company", {})
        company_size = company.get("company_size", "").lower() if isinstance(company, dict) else ""
        
        if not company_size:
            return {"score": 50, "details": "Company size unknown"}
        
        size_mapping = {
            "startup": ["startup", "1-10", "11-50", "early stage"],
            "scale-up": ["scale-up", "scaleup", "51-200", "201-500"],
            "pme": ["pme", "sme", "medium", "501-1000"],
            "grand groupe": ["enterprise", "large", "1000+", "5000+", "grand groupe"],
        }
        
        for option in sub_criteria.get("options", []):
            if not option.get("enabled"):
                continue
            name = option.get("name", "").lower()
            
            for key, values in size_mapping.items():
                if name in key or key in name:
                    if any(v in company_size for v in values):
                        return {
                            "score": option.get("importance", 70),
                            "details": f"Company size match: {company_size}"
                        }
        
        return {"score": 50, "details": f"Company size: {company_size}"}
    
    def _score_seniority(
        self,
        job: Dict[str, Any],
        profile: Dict[str, Any],
        sub_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Score seniority level match."""
        job_level = (job.get("experience_level") or "").lower()
        job_title = (job.get("title") or "").lower()
        
        # Try to infer from title if not specified
        if not job_level:
            if any(x in job_title for x in ["senior", "sr.", "lead", "principal"]):
                job_level = "senior"
            elif any(x in job_title for x in ["junior", "jr.", "entry"]):
                job_level = "junior"
            elif "mid" in job_title:
                job_level = "mid"
        
        if not job_level:
            return {"score": 50, "details": "Seniority level not specified"}
        
        level_mapping = {
            "junior": ["junior", "entry", "jr.", "stage"],
            "mid": ["mid", "intermediate"],
            "senior": ["senior", "sr.", "experienced"],
            "lead": ["lead", "principal", "staff", "architect"],
        }
        
        for option in sub_criteria.get("options", []):
            if not option.get("enabled"):
                continue
            name = option.get("name", "").lower()
            
            for key, values in level_mapping.items():
                if name in key or key in name:
                    if any(v in job_level for v in values):
                        return {
                            "score": option.get("importance", 80),
                            "details": f"Seniority match: {job_level}"
                        }
        
        return {"score": 40, "details": f"Seniority: {job_level}"}
    
    def _score_skills(
        self,
        job: Dict[str, Any],
        profile: Dict[str, Any],
        sub_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Score skills match."""
        job_skills = set(s.lower() for s in (job.get("skills") or []))
        job_desc = (job.get("description") or "").lower()
        
        # Get user skills from profile and custom sub_criteria
        user_skills = set(s.lower() for s in (profile.get("skills") or []))
        
        for item in sub_criteria.get("custom", []):
            if item.get("enabled", True):
                user_skills.add(item.get("name", "").lower())
        
        if not user_skills:
            return {"score": 50, "details": "No skills configured"}
        
        if not job_skills and not job_desc:
            return {"score": 50, "details": "Job skills not specified"}
        
        # Count matches
        matches = []
        for skill in user_skills:
            if skill in job_skills or skill in job_desc:
                matches.append(skill)
        
        if not matches:
            return {"score": 30, "details": "No skill matches found"}
        
        match_ratio = len(matches) / len(user_skills)
        score = round(30 + match_ratio * 70)  # 30-100 range
        
        return {
            "score": score,
            "details": f"Skills matched: {', '.join(matches[:5])}" + 
                       (f"... (+{len(matches)-5})" if len(matches) > 5 else "")
        }
    
    def _score_languages(
        self,
        job: Dict[str, Any],
        profile: Dict[str, Any],
        sub_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Score language requirements match."""
        job_desc = (job.get("description") or "").lower()
        
        # Get required languages from sub_criteria
        required_langs = []
        for item in sub_criteria.get("custom", []):
            if item.get("enabled", True):
                required_langs.append(item.get("name", "").lower())
        
        if not required_langs:
            return {"score": 100, "details": "No language requirement set"}
        
        # Check if job mentions these languages
        matches = [lang for lang in required_langs if lang in job_desc]
        
        if len(matches) == len(required_langs):
            return {"score": 100, "details": f"All languages mentioned: {', '.join(matches)}"}
        elif matches:
            score = 50 + (len(matches) / len(required_langs)) * 50
            return {"score": round(score), "details": f"Some languages mentioned: {', '.join(matches)}"}
        
        return {"score": 60, "details": "Language requirements not mentioned in job"}
    
    def _score_values(
        self,
        job: Dict[str, Any],
        profile: Dict[str, Any],
        sub_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Score company values match."""
        job_desc = (job.get("description") or "").lower()
        company = job.get("company", {})
        culture_keywords = company.get("culture_keywords", []) if isinstance(company, dict) else []
        
        all_text = job_desc + " " + " ".join(str(k).lower() for k in culture_keywords)
        
        value_keywords = {
            "impact": ["impact", "meaningful", "purpose", "mission"],
            "innovation": ["innovation", "innovative", "cutting-edge", "disrupt"],
            "bienveillance": ["bienveillance", "caring", "supportive", "wellbeing", "well-being"],
            "flexibilité": ["flexible", "flexibility", "work-life", "balance"],
        }
        
        matches = []
        total_importance = 0
        matched_importance = 0
        
        for option in sub_criteria.get("options", []):
            if not option.get("enabled"):
                continue
            
            name = option.get("name", "").lower()
            importance = option.get("importance", 50)
            total_importance += importance
            
            keywords = value_keywords.get(name, [name])
            if any(kw in all_text for kw in keywords):
                matches.append(name)
                matched_importance += importance
        
        # Also check custom values
        for item in sub_criteria.get("custom", []):
            if item.get("enabled", True):
                name = item.get("name", "").lower()
                importance = item.get("importance", 50)
                total_importance += importance
                
                if name in all_text:
                    matches.append(name)
                    matched_importance += importance
        
        if total_importance == 0:
            return {"score": 100, "details": "No values configured"}
        
        score = round((matched_importance / total_importance) * 100)
        
        if matches:
            return {"score": max(50, score), "details": f"Values found: {', '.join(matches)}"}
        
        return {"score": 40, "details": "Company values not mentioned"}
