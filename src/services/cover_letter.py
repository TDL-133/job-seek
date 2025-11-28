import os
import json
from typing import Dict, Any, Optional
import anthropic


ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


COVER_LETTER_PROMPT = """Tu es un expert en rédaction de lettres de motivation professionnelles. Génère une lettre de motivation personnalisée et percutante.

## Profil du candidat
{profile_data}

## Offre d'emploi
Poste: {job_title}
Entreprise: {company_name}
Description: {job_description}
Compétences requises: {job_skills}
Localisation: {job_location}

## Instructions
1. La lettre doit être authentique et personnelle, pas générique
2. Mets en avant les compétences du candidat qui correspondent au poste
3. Montre ta motivation pour cette entreprise spécifique
4. Structure: Accroche → Expérience pertinente → Motivation → Conclusion
5. Longueur: 250-350 mots maximum
6. Ton: Professionnel mais chaleureux
7. Si des valeurs d'entreprise sont connues, les intégrer subtilement

Génère la lettre directement, sans formule de politesse excessive.
Commence par "Madame, Monsieur," et termine par une formule de politesse courte.
"""


class CoverLetterService:
    """Service for generating personalized cover letters using Claude."""
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None
    
    async def generate_cover_letter(
        self,
        profile: Dict[str, Any],
        job: Dict[str, Any],
        company: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a personalized cover letter.
        
        Step 9 from PRD: Generate cover letter based on CV, description, and job.
        
        Args:
            profile: User profile with experiences, skills, ai_description
            job: Job data with title, description, company info
            company: Optional company data with values, culture
            
        Returns:
            Generated cover letter text
        """
        if not self.client:
            return self._get_mock_cover_letter(profile, job)
        
        # Build profile data for prompt
        profile_text = self._format_profile(profile)
        
        # Extract job details
        job_title = job.get("title", "Poste non spécifié")
        job_description = job.get("description", "")[:2000]  # Limit length
        job_skills = ", ".join(job.get("skills", [])) or "Non spécifiées"
        job_location = job.get("location", "Non spécifiée")
        
        # Get company name
        company_name = "l'entreprise"
        if company:
            company_name = company.get("name", "l'entreprise")
        elif isinstance(job.get("company"), dict):
            company_name = job["company"].get("name", "l'entreprise")
        elif isinstance(job.get("company_name"), str):
            company_name = job["company_name"]
        
        prompt = COVER_LETTER_PROMPT.format(
            profile_data=profile_text,
            job_title=job_title,
            company_name=company_name,
            job_description=job_description,
            job_skills=job_skills,
            job_location=job_location
        )
        
        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return message.content[0].text.strip()
            
        except Exception as e:
            raise ValueError(f"Cover letter generation failed: {str(e)}")
    
    def _format_profile(self, profile: Dict[str, Any]) -> str:
        """Format profile data for the prompt."""
        sections = []
        
        # AI description
        if profile.get("ai_description"):
            sections.append(f"Résumé: {profile['ai_description']}")
        
        # Latest job
        if profile.get("latest_job_title"):
            sections.append(f"Poste actuel/récent: {profile['latest_job_title']}")
        
        # Years of experience
        if profile.get("years_of_experience"):
            sections.append(f"Années d'expérience: {profile['years_of_experience']}")
        
        # Skills
        if profile.get("skills"):
            skills = profile["skills"][:15]  # Limit to 15 skills
            sections.append(f"Compétences clés: {', '.join(skills)}")
        
        # Recent experiences
        experiences = profile.get("experiences", [])
        if experiences:
            exp_text = []
            for exp in experiences[:3]:  # Last 3 experiences
                exp_text.append(
                    f"- {exp.get('poste', 'Poste')} chez {exp.get('entreprise', 'Entreprise')} "
                    f"({exp.get('dates', '')})"
                )
            sections.append("Expériences récentes:\n" + "\n".join(exp_text))
        
        # Languages
        if profile.get("languages"):
            langs = [f"{l.get('language')} ({l.get('level')})" for l in profile["languages"]]
            sections.append(f"Langues: {', '.join(langs)}")
        
        # User description
        if profile.get("user_description"):
            sections.append(f"Motivation: {profile['user_description']}")
        
        return "\n\n".join(sections)
    
    def _get_mock_cover_letter(
        self,
        profile: Dict[str, Any],
        job: Dict[str, Any]
    ) -> str:
        """Return a mock cover letter for development without API key."""
        job_title = job.get("title", "ce poste")
        company_name = "votre entreprise"
        
        if isinstance(job.get("company"), dict):
            company_name = job["company"].get("name", company_name)
        
        latest_job = profile.get("latest_job_title", "mon parcours professionnel")
        
        return f"""Madame, Monsieur,

C'est avec un vif intérêt que je vous adresse ma candidature pour le poste de {job_title} au sein de {company_name}.

Fort(e) de mon expérience en tant que {latest_job}, j'ai développé des compétences solides qui correspondent parfaitement aux exigences de ce poste. Mon parcours m'a permis d'acquérir une expertise technique approfondie ainsi qu'une capacité à travailler efficacement en équipe.

Je suis particulièrement attiré(e) par {company_name} pour son approche innovante et ses valeurs. Je suis convaincu(e) que mon profil et ma motivation seraient un atout pour votre équipe.

Je me tiens à votre disposition pour un entretien afin de vous présenter plus en détail mon parcours et mes motivations.

Cordialement"""
