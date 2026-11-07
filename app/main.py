from app.graph.workflow import build_workflow
from app.services.delivery import save_report, send_report
import json
from pathlib import Path


def main():
    workflow = build_workflow()
    initial_state = {
        "search_queries": [
            "AI Engineer Intern",
            "Machine Learning Intern",
            "Data Scientist Intern",
            "Artificial Intelligence Internship",
        ],
        "raw_jobs": [],
        "extracted_jobs": [],
        "matched_jobs": [],
        "ranked_jobs": [],
        "report": "",
        "errors": [],
        "cv_path": None,
        "jobs_file": None,
        "seen_jobs_file": None,
    }
    result = workflow.invoke(initial_state)
    print("\\n===== DAILY JOB REPORT =====")
    print(result["report"])
    report_date = result.get("report_date", "daily")
    report_path = save_report(result["report"], report_date)
    print(f"\nRapport enregistré : {report_path}")
    try:
        seen_file = Path("data/seen_job_ids.json")
        previous = set(json.loads(seen_file.read_text(encoding="utf-8"))) if seen_file.is_file() else set()
        previous.update(str(job.get("source_id") or job.get("url") or "").casefold() for job in result.get("extracted_jobs", []))
        seen_file.parent.mkdir(parents=True, exist_ok=True)
        seen_file.write_text(json.dumps(sorted(previous), ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as exc:
        print(f"Historique de déduplication non enregistré : {exc}")
    try:
        if send_report(result["report"], report_date):
            print("Rapport envoyé par email.")
        else:
            print("Email non configuré ; rapport conservé localement.")
    except Exception as exc:
        print(f"Échec de l’envoi email : {exc}")


if __name__ == "__main__":
    main()
