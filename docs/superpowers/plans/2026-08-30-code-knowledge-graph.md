# Portable Code Knowledge Graph Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a dependency-free Python companion that indexes arbitrary Python GitHub checkouts into SQLite, retrieves structurally related files, optionally asks an OpenAI-compatible API to rank files with and without graph context, and document the workflow in a self-contained Jekyll post.

**Architecture:** The parser produces typed file/symbol nodes and import/call/containment edges; a Git-history reader adds weighted co-edit edges. A SQLite store persists the graph and retrieval projects it to files for deterministic lexical seeding and Personalized PageRank. A small HTTP client supplies optional control/treatment localization trials, while the core CLI and offline experiment remain network-free.

**Tech Stack:** Python 3.11+ standard library (`ast`, `sqlite3`, `subprocess`, `urllib`), `unittest`, SQLite, Markdown/Jekyll, Mermaid.

---

## File map

Companion project files:

- Create `code-knowledge-graph/pyproject.toml`: package metadata and a console entry point with no runtime dependencies.
- Create `code-knowledge-graph/README.md`: setup, commands, task-file format, API configuration, limitations, and sample output.
- Create `code-knowledge-graph/codekg/__init__.py`: public package version and core exports.
- Create `code-knowledge-graph/codekg/__main__.py`: `python -m codekg` entry point.
- Create `code-knowledge-graph/codekg/model.py`: `Node`, `Edge`, `ParsedGraph`, and task/result dataclasses.
- Create `code-knowledge-graph/codekg/parser.py`: source-tree discovery and Python AST extraction.
- Create `code-knowledge-graph/codekg/git_history.py`: bounded co-edit extraction from Git history.
- Create `code-knowledge-graph/codekg/store.py`: SQLite schema, loading, counts, and file-level projection.
- Create `code-knowledge-graph/codekg/retrieval.py`: token overlap, anchors, PageRank, scoring, and structure-map rendering.
- Create `code-knowledge-graph/codekg/llm.py`: OpenAI-compatible chat-completions client and response parser.
- Create `code-knowledge-graph/codekg/cli.py`: `index`, `retrieve`, `map`, `experiment`, and `ab` commands.
- Create `code-knowledge-graph/examples/tasks.json`: honest example tasks whose gold files are relative paths in the companion project.
- Create `code-knowledge-graph/tests/test_parser.py`: parser and Git-history tests.
- Create `code-knowledge-graph/tests/test_store_retrieval.py`: SQLite, projection, PageRank, map, and scoring tests.
- Create `code-knowledge-graph/tests/test_llm.py`: request/response tests with a local fake HTTP server.
- Create `code-knowledge-graph/tests/test_cli.py`: temporary-repository CLI smoke tests.

Blog files:

- Create `dzlab.github.io/_posts/2026-08-30-building-code-knowledge-graphs.md`: source-backed standalone article linking to `https://github.com/dzlab/snippets/tree/master/code-knowledge-graph`.
- Modify `dzlab.github.io/README.md` only if the existing blog convention requires a post index entry; otherwise leave it untouched.

### Task 1: Scaffold the dependency-free project and data model

**Files:**
- Create: `code-knowledge-graph/pyproject.toml`
- Create: `code-knowledge-graph/codekg/__init__.py`
- Create: `code-knowledge-graph/codekg/__main__.py`
- Create: `code-knowledge-graph/codekg/model.py`
- Create: `code-knowledge-graph/tests/__init__.py`

- [ ] **Step 1: Define package metadata and the CLI entry point**

Create a `pyproject.toml` using `setuptools` as the build backend, require Python `>=3.11`, declare no dependencies, and expose `codekg = "codekg.cli:main"`. Keep all development tools optional so a fresh checkout can run with `python -m codekg`.

- [ ] **Step 2: Define stable dataclasses**

In `model.py`, define frozen `Node(id, kind, path, name, text="")`, frozen `Edge(src, dst, kind, weight=1.0)`, `ParsedGraph(nodes: list[Node], edges: list[Edge], warnings: list[str])`, `Task(query, gold_files)`, and `RankResult(items, scores)`. Add `to_dict()` helpers only where the CLI needs JSON output.

- [ ] **Step 3: Add the importable entry point**

Make `__main__.py` call `main()` and make `__init__.py` export the package version plus the model classes. Do not import optional network or database code at package import time.

- [ ] **Step 4: Run the scaffold smoke check**

Run:

