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
uv run python run_experiment.py --mode all --model gpt-4o-mini --limit 3
uv run python run_experiment.py --mode all --model gpt-4o-mini
```

`uv sync` creates the project virtual environment and installs dependencies. Use `--limit` while iterating to reduce token usage. `--dry-run` validates fixture loading and chunking without making OpenAI API calls.

## Options

```bash
uv run python run_experiment.py --help
```

Useful examples:

```bash
uv run python run_experiment.py --mode diff --model gpt-4o-mini --limit 5
uv run python run_experiment.py --mode selective --n-results 8
uv run python run_experiment.py --mode ensemble --model gpt-4o-mini
```

## Local OpenAI Proxy

If OpenAI API billing is unavailable, run the sibling local proxy at `~/co/github/dzlab/openai-proxy`. It exposes OpenAI-compatible endpoints at `/v1`, sends chat-style requests to `codex app-server`, and uses deterministic local hash embeddings for retrieval tests.

The proxy stores Codex sessions under the configured `CODEX_HOME`, not under the default `~/.codex`. Initialize that isolated home once:

```bash
cd ~/co/github/dzlab/openai-proxy
OPENAI_PROXY_CODEX_HOME="$PWD/.openai-proxy-codex-home"
CODEX_HOME="$OPENAI_PROXY_CODEX_HOME" codex login
```

Start the proxy:

```bash
uv run --locked python -m openai_proxy \
  --host 127.0.0.1 \
  --port 8765 \
  --codex-home "$OPENAI_PROXY_CODEX_HOME" \
  --codex-cwd ~/co/github/dzlab/snippets/ai-code-review-agents
```

Point the OpenAI SDK at it:

```bash
cd ~/co/github/dzlab/snippets/ai-code-review-agents
OPENAI_API_KEY=local-test-key \
OPENAI_BASE_URL=http://127.0.0.1:8765/v1 \
uv run python run_experiment.py --mode diff --model gpt-4o-mini --limit 1
```

For selective retrieval, `/v1/embeddings` is handled locally and deterministically:

```bash
cd ~/co/github/dzlab/snippets/ai-code-review-agents
OPENAI_API_KEY=local-test-key \
OPENAI_BASE_URL=http://127.0.0.1:8765/v1 \
uv run python run_experiment.py --mode selective --model gpt-4o-mini --limit 1
```

Supported proxy endpoints:

- `GET /health`
- `GET /v1/models`
- `GET /v1/models/{model}`
- `POST /v1/chat/completions`
- `POST /v1/responses`
- `POST /v1/completions`
- `POST /v1/embeddings`

Other `/v1/*` endpoints return an OpenAI-style `unsupported_endpoint` error. Set `OPENAI_PROXY_API_KEY` or pass `--api-key` if you want the proxy to require a specific bearer token.
