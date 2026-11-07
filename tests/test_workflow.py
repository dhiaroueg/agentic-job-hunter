from app.graph.workflow import build_workflow


def test_workflow_runs_with_empty_sources():
    workflow = build_workflow()
    state = {
        "search_queries": ["AI Engineer Intern"],
        "raw_jobs": [],
        "extracted_jobs": [],
        "matched_jobs": [],
        "ranked_jobs": [],
        "report": "",
        "errors": [],
    }
    result = workflow.invoke(state)
    assert result["ranked_jobs"] == []
    assert "Offers analyzed: 0" in result["report"]
