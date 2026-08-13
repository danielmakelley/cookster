Cookster — EPUB Cookbook Search

Overview
- Index EPUB cookbooks and search for recipes by ingredients or keywords.

Installation
1. Create a virtualenv and install dependencies:

```
python -m venv .venv
.\\venv\\Scripts\\activate    # Windows
pip install -r requirements.txt
```

Index EPUB files

```
python run_index.py --epub-dir path/to/epubs --db cookster.db
```

Search recipes

```
python search.py --db cookster.db --query "chicken" --limit 10

Run as web service

```
pip install -r requirements.txt
python run_api.py
```

Then open http://127.0.0.1:8000 in your browser and search.

Download recipes

You can download the EPUB file that contains a recipe from the web UI by opening the recipe and clicking the download link, or programmatically via:

```
GET /download/{recipe_id}?db=cookster.db

# example
curl "http://127.0.0.1:8000/download/1?db=cookster.db" -o recipe1.epub
```

Improvements included:
- FTS pre-filtering for faster candidate retrieval
- BM25 ranking with stopword removal and simple synonym expansion
- Pagination, result counts, snippets with highlighted query terms
- API integration tests and CI workflow
```

Notes
- The indexer uses heuristics to extract recipe sections (looks for headings like "Ingredients" and "Directions").
- Results quality depends on EPUB formatting; you can refine heuristics in `indexer.py`.
