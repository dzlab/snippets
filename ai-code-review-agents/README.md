# AI Code Review Agents

Runnable companion code for the AI code review article.

The experiment compares four reviewer implementations against the same synthetic benchmark:

- diff-only reviewer
- full-context reviewer
- selective-context reviewer using Chroma retrieval
- specialized ensemble reviewer

## Files

| File | Purpose |
|---|---|
| `src/data.py` | Synthetic FastAPI repository fixture and 15 flawed pull requests. |
| `src/reviewers.py` | General reviewer, specialist reviewers, and ensemble combiner. |
| `src/context.py` | AST chunking, embedding, Chroma indexing, and retrieval. |
| `src/evaluation.py` | Keyword-overlap benchmark harness. |
| `run_experiment.py` | CLI entry point. |

## Run

```bash
cd ~/co/github/dzlab/snippets/ai-code-review-agents
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set `OPENAI_API_KEY`, then run:

```bash
python run_experiment.py --dry-run
python run_experiment.py --mode all --limit 3
python run_experiment.py --mode all
```

Use `--limit` while iterating to reduce token usage. `--dry-run` validates fixture loading and chunking without making OpenAI API calls.

## Options

```bash
python run_experiment.py --help
```

Useful examples:

```bash
python run_experiment.py --mode diff --limit 5
python run_experiment.py --mode selective --n-results 8
python run_experiment.py --mode ensemble --model gpt-4o-mini
```
