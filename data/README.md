# Data and benchmark

Task definitions currently live in `backend/app/tasks.py` so the first demo has no external data dependency. Before training, migrate them to versioned JSONL and record task provenance, repository snapshot, license, test command, and train/validation/test split. Do not put model weights, caches, or large benchmark artifacts in Git.
