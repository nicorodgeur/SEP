"""
modules/writer.py — Module 3 : Génération des lettres de motivation.

Stub : template simple. À remplacer par un appel LLM (Anthropic / OpenAI)
pour personnaliser la lettre en fonction de la fiche de poste.
"""

from typing import Optional

from loguru import logger

from config import CANDIDATE_NAME, CANDIDATE_LOCATION, CANDIDATE_PROFILE


class CoverLetterWriter:
    """Génère lettre de motivation + objet d'email."""

    def __init__(self):
        self.candidate = CANDIDATE_NAME
        self.location = CANDIDATE_LOCATION
        self.profile = CANDIDATE_PROFILE

    def generate_cover_letter(
        self,
        job_title: str,
        company: str,
        job_description: str,
        recruiter_name: Optional[str] = None,
        contract_type: str = "CDI",
    ) -> str:
        logger.debug(f"    Rédaction lettre pour {company} / {job_title}")
        greeting = f"Bonjour {recruiter_name}," if recruiter_name else "Bonjour,"
        return (
            f"{greeting}\n\n"
            f"Votre offre « {job_title} » ({contract_type}) chez {company} retient toute "
            f"mon attention. Mon parcours articulé autour de {self.profile} s'inscrit "
            f"naturellement dans les enjeux que vous décrivez.\n\n"
            f"Basé à {self.location}, je serais ravi d'échanger sur la façon dont je peux "
            f"contribuer à vos projets.\n\n"
            f"Cordialement,\n{self.candidate}\n"
        )

    def generate_email_subject(self, job_title: str, company: str) -> str:
        return f"Candidature — {job_title} ({company}) — {CANDIDATE_NAME}"
