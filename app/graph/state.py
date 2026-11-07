from typing import TypedDict


class JobHunterState(TypedDict):
    search_queries: list[str]
    raw_jobs: list[dict]
    extracted_jobs: list[dict]
    matched_jobs: list[dict]
    ranked_jobs: list[dict]
    report: str
    errors: list[str]
    cv_path: str
    cv_text: str
    candidate_profile: dict
    jobs_file: str
    seen_jobs_file: str
    seen_ids: list[str]
    report_date: str