```bash
cd /Users/bachir/co/github/dzlab/snippets/code-knowledge-graph
python3 -m codekg --help
```

Expected: the command starts and prints the CLI help once `cli.py` exists; during the scaffold step, use a temporary minimal `cli.py` only if needed, then retain the final CLI implementation from Task 5.

### Task 2: Extract source structure and Git co-edits

**Files:**
- Create: `code-knowledge-graph/codekg/parser.py`
- Create: `code-knowledge-graph/codekg/git_history.py`
- Create: `code-knowledge-graph/tests/test_parser.py`

- [ ] **Step 1: Write parser tests against a temporary source tree**

Create tests that write `pkg/api.py`, `pkg/helpers.py`, a syntax-invalid `broken.py`, and an ignored `__pycache__/ignored.py`. Assert that `scan_repository()` emits file nodes, function/class symbol nodes, `contains`, `import`, and local `call` edges, skips ignored directories, and records a warning instead of raising for `broken.py`.

- [ ] **Step 2: Implement deterministic source discovery**

Walk the repository with `pathlib`, skip `.git`, `.venv`, `venv`, `__pycache__`, `node_modules`, `vendor`, `build`, `dist`, and hidden dependency directories, and create file nodes for readable source-like files. Store normalized POSIX relative paths and bounded text (for example, 200,000 bytes) so retrieval has identifiers and short source context without loading large binaries.

- [ ] **Step 3: Implement Python AST extraction**

Parse `.py` files with `ast.parse`. Add symbol nodes for functions, async functions, and classes using qualified names; add file-to-symbol containment edges; add nested symbol containment edges; resolve local imports to known repository modules; and resolve simple `Name`/`Attribute` calls to known symbols by name. Deduplicate edges by `(src, dst, kind)` and keep stable sorted output. Catch `SyntaxError`, `UnicodeDecodeError`, and `OSError`, append a warning, and continue.

- [ ] **Step 4: Write Git co-edit tests and fallback behavior**

Create a temporary Git repository with two commits that change `pkg/api.py` and `pkg/helpers.py` together. Assert that `co_edit_edges()` returns a deterministic weighted pair. Also assert that a non-Git directory returns `[]` without raising.

- [ ] **Step 5: Implement bounded co-edit extraction**

Run `git -C REPO log --format= --name-only --diff-filter=ACMR` with a configurable commit limit. Split file lists by commit, discard paths not present in the parsed node set, skip commits above `max_files_per_commit`, count unordered file pairs, and emit one canonical edge per pair with `kind="co_edit"` and the count as weight. Treat Git command failures as an empty result plus no exception.

- [ ] **Step 6: Run parser tests**

Run:

```bash
python3 -m unittest discover -s tests -p 'test_parser.py' -v
```

Expected: all parser and Git fallback tests pass.

### Task 3: Persist the graph and implement structural retrieval

**Files:**
- Create: `code-knowledge-graph/codekg/store.py`
- Create: `code-knowledge-graph/codekg/retrieval.py`
- Create: `code-knowledge-graph/tests/test_store_retrieval.py`

- [ ] **Step 1: Write SQLite round-trip and ranking tests**

Build a tiny graph with `api.py -> service.py -> database.py`, a co-edited `test_api.py`, and a query whose lexical anchor is `api.py`. Assert that `replace_graph()` round-trips node/edge counts, the file projection is deterministic, graph ranking reaches a multi-hop neighbor, lexical ranking remains available as a baseline, recall@k is correct, and the structure map includes edge kinds.

- [ ] **Step 2: Implement SQLite schema and replacement**

Create `nodes(id TEXT PRIMARY KEY, kind TEXT NOT NULL, path TEXT, name TEXT, text TEXT)` and `edges(src TEXT NOT NULL, dst TEXT NOT NULL, kind TEXT NOT NULL, weight REAL NOT NULL, PRIMARY KEY(src, dst, kind))`, with indexes on `edges.src`, `edges.dst`, and `nodes.path`. Use one transaction to clear and insert a complete `ParsedGraph`; expose `open_store`, `replace_graph`, `counts`, and `load_file_graph`.

- [ ] **Step 3: Project symbol edges to files**

Load node IDs to file paths, map each symbol endpoint to its owning file, keep file-to-file edges with their kinds, drop same-file self edges, and add both directions to the adjacency used for retrieval. Keep import/call/containment/co-edit labels and sum repeated weights so the store remains the source of truth while traversal is simple and deterministic.

- [ ] **Step 4: Implement lexical ranking and anchors**

