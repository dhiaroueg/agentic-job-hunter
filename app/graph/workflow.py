"""LangGraph pipeline for authorized job feeds and explainable CV matching."""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from langgraph.graph import END, START, StateGraph

from app.config import settings
from app.graph.state import JobHunterState

SKILLS = {
    "python", "java", "scala", "sql", "pytorch", "tensorflow", "scikit-learn",
    "pandas", "numpy", "hugging face", "transformers", "langchain", "langgraph",
    "docker", "kubernetes", "aws", "azure", "gcp", "mlflow", "spark", "tableau",
    "power bi", "git", "fastapi", "opencv", "nlp", "deep learning", "machine learning",
}
INTERN_TERMS = ("intern", "internship", "stage", "stagiaire", "trainee")
EUROPE_TERMS = ("europe", "remote", "remotely", "hybrid", "france", "germany", "spain", "italy", "netherlands", "belgium", "ireland", "sweden", "finland", "denmark", "portugal", "poland", "switzerland", "united kingdom", "uk", "paris", "berlin", "amsterdam", "london", "dublin")


def _read_cv(path: str | None) -> str:
    if not path:
        return ""
    file = Path(path)
    if not file.is_file():
        return ""
    try:
        if file.suffix.lower() == ".pdf":
            from pypdf import PdfReader
            return "\n".join(page.extract_text() or "" for page in PdfReader(str(file)).pages)
        if file.suffix.lower() == ".docx":
            from docx import Document
            return "\n".join(p.text for p in Document(str(file)).paragraphs)
        if file.suffix.lower() in (".txt", ".md"):
            return file.read_text(encoding="utf-8", errors="ignore")
    except Exception as exc:
        raise ValueError(f"Impossible de lire le CV ({file.suffix}): {exc}") from exc
    raise ValueError("Format CV non pris en charge. Utilisez PDF, DOCX ou TXT.")


def _skills(text: str) -> list[str]:
    normalized = text.casefold()
    return sorted(skill for skill in SKILLS if re.search(r"(?<!\w)" + re.escape(skill) + r"(?!\w)", normalized))


def discover_jobs(state: JobHunterState) -> dict[str, Any]:
    """Read authorized adapter data from JSONL; adapters can be added without scraping sites."""
    jobs = list(state.get("raw_jobs", []))
    errors = list(state.get("errors", []))
    feed = state.get("jobs_file") or settings.JOBS_FILE
    if feed:
        path = Path(feed)
        if path.is_file():
            try:
                if path.suffix.lower() == ".jsonl":
                    jobs.extend(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
                else:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                    jobs.extend(payload if isinstance(payload, list) else payload.get("jobs", []))
            except (OSError, ValueError, TypeError) as exc:
                errors.append(f"Lecture du flux {path}: {exc}")
    seen_path = Path(state.get("seen_jobs_file") or "data/seen_job_ids.json")
    try:
        seen_ids = set(json.loads(seen_path.read_text(encoding="utf-8"))) if seen_path.is_file() else set()
        fresh = [job for job in jobs if str(job.get("source_id") or job.get("url") or job.get("apply_url") or "").casefold() not in seen_ids]
        return {"raw_jobs": fresh, "errors": errors, "seen_ids": sorted(seen_ids)}
    except (OSError, ValueError, TypeError) as exc:
        errors.append(f"Lecture de l’historique des offres: {exc}")
        return {"raw_jobs": jobs, "errors": errors, "seen_ids": []}


def extract_jobs(state: JobHunterState) -> dict[str, Any]:
    normalized, seen = [], set()
    for raw in state.get("raw_jobs", []):
        title = str(raw.get("title", "")).strip()
        description = re.sub(r"\s+", " ", str(raw.get("description", "")).strip())
        url = str(raw.get("url") or raw.get("apply_url") or "").strip()
        if not title or not url:
            continue
        parsed = urlsplit(url)
        canonical = urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path.rstrip("/"), "", ""))
        key = str(raw.get("source_id") or canonical).casefold()
        if key in seen:
            continue
        seen.add(key)
        text = f"{title} {description}"
        normalized.append({
            "title": title, "company": str(raw.get("company", "À préciser")).strip(),
            "location": str(raw.get("location", "")).strip(), "description": description,
            "published_at": raw.get("published_at", ""), "url": url,
            "source": raw.get("source", "feed"), "source_id": raw.get("source_id", ""),
            "skills": _skills(text), "internship": any(t in text.casefold() for t in INTERN_TERMS),
        })
    return {"extracted_jobs": normalized}


