import os
import json
from typing import Dict, Any, Optional
from datetime import datetime
import anthropic
import PyPDF2
from io import BytesIO


ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


CV_EXTRACTION_PROMPT = """Tu es un assistant expert en analyse de CV. Analyse le CV suivant et extrais les informations structurées.

CV:
{cv_text}

{user_description}

Réponds UNIQUEMENT avec un JSON valide (pas de texte avant ou après) avec la structure suivante:
{{
    "experiences": [
        {{
            "poste": "Titre du poste",
            "entreprise": "Nom de l'entreprise",
            "dates": "Date début - Date fin",
            "date_debut": "YYYY-MM",
            "date_fin": "YYYY-MM ou null si en cours",
            "lieu": "Ville, Pays",
            "competences": ["compétence1", "compétence2"],
            "description": "Résumé des responsabilités"
        }}
    ],
    "education": [
        {{
            "diplome": "Nom du diplôme",
            "ecole": "Nom de l'école",
            "annee": "Année d'obtention",
            "lieu": "Ville, Pays"
        }}
    ],
    "skills": ["compétence1", "compétence2", "compétence3"],
    "languages": [
        {{"language": "Français", "level": "Natif"}},
        {{"language": "Anglais", "level": "Courant"}}
    ],
    "latest_job_title": "Dernier poste occupé",
    "years_of_experience": 5,
    "preferred_location": "Ville préférée basée sur l'historique"
}}

Sois précis et exhaustif dans l'extraction des compétences techniques et soft skills.
"""


AI_DESCRIPTION_PROMPT = """Tu es un expert en rédaction de profils professionnels. Génère une description professionnelle concise et percutante basée sur le CV et la description fournie par le candidat.

CV extrait:
{cv_data}

Description du candidat:
{user_description}

Génère une description de 3-4 phrases maximum qui:
1. Résume le parcours professionnel
2. Met en avant les compétences clés
3. Indique le type de poste recherché
4. Reste authentique et professionnel

Réponds directement avec la description, sans guillemets ni formatage spécial.
"""


class CVAnalysisService:
    """Service for CV upload, parsing, and AI analysis."""
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None
    
    def extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF file."""
        try:
            pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    
    def extract_text_from_docx(self, file_content: bytes) -> str:
        """Extract text from DOCX file."""
        try:
            import docx
            doc = docx.Document(BytesIO(file_content))
            text = "\n".join([para.text for para in doc.paragraphs])
            return text.strip()
        except ImportError:
            raise ValueError("python-docx not installed. Install with: pip install python-docx")
        except Exception as e:
            raise ValueError(f"Failed to extract text from DOCX: {str(e)}")
    
    def extract_cv_text(self, file_content: bytes, filename: str) -> str:
        """Extract text from CV file based on extension."""
        filename_lower = filename.lower()
        
        if filename_lower.endswith('.pdf'):
            return self.extract_text_from_pdf(file_content)
        elif filename_lower.endswith('.docx'):
            return self.extract_text_from_docx(file_content)
        elif filename_lower.endswith('.txt'):
            return file_content.decode('utf-8')
        else:
            raise ValueError(f"Unsupported file format: {filename}. Use PDF, DOCX, or TXT.")
    
    async def analyze_cv(
        self, 
        cv_text: str, 
        user_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze CV text using Claude API.
        Returns structured data: experiences, skills, languages, education.
        """
        if not self.client:
            # Return mock data if no API key (for development)
            return self._get_mock_analysis()
        
        user_desc_text = f"\nDescription fournie par le candidat:\n{user_description}" if user_description else ""
        
        prompt = CV_EXTRACTION_PROMPT.format(
            cv_text=cv_text,
            user_description=user_desc_text
        )
        
        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = message.content[0].text.strip()
            
            # Parse JSON response
            # Handle potential markdown code blocks
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            
            return json.loads(response_text)
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse CV analysis response: {str(e)}")
        except Exception as e:
            raise ValueError(f"CV analysis failed: {str(e)}")
    
    async def generate_ai_description(
        self,
        cv_data: Dict[str, Any],
        user_description: Optional[str] = None
    ) -> str:
        """Generate an AI-powered professional description."""
        if not self.client:
            return "Professionnel expérimenté avec des compétences variées, recherchant de nouvelles opportunités."
        
        prompt = AI_DESCRIPTION_PROMPT.format(
            cv_data=json.dumps(cv_data, ensure_ascii=False, indent=2),
            user_description=user_description or "Non fournie"
        )
        
        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return message.content[0].text.strip()
            
        except Exception as e:
            raise ValueError(f"Description generation failed: {str(e)}")
    
    def _get_mock_analysis(self) -> Dict[str, Any]:
        """Return mock data for development without API key."""
        return {
            "experiences": [
                {
                    "poste": "Senior Software Engineer",
                    "entreprise": "Tech Company",
                    "dates": "2020 - Present",
                    "date_debut": "2020-01",
                    "date_fin": None,
                    "lieu": "Paris, France",
                    "competences": ["Python", "FastAPI", "PostgreSQL", "Docker"],
                    "description": "Développement d'applications web backend"
                }
            ],
            "education": [
                {
                    "diplome": "Master en Informatique",
                    "ecole": "Université Paris",
                    "annee": "2018",
                    "lieu": "Paris, France"
                }
            ],
            "skills": ["Python", "JavaScript", "SQL", "Docker", "AWS", "Git"],
            "languages": [
                {"language": "Français", "level": "Natif"},
                {"language": "Anglais", "level": "Courant"}
            ],
            "latest_job_title": "Senior Software Engineer",
            "years_of_experience": 5,
            "preferred_location": "Paris"
        }