Tokenize lower-case identifiers, splitting snake case and path separators. Score each file by query-token overlap with relative path, basename, and stored source text; tie-break by path. Use the top `n_anchors` files as equal-weight PageRank seeds.

- [ ] **Step 5: Implement Personalized PageRank**

Use a fixed damping factor, bounded iterations, self-loops for connected nodes, teleport mass for dangling nodes, and normalized seed weights. Rank file nodes by propagated score with lexical score/path tie-breaks. Expose `lexical_rank`, `graph_rank`, `recall_at_k`, and `ndcg_at_k` so the CLI and tests share one implementation.

- [ ] **Step 6: Render a structure map**

Produce Markdown containing the query, lexical anchors, and each selected file's imports, calls, containment, and co-edit neighbors. Escape backticks and truncate long neighbor lists. Keep the output suitable for direct insertion into a system prompt.

- [ ] **Step 7: Run retrieval tests**

Run:

```bash
python3 -m unittest discover -s tests -p 'test_store_retrieval.py' -v
```

Expected: all SQLite, projection, PageRank, scoring, and map tests pass.

### Task 4: Add the OpenAI-compatible client and offline task evaluation

**Files:**
- Create: `code-knowledge-graph/codekg/llm.py`
- Create: `code-knowledge-graph/examples/tasks.json`
- Create: `code-knowledge-graph/tests/test_llm.py`

- [ ] **Step 1: Define the task-file and response tests**

Use a local `ThreadingHTTPServer` in tests. Assert that the client posts JSON to `/v1/chat/completions`, adds `Authorization: Bearer ...` only when a key is configured, accepts a base URL ending in either `/v1` or `/v1/`, parses `{"files": ["..."]}` from assistant content, strips Markdown code fences, rejects non-list or non-string file lists, and returns usage when present.

- [ ] **Step 2: Implement the minimal HTTP client**

Implement `OpenAICompatibleClient(base_url, model, api_key=None, timeout=60, temperature=0)`. Send a system message that requires a JSON object containing a ranked `files` array, plus a user message containing the task, candidate relative paths, and optional structure map. Use `urllib.request`, `json`, and `urllib.error`; surface HTTP errors with status and provider body but never print the API key.

- [ ] **Step 3: Implement robust response normalization**

Read the first assistant message, parse JSON directly or from a fenced block, normalize paths to POSIX relative strings, drop candidates not in the repository inventory, deduplicate while preserving rank, and return `(files, usage, raw_text)`. Raise a specific `LLMResponseError` for malformed content so the A/B runner can record a failed trial.

- [ ] **Step 4: Add representative tasks**

Create three tasks targeting files in the companion itself, such as locating the parser, SQLite store, and PageRank implementation. Each task must include a natural-language query and explicit `gold_files`; README instructions will explain that users should author their own gold labels for another checkout.

- [ ] **Step 5: Run client tests without network**

Run:

```bash
python3 -m unittest discover -s tests -p 'test_llm.py' -v
```

Expected: all fake-server request and parsing tests pass without credentials or external network access.

### Task 5: Build the CLI and verify it on an arbitrary checkout

**Files:**
- Create: `code-knowledge-graph/codekg/cli.py`
- Modify: `code-knowledge-graph/codekg/__main__.py`
- Create: `code-knowledge-graph/tests/test_cli.py`

- [ ] **Step 1: Write the CLI smoke test**

Create a temporary Git repository with two Python modules and a commit. Invoke the module as a subprocess for `index`, `retrieve`, `map`, and offline `experiment`, assert exit code zero, assert the index reports nonzero nodes/edges, assert retrieval names the expected anchor, assert the map contains `## Structure map`, and assert experiment JSON contains lexical and graph recall fields.

- [ ] **Step 2: Implement `index`**

Accept `REPO`, `--db`, `--max-commits`, and `--max-files-per-commit`; call parser plus Git extraction, persist the graph, and print JSON counts and warnings. Resolve all paths relative to the supplied repository, so the command works regardless of the caller's current directory.

- [ ] **Step 3: Implement `retrieve` and `map`**

Accept `--db`, `--query`, `--k`, and `--anchors`; print stable JSON for retrieve and Markdown for map. Fail with a concise message when the DB does not exist or the query is empty.

- [ ] **Step 4: Implement offline `experiment`**

Load the task JSON, run lexical and graph ranks for each task, calculate recall@1/3/5 (bounded by available files), and print a JSON report containing per-task results and aggregate means. Do not invent gold labels or claim statistical significance from a user-supplied task list.

