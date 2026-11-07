# Agentic AI Job Hunter

Assistant quotidien de recherche de stages en IA et data en Europe et en télétravail. Le pipeline est orchestré par LangGraph et sépare découverte, extraction, analyse du CV, matching, scoring et génération du rapport.

## Démarrage

Python 3.10+ est requis.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -m app.main
```

Déposez le CV dans `data/cv.pdf` (ou configurez `CV_PATH`). Les formats PDF, DOCX et TXT sont acceptés. Configurez `JOBS_FILE` pour fournir les offres d’une API ou d’un adaptateur dont l’accès automatisé est autorisé.

## Format du flux d’offres

`data/jobs.json` peut contenir une liste d’offres ou un objet avec une clé `jobs`. Chaque entrée accepte :

```json
{
  "source": "official-api",
  "source_id": "job-123",
  "title": "Machine Learning Intern",
  "company": "Example",
  "location": "Remote, Europe",
  "description": "Python, PyTorch, SQL...",
  "published_at": "2026-11-07",
  "url": "https://example.org/jobs/123"
}
```

Le JSONL (une offre JSON par ligne) est aussi accepté. Le projet ne contourne pas les protections, connexions ou conditions d’utilisation des sites. Pour LinkedIn, utilisez l’ingestion de courriels d’alertes ou une intégration explicitement autorisée.

## Résultats et email

Le rapport Markdown est enregistré dans `reports/job_report_YYYY-MM-DD.md`. Les offres vues sont consignées dans `data/seen_job_ids.json` afin de les filtrer aux exécutions suivantes. L’envoi SMTP est activé uniquement lorsque `EMAIL_SENDER`, `EMAIL_PASSWORD` et `EMAIL_RECEIVER` sont renseignés. Gardez les secrets dans `.env`, jamais dans Git. Programmez `python -m app.main` avec le planificateur de votre système pour une exécution quotidienne.

Le score sur 100 combine compétences correspondantes (60 points), caractère stage (20), Europe/télétravail (15) et pertinence du titre (5). Sans CV, les points de compétences restent à zéro. Le rapport affiche les compétences communes pour rendre le score lisible.

## Limites actuelles

Les adaptateurs de sources spécifiques et l’ingestion des alertes email doivent être ajoutés selon les API et autorisations disponibles. L’extraction de compétences et le matching utilisent actuellement un vocabulaire local et une comparaison explicable ; les embeddings et les fonctions d’import web ne sont pas activés. L’envoi email et la persistance locale sont prêts à configurer.
