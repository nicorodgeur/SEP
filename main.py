"""
main.py — Orchestrateur principal de l'agent Job Hunt
Lance le cycle toutes les N heures (configurable dans .env)
"""

import time
import sys
import traceback
from datetime import datetime
from typing import List, Dict

import schedule
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from loguru import logger

from config import (
    SCRAPE_INTERVAL_HOURS, MIN_RELEVANCE_SCORE,
    MAX_APPLICATIONS_PER_CYCLE, DELAY_BETWEEN_APPLICATIONS, DRY_RUN
)
from utils.logger import setup_logger
from utils.database import init_database, get_jobs_by_status, get_stats, start_cycle, end_cycle
from modules.scraper import JobScraper
from modules.investigator import ContactInvestigator
from modules.writer import CoverLetterWriter
from modules.executor import ApplicationExecutor

console = Console()


def print_banner():
    console.print(Panel.fit(
        "[bold blue]🤖 Nicolas Roger — Job Hunt Agent[/bold blue]\n"
        "[dim]Communication · Data · E-Commerce · Paris[/dim]",
        border_style="blue"
    ))
    if DRY_RUN:
        console.print("[yellow bold]⚠️  MODE DRY RUN ACTIF — Aucune vraie candidature ne sera envoyée[/yellow bold]")
    console.print(f"[dim]Cycle toutes les {SCRAPE_INTERVAL_HOURS}h · Score min {MIN_RELEVANCE_SCORE}% · Max {MAX_APPLICATIONS_PER_CYCLE} candidatures/cycle[/dim]\n")


