# code-knowledge-graph

`codekg` is a dependency-free Python 3.11+ CLI for indexing a Git checkout into a SQLite-backed code graph, retrieving likely files for a task, rendering a lightweight structure map, running offline recall experiments, and comparing LLM ranking with and without the structure map prompt.

## Zero-dependency setup

No third-party packages are required.

```bash
git clone <this-repo>
cd code-knowledge-graph
python3 -m codekg --help
```

You can also install the local console script if you want:

```bash
python3 -m pip install .
codekg --help
```

## Index Any GitHub Checkout

`index` scans repository files with the parser, extracts co-edit edges from Git history, and writes the full graph into a SQLite database.

```bash
python3 -m codekg index /path/to/github-checkout \
  --db /tmp/codekg.sqlite3 \
  --max-commits 500 \
  --max-files-per-commit 50
```

The output is JSON with graph counts and parser warnings. Paths are resolved from the repository path you pass to `index`, so the same command works for any local GitHub checkout.

The database is a normal SQLite file. Re-running `index` replaces the stored graph contents in that file.

## Retrieve And Map

`retrieve` prints deterministic JSON with lexical anchors plus lexical and graph-ranked files and scores.

```bash
python3 -m codekg retrieve \
  --db /tmp/codekg.sqlite3 \
  --query "Which file defines helper_value?" \
  --k 5 \
  --anchors 3
```

`map` prints Markdown for the graph-ranked files:

```bash
python3 -m codekg map \
  --db /tmp/codekg.sqlite3 \
  --query "Which file defines helper_value?" \
  --k 5 \
  --anchors 3
```

If the DB file is missing or the query is empty, the CLI exits with a concise error on stderr.

## Task File Format

Offline experiments and A/B runs both read a JSON array of tasks. Each task must provide an explicit `query` and `gold_files`.

```json
[
  {
    "query": "Which file defines helper_value?",
    "gold_files": ["pkg/helpers.py"]
  },
  {
    "query": "Which file calls helper_value from the service layer?",
    "gold_files": ["pkg/service.py"]
  }
]
```

`gold_files` must use repository-relative POSIX paths that match the indexed checkout.

## Offline Experiment

`experiment` runs lexical ranking and graph ranking for each task, then reports per-task and aggregate `recall_at_1`, `recall_at_3`, and `recall_at_5`. The recall cutoff is bounded by the number of indexed files so the metrics stay valid on very small repositories.

```bash
python3 -m codekg experiment \
  --db /tmp/codekg.sqlite3 \
  --tasks examples/tasks.json \
  --anchors 3
```

The output is plain JSON only. It does not invent labels, winners, or statistical claims.

## LLM A/B Run

`ab` compares two prompts against the same candidate inventory and model settings:

- `control`: task plus candidate inventory
- `treatment`: task plus candidate inventory plus generated structure map

```bash
python3 -m codekg ab \
  --db /tmp/codekg.sqlite3 \
  --tasks examples/tasks.json \
  --base-url https://api.openai.com/v1 \
  --model gpt-4.1-mini \
  --k 8 \
  --runs 3 \
  --seed 7 \
  --output /tmp/codekg-ab.json
```

For real requests, provide an API key with `--api-key` or `OPENAI_API_KEY`. The CLI only requires an API key when `--dry-run` is not set.

Environment variables:

```bash
export OPENAI_BASE_URL=https://api.openai.com/v1
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=gpt-4.1-mini
```

Local endpoint example:

```bash
export OPENAI_BASE_URL=http://127.0.0.1:11434/v1
export OPENAI_API_KEY=dummy
export OPENAI_MODEL=qwen2.5-coder:14b
python3 -m codekg ab --db /tmp/codekg.sqlite3 --tasks examples/tasks.json --dry-run
```

`ab` records the arm, task index, run number, candidate inventory, ranked files, recall metrics, usage, and any request/response error string. `--output` writes the same JSON payload to disk.

## Privacy And Cost

`index`, `retrieve`, `map`, and `experiment` are fully local.

`ab` sends the task text, candidate relative paths, and, for the treatment arm, the generated structure map to the configured OpenAI-compatible endpoint. That can expose repository file names and graph-localized context to the model provider, and real requests can incur API cost according to the configured model.

## Scope

`codekg` helps localize likely files for a task. It does not autonomously edit repositories or execute multi-file changes inside the indexed checkout. Use it as a file-localization and prompt-shaping tool, then hand the ranked files to whatever editing workflow you prefer.