- [ ] **Step 5: Implement paired `ab`**

For each task and run, use the same candidate inventory and model settings. The control prompt includes the task and file inventory; the treatment prompt adds the generated structure map. Record arm, task, run index, ranked files, recall, usage, and error. Support `--base-url`, `--model`, `--api-key`, `--runs`, `--seed`, `--k`, `--output`, and `--dry-run`. Require credentials only when a real request is about to be made.

- [ ] **Step 6: Finish the README and examples**

Document:

```bash
cd /path/to/code-knowledge-graph
python3 -m codekg index /path/to/any/github/checkout --db /tmp/project.sqlite
python3 -m codekg retrieve --db /tmp/project.sqlite --query "where are request validation errors handled?"
python3 -m codekg map --db /tmp/project.sqlite --query "where are request validation errors handled?" > structure-map.md
python3 -m codekg experiment --db /tmp/project.sqlite --tasks tasks.json
OPENAI_BASE_URL=http://localhost:8000/v1 OPENAI_API_KEY=... \
  python3 -m codekg ab --db /tmp/project.sqlite --tasks tasks.json --model local-model
```

Explain Python-only extraction, SQLite persistence, OpenAI-compatible configuration, task-label quality, API cost/privacy, and the difference between file localization and autonomous code editing.

- [ ] **Step 7: Run the full companion verification**

Run:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q codekg tests
git diff --check
```

Then run `index`, `retrieve`, `map`, and `experiment` against a temporary copy of an existing GitHub checkout under `/private/tmp`, not against the source repository itself. Preserve the output for article examples and inspect that the temporary DB is created outside the repository.

### Task 6: Write, build, and verify the standalone blog post

**Files:**
- Create: `/Users/bachir/co/github/dzlab/dzlab.github.io/_posts/2026-08-30-building-code-knowledge-graphs.md`

- [ ] **Step 1: Draft front matter and motivation**

Use the local post style:

```yaml
---
layout: post
comments: true
title: "Building Code Knowledge Graphs with SQLite and PageRank"
excerpt: "Build a portable code knowledge graph from a GitHub checkout and use it to retrieve structurally related files."
categories: genai
tags: [ai, agents, code-search, knowledge-graph, rag]
toc: true
img_excerpt:
mermaid: true
---
```

Explain why path/keyword search is a useful baseline but misses multi-hop dependencies and co-edited files.

- [ ] **Step 2: Explain the graph model and workflow**

Include a Mermaid diagram showing checkout → AST/Git extraction → SQLite → lexical anchors → PageRank → structure map → optional API A/B. Use a table for node and edge types. Do not mention private notebooks or local lesson paths.

- [ ] **Step 3: Show focused implementation excerpts**

Include short, accurate excerpts for AST extraction, SQLite schema, PageRank, and the OpenAI-compatible request. Explain each excerpt before showing it, and link the complete implementation to the companion project.

- [ ] **Step 4: Document reproducible commands and experiment protocol**

Show the arbitrary-checkout `index`, `retrieve`, `map`, `experiment`, and optional `ab` commands. Define control versus treatment, explicit gold files, recall@k, repeated runs, and why a chat-completions localization test is not the same as an editing-agent benchmark.

- [ ] **Step 5: Add results interpretation and production cautions**

Use only numbers reproduced from the verified local companion run or clearly label course-study numbers as prior benchmark evidence. State that graph hints are not guaranteed improvements, that lexical anchoring can dominate, and that co-edit edges reflect historical coupling rather than semantic correctness. Cover incremental updates, language support, graph freshness, privacy, prompt size, and API cost.

- [ ] **Step 6: Build and inspect the blog**

From the blog root, run:

```bash
git diff --check
make build
```

Inspect the generated post for front matter, headings, table rendering, Mermaid syntax, code fences, and the companion link. Leave unrelated blog changes untouched.

- [ ] **Step 7: Final requirement audit**

Confirm all requirements against the files and commands:

- standalone article exists and does not rely on private paths;
- extracted code lives under `snippets/code-knowledge-graph`;
- SQLite is the only required persistence layer;
- OpenAI-compatible API configuration is documented and tested offline with a fake server;
- arbitrary GitHub checkout indexing works in a temporary verification run;
- offline retrieval and evaluation work with no API key;
- full tests, compile checks, `git diff --check`, and `make build` have fresh passing output.
