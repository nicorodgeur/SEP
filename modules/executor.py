"""
modules/executor.py — Module 4 : Envoi des candidatures + rapport quotidien.

Implémente la voie "email" et le mode dry-run. Les soumissions automatiques
via formulaire (WTTJ, Indeed...) sont laissées en stubs.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional

from loguru import logger

from config import (
    DRY_RUN,
    EMAIL_FROM, EMAIL_REPORT_TO,
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD,
    CANDIDATE_NAME,
)
from utils.database import set_job_status


class ApplicationExecutor:
    """Transforme une offre + lettre en candidature envoyée (ou rapport)."""

    def __init__(self):
        self.dry_run = DRY_RUN

    def process_job(
        self,
        job: Dict,
        cover_letter: str,
        email_subject: str,
        recruiter_name: Optional[str],
        recruiter_email: Optional[str],
    ) -> str:
        """
        Retourne un code statut :
        - "dry_run"          : DRY_RUN activé, rien envoyé
        - "direct_email"     : email envoyé au recruteur
        - "auto_form_wttj"   : formulaire WTTJ soumis (stub)
        - "auto_form_indeed" : formulaire Indeed soumis (stub)
        - "email_sent"       : email envoyé via canal générique
        - "failed"           : aucune voie disponible / erreur
        """
        if self.dry_run:
            logger.info(f"    [DRY RUN] Candidature simulée pour {job['company']}")
            set_job_status(job["url"], "dry_run")
            return "dry_run"

        if recruiter_email:
            try:
                self._send_email(
                    to=recruiter_email,
                    subject=email_subject,
                    body=cover_letter,
                )
                set_job_status(job["url"], "direct_email")
                return "direct_email"
            except Exception as e:
                logger.error(f"    Envoi email échoué : {e}")

        source = (job.get("source") or "").lower()
        if source == "wttj":
            return self._submit_wttj(job, cover_letter)
        if source == "indeed":
            return self._submit_indeed(job, cover_letter)

        set_job_status(job["url"], "failed")
        return "failed"

    def _submit_wttj(self, job: Dict, cover_letter: str) -> str:
        logger.warning("    Soumission WTTJ non implémentée.")
        set_job_status(job["url"], "failed")
        return "failed"

    def _submit_indeed(self, job: Dict, cover_letter: str) -> str:
        logger.warning("    Soumission Indeed non implémentée.")
        set_job_status(job["url"], "failed")
        return "failed"

    def _send_email(self, to: str, subject: str, body: str) -> None:
        if not (SMTP_HOST and SMTP_USER and SMTP_PASSWORD):
            raise RuntimeError("SMTP non configuré (SMTP_HOST / SMTP_USER / SMTP_PASSWORD).")
        msg = MIMEMultipart()
        msg["From"] = EMAIL_FROM or SMTP_USER
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(msg["From"], [to], msg.as_string())

    def send_daily_summary(self, stats: Dict, jobs: List[Dict]) -> None:
        """Envoie un récap à EMAIL_REPORT_TO."""
        if not EMAIL_REPORT_TO:
            logger.debug("    Pas de destinataire de rapport configuré.")
            return

        lines = [f"Synthèse cycle — {CANDIDATE_NAME}", ""]
        lines.append(f"Stats globales : {stats}")
        lines.append("")
        if jobs:
            lines.append("Offres traitées ce cycle :")
            for j in jobs:
                lines.append(
                    f"  - [{j.get('status','?')}] {j.get('company','?')} — "
                    f"{j.get('title','?')} ({j.get('relevance_score',0)}%)"
                )
        else:
            lines.append("Aucune offre traitée ce cycle.")

        body = "\n".join(lines)
        subject = f"[Job Hunt] Rapport — {len(jobs)} offre(s) traitée(s)"

        if self.dry_run or not (SMTP_HOST and SMTP_USER and SMTP_PASSWORD):
            logger.info(f"    [REPORT] {subject}\n{body}")
            return

        self._send_email(to=EMAIL_REPORT_TO, subject=subject, body=body)