def analyze_cv(state: JobHunterState) -> dict[str, Any]:
    errors = list(state.get("errors", []))
    text = str(state.get("cv_text", ""))
    try:
        text = text or _read_cv(state.get("cv_path") or settings.CV_PATH)
    except ValueError as exc:
        errors.append(str(exc))
    profile = {"skills": _skills(text), "text": text, "available": bool(text)}
    return {"candidate_profile": profile, "errors": errors}


def match_jobs(state: JobHunterState) -> dict[str, Any]:
    profile = state.get("candidate_profile", {}) or {}
    candidate_skills = set(profile.get("skills", []))
    matched = []
    for job in state.get("extracted_jobs", []):
        job_skills = set(job.get("skills", []))
        overlap = sorted(candidate_skills & job_skills)
        semantic = len(overlap) / max(1, len(job_skills)) if candidate_skills else 0.0
        matched.append({**job, "matching_skills": overlap, "skill_match": semantic, "cv_available": bool(profile.get("available"))})
    return {"matched_jobs": matched}


def score_jobs(state: JobHunterState) -> dict[str, Any]:
    ranked = []
    for job in state.get("matched_jobs", []):
        location = job.get("location", "").casefold()
        location_match = any(term in location for term in EUROPE_TERMS)
        internship_points = 20 if job.get("internship") else 0
        location_points = 15 if location_match else 0
        skills_points = round(60 * float(job.get("skill_match", 0))) if job.get("cv_available") else 0
        title = job.get("title", "").casefold()
        role_points = 5 if any(t in title for t in ("ai", "data scientist", "machine learning", "ml engineer")) else 0
        score = min(100, skills_points + internship_points + location_points + role_points)
        ranked.append({**job, "score": score, "score_breakdown": {"skills": skills_points, "internship": internship_points, "europe_or_remote": location_points, "role_relevance": role_points}})
    ranked.sort(key=lambda job: (-job["score"], job["title"].casefold()))
    return {"ranked_jobs": ranked}


def generate_report(state: JobHunterState) -> dict[str, Any]:
    jobs = state.get("ranked_jobs", [])
    lines = ["# Rapport quotidien – recherche de stages", "", f"Offres analysées : {len(jobs)}", ""]
    if not state.get("candidate_profile", {}).get("available"):
        lines.extend(["_Aucun CV n’a été fourni : les scores reflètent le type de poste et la localisation, sans comparaison de compétences._", ""])
    if not jobs:
        lines.append("Aucune nouvelle offre dans les sources configurées aujourd’hui.")
    for job in jobs:
        lines.extend([f"## {job['title']} — {job['company']}", f"**Score : {job['score']}/100** · {job['location'] or 'Lieu non précisé'} · {job.get('published_at') or 'Date non précisée'}", f"[Postuler]({job['url']})", ""])
        if job.get("matching_skills"):
            lines.append("Compétences correspondantes : " + ", ".join(job["matching_skills"]))
            lines.append("")
    if state.get("errors"):
        lines.extend(["### À vérifier", *[f"- {error}" for error in state["errors"]]])
    return {"report": "\n".join(lines), "report_date": date.today().isoformat()}


def build_workflow():
    graph = StateGraph(JobHunterState)
    for name, fn in (("discovery", discover_jobs), ("extraction", extract_jobs), ("cv_analysis", analyze_cv), ("matching", match_jobs), ("scoring", score_jobs), ("report", generate_report)):
        graph.add_node(name, fn)
    graph.add_edge(START, "discovery")
    graph.add_edge("discovery", "extraction")
    graph.add_edge("extraction", "cv_analysis")
    graph.add_edge("cv_analysis", "matching")
    graph.add_edge("matching", "scoring")
    graph.add_edge("scoring", "report")
    graph.add_edge("report", END)
    return graph.compile()