def run_cycle():
    """
    Exécute un cycle complet :
    1. Scrape les job boards
    2. Pour chaque nouvelle offre pertinente :
       a. Recherche le recruteur
       b. Génère la lettre de motivation
       c. Tente de postuler (ou envoie rapport)
    3. Rapport de synthèse
    """
    cycle_start = datetime.now()
    cycle_id = start_cycle()
    console.rule(f"[bold blue]⏱  Cycle #{cycle_id} — {cycle_start.strftime('%d/%m/%Y %H:%M')}[/bold blue]")

    jobs_found = 0
    jobs_processed_this_cycle = []
    errors = []

    # ── Initialiser les modules ──
    try:
        scraper      = JobScraper()
        investigator = ContactInvestigator()
        writer       = CoverLetterWriter()
        executor     = ApplicationExecutor()
    except Exception as e:
        logger.critical(f"Initialisation des modules échouée : {e}")
        end_cycle(cycle_id, 0, 0, 0, str(e))
        return

    # ── MODULE 1 : Scraping ──────────────────────────────────
    logger.info("📡 Module 1 : Scraping des job boards...")
    try:
        new_jobs = scraper.scrape_all()
        jobs_found = len(new_jobs)
        logger.info(f"  → {jobs_found} nouvelles offres trouvées")
    except Exception as e:
        logger.error(f"Module 1 erreur : {e}")
        errors.append(f"Scraper: {e}")
        new_jobs = []

    # Récupérer aussi les offres "new" déjà en DB non encore traitées
    pending_jobs = get_jobs_by_status("new")
    all_to_process = new_jobs[:MAX_APPLICATIONS_PER_CYCLE]

    if not all_to_process and pending_jobs:
        all_to_process = pending_jobs[:MAX_APPLICATIONS_PER_CYCLE]

    if not all_to_process:
        logger.info("⏸  Aucune offre à traiter ce cycle.")
        end_cycle(cycle_id, jobs_found, 0, 0, "; ".join(errors))
        return

    # Trier par score décroissant
    all_to_process.sort(key=lambda j: j.get("relevance_score", 0), reverse=True)

    # ── Afficher le tableau des offres à traiter ─────────────
    table = Table(title=f"🎯 {len(all_to_process)} offres à traiter", show_header=True, header_style="bold blue")
    table.add_column("Score", style="bold", width=8)
    table.add_column("Poste", width=35)
    table.add_column("Entreprise", width=25)
    table.add_column("Source", width=12)
    for j in all_to_process:
        score = j.get("relevance_score", 0)
        color = "green" if score >= 80 else "yellow" if score >= 70 else "cyan"
        table.add_row(
            Text(f"{score}%", style=f"bold {color}"),
            j.get("title", "?")[:35],
            j.get("company", "?")[:25],
            j.get("source", "?"),
        )
    console.print(table)

    # ── Traitement de chaque offre ───────────────────────────
    applications_sent = 0

    for i, job in enumerate(all_to_process):
        if applications_sent >= MAX_APPLICATIONS_PER_CYCLE:
            logger.info(f"Quota {MAX_APPLICATIONS_PER_CYCLE} candidatures atteint — arrêt du cycle.")
            break

        console.print(f"\n[bold]({i+1}/{len(all_to_process)}) Traitement : {job['title']} @ {job['company']}[/bold]")

        try:
            # Enrichir la description si elle est courte
            if len(job.get("description", "")) < 200:
                logger.debug("  📄 Récupération description complète...")
                full_desc = scraper.fetch_job_details(job["url"], job["source"])
                if full_desc:
                    job["description"] = full_desc

            # ── MODULE 2 : Recherche recruteur ──────────────
            logger.info("  🔍 Module 2 : Recherche recruteur...")
            recruiter_name, recruiter_email = investigator.find_recruiter(
                job["company"], job["url"], job["title"]
            )
            job["recruiter_name"] = recruiter_name
            job["recruiter_email"] = recruiter_email

            # ── MODULE 3 : Génération lettre ────────────────
            logger.info("  ✍️  Module 3 : Génération lettre de motivation...")
            cover_letter = writer.generate_cover_letter(
                job_title       = job["title"],
                company         = job["company"],
                job_description = job.get("description", ""),
                recruiter_name  = recruiter_name,
                contract_type   = job.get("contract_type", "CDI"),
            )
            email_subject = writer.generate_email_subject(job["title"], job["company"])

            # ── MODULE 4 : Candidature / Rapport ────────────
            logger.info("  🚀 Module 4 : Candidature / Envoi rapport...")
            result = executor.process_job(
                job             = job,
                cover_letter    = cover_letter,
                email_subject   = email_subject,
                recruiter_name  = recruiter_name,
                recruiter_email = recruiter_email,
            )

            job["status"] = result
            jobs_processed_this_cycle.append(job)

            if result in ("auto_form_wttj", "auto_form_indeed", "direct_email", "email_sent", "dry_run"):
                applications_sent += 1
                logger.success(f"  ✅ [{result.upper()}] {job['company']} — {job['title'][:30]}")
            else:
                logger.warning(f"  ⚠️  Échec candidature : {job['company']}")

        except Exception as e:
            logger.error(f"  ❌ Erreur traitement {job.get('company','?')} : {e}")
            errors.append(f"{job.get('company','?')}: {str(e)[:100]}")
            continue

        # Délai anti-détection entre les candidatures
        if i < len(all_to_process) - 1:
            logger.debug(f"  ⏳ Pause {DELAY_BETWEEN_APPLICATIONS}s...")
            time.sleep(DELAY_BETWEEN_APPLICATIONS)

    # ── Rapport de synthèse ──────────────────────────────────
    stats = get_stats()
    try:
        executor.send_daily_summary(stats, jobs_processed_this_cycle)
    except Exception as e:
        logger.warning(f"Rapport quotidien non envoyé : {e}")

    duration = (datetime.now() - cycle_start).seconds
    end_cycle(cycle_id, jobs_found, len(jobs_processed_this_cycle), applications_sent, "; ".join(errors))

    console.print(Panel(
        f"[green bold]✅ Cycle #{cycle_id} terminé en {duration}s[/green bold]\n"
        f"Offres trouvées : {jobs_found} · Traitées : {len(jobs_processed_this_cycle)} · "
        f"Candidatures : [bold]{applications_sent}[/bold]",
        border_style="green"
    ))


def main():
    setup_logger()
    print_banner()
    init_database()

    logger.info(f"🕐 Scheduler démarré — cycle toutes les {SCRAPE_INTERVAL_HOURS}h")

    # Lancer immédiatement un premier cycle au démarrage
    run_cycle()

    # Planifier les cycles suivants
    schedule.every(SCRAPE_INTERVAL_HOURS).hours.do(run_cycle)

    console.print(f"\n[dim]Prochaine exécution dans {SCRAPE_INTERVAL_HOURS}h. Ctrl+C pour arrêter.[/dim]")

    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Vérifier le scheduler toutes les minutes
        except KeyboardInterrupt:
            console.print("\n[yellow]⏹  Agent arrêté manuellement.[/yellow]")
            stats = get_stats()
            console.print(f"[dim]Stats finales : {stats}[/dim]")
            sys.exit(0)
        except Exception as e:
            logger.critical(f"Erreur critique dans la boucle principale : {e}\n{traceback.format_exc()}")
            time.sleep(300)  # Pause 5 min avant de réessayer


if __name__ == "__main__":
    main()
