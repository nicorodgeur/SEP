"""
modules/scraper.py — Module 1 : Scraping des job boards.

Stub d'implémentation : retourne une liste vide pour l'instant.
À compléter avec des connecteurs spécifiques (WTTJ, Indeed, LinkedIn, etc.).
"""

from typing import Dict, List, Optional

from loguru import logger

from config import JOB_BOARDS, JOB_KEYWORDS, JOB_LOCATION, MIN_RELEVANCE_SCORE
from utils.database import upsert_job


class JobScraper:
    """Orchestrateur des connecteurs de job boards."""

    def __init__(self):
        self.boards = JOB_BOARDS
        self.keywords = JOB_KEYWORDS
        self.location = JOB_LOCATION

    def scrape_all(self) -> List[Dict]:
        """
        Itère sur tous les job boards configurés, retourne la liste des nouvelles offres
        (déjà filtrées par MIN_RELEVANCE_SCORE et persistées en DB).
        """
        all_jobs: List[Dict] = []
        for board in self.boards:
            try:
                jobs = self._scrape_board(board)
                logger.debug(f"    {board}: {len(jobs)} offres")
                all_jobs.extend(jobs)
            except Exception as e:
                logger.error(f"    {board} erreur : {e}")

        kept: List[Dict] = []
        for job in all_jobs:
            if job.get("relevance_score", 0) < MIN_RELEVANCE_SCORE:
                continue
            upsert_job(job)
            kept.append(job)
        return kept

    def _scrape_board(self, board: str) -> List[Dict]:
        """Dispatch vers le connecteur spécifique. Stub par défaut."""
        return []

    def fetch_job_details(self, url: str, source: str) -> Optional[str]:
        """Récupère la description complète d'une offre (stub)."""
        return None
