# AI Code Review Agents

Runnable companion code for the AI code review article.

Article: [AI Code Review: Context, Retrieval, and Specialized Review Agents](https://dzlab.github.io/genai/2026/08/11/ai-code-review-agents/)

The experiment compares four reviewer implementations against the same synthetic benchmark:

- diff-only reviewer
- full-context reviewer
- selective-context reviewer using Chroma retrieval
- specialized ensemble reviewer

## Files

| File | Purpose |
|---|---|
| `fixtures/repository/` | File-backed synthetic FastAPI repository used as the review baseline. |
| `fixtures/prs/` | The 15 flawed pull requests stored as standalone diff files. |
| `src/data.py` | Fixture loaders plus PR metadata and expected issues. |
| `src/reviewers.py` | General reviewer, specialist reviewers, and ensemble combiner. |
| `src/context.py` | AST chunking, embedding, Chroma indexing, and retrieval. |
| `src/evaluation.py` | Keyword-overlap benchmark harness. |
| `run_experiment.py` | CLI entry point. |
| `pyproject.toml` | Project metadata and direct dependencies for `uv`. |
| `uv.lock` | Reproducible dependency lockfile. |

## Run

Install `uv` first if it is not already available.

```bash
cd ~/co/github/dzlab/snippets/ai-code-review-agents
uv sync
cp .env.example .env
```

Edit `.env` and set `OPENAI_API_KEY`, then run:

```bash
uv run python run_experiment.py --dry-run
uv run python run_experiment.py --mode all --limit 3
uv run python run_experiment.py --mode all
```

`uv sync` creates the project virtual environment and installs dependencies. Use `--limit` while iterating to reduce token usage. `--dry-run` validates fixture loading and chunking without making OpenAI API calls.

## Options

```bash
uv run python run_experiment.py --help
```

Useful examples:

```bash
uv run python run_experiment.py --mode diff --limit 5
uv run python run_experiment.py --mode selective --n-results 8
uv run python run_experiment.py --mode ensemble --model gpt-4o-mini
```
