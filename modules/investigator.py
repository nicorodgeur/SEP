"""
modules/investigator.py — Module 2 : Identification du recruteur.

Stub : renvoie (None, None) par défaut. À enrichir avec des sources
type Hunter.io, Apollo, LinkedIn, Google dorks, pages "équipe", etc.
"""

from typing import Optional, Tuple

from loguru import logger


class ContactInvestigator:
    """Recherche un contact humain (nom, email) pour une offre donnée."""

    def __init__(self):
        pass

    def find_recruiter(
        self, company: str, job_url: str, job_title: str
    ) -> Tuple[Optional[str], Optional[str]]:
        logger.debug(f"    Recherche contact pour {company}")
        return (None, None)
