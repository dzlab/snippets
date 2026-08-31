# Portable Code Knowledge Graph Design

## Goal

Create a self-contained technical article and companion project that shows how to build a code knowledge graph for an arbitrary local GitHub checkout, retrieve structurally related files, and compare graph-assisted localization with lexical retrieval. The companion must run without Oracle, a vector database, or an LLM API, while supporting an optional OpenAI-compatible chat-completions endpoint for control-versus-graph-context trials.

## Scope

The deliverable has two coordinated parts:

1. `snippets/code-knowledge-graph/`: a runnable Python project with a CLI, SQLite persistence, Python source parsing, Git co-edit extraction, graph retrieval, Markdown structure-map generation, and optional OpenAI-compatible A/B localization.
2. `dzlab.github.io/_posts/2026-08-30-building-code-knowledge-graphs.md`: a standalone Jekyll article explaining the problem, graph model, implementation, retrieval algorithm, experiment protocol, limitations, and reproducible commands. It links to the public companion repository rather than depending on private lesson paths.

The canonical experiment is file localization, not autonomous editing. The concrete article walkthrough uses the local `chess-studio` GitHub checkout as its dataset rather than an invented toy graph. The optional API mode asks a model to rank candidate files for a task in two conditions: the task alone and the task plus the generated structure map. The project reports recall@k and any usage fields returned by the API. A no-API mode compares lexical ranking and graph-expanded ranking on the same task definitions.

## Recommended architecture

Use only the Python standard library for the core path:

- `ast` extracts Python file, class, function, import, call, and containment relationships.
- `subprocess` invokes read-only Git commands to derive co-edit relationships from commit history.
- `sqlite3` stores nodes and typed directed edges, with indexes for traversal and inspection.
- A small deterministic tokenizer seeds lexical retrieval.
- Personalized PageRank propagates seed mass across the graph and ranks structurally related files.
- `urllib.request` calls any endpoint implementing OpenAI-compatible `POST /v1/chat/completions`; the base URL, model, API key, timeout, and temperature are CLI/environment configuration.

The core must degrade gracefully:

- Non-Python files remain file nodes and can participate in imports/co-edits when relationships are visible from Python code or Git history.
- Parse failures are recorded as warnings and do not abort the full repository scan.
- Repositories without Git history still produce a file/symbol/import/call graph; co-edit edges are simply absent.
- Missing API credentials make the `ab` command fail with a clear setup message, while `index`, `retrieve`, `map`, and offline experiment commands continue to work.
- API responses must be validated for an assistant message and a JSON ranking payload; malformed responses are reported per trial rather than silently treated as successes.

## Components and interfaces

### `codekg/parser.py`

Expose `scan_repository(repo_root) -> ParsedGraph`. Walk tracked or source files while skipping common generated and dependency directories. Emit stable relative-path node IDs and symbol IDs, plus typed raw edges. Keep parser output independent of SQLite so it can be unit tested directly.

### `codekg/git_history.py`

Expose `co_edit_edges(repo_root, max_commits, max_files_per_commit) -> list[Edge]`. Read commit file lists using Git, form bounded pairwise co-edit edges, and keep the newest/strongest relationship as an edge weight. Return an empty list when the directory is not a Git checkout or history cannot be read.

### `codekg/store.py`

Create the SQLite schema, replace a database from parsed graph data, expose node/edge counts, and return an in-memory adjacency representation for ranking. The schema uses `nodes(id, kind, path, name, text)` and `edges(src, dst, kind, weight)` with primary/lookup indexes. SQLite is the durable store; PageRank does not require a graph-specific database extension.

### `codekg/retrieval.py`

Implement shared identifier tokenization, lexical file ranking, anchor selection, personalized PageRank, recall@k, and structure-map rendering. The default graph rank uses one or more lexical anchors and traverses imports, calls, containment, and co-edit edges. Results must be deterministic under a fixed database and task.

### `codekg/llm.py`

Implement a minimal OpenAI-compatible client using JSON over HTTP. Send a system instruction requiring a JSON array of relative file paths, include the task and either no graph context or the generated structure map, and parse the response into ranked paths. Do not require the `openai` Python package; this keeps compatibility with OpenAI, local servers, and hosted providers that implement the same endpoint.

### `codekg/cli.py`

Provide the user-facing commands:

- `index REPO --db PATH`: build or replace the SQLite graph.
- `retrieve --db PATH --query TEXT --k N`: print lexical and graph-ranked files.
- `map --db PATH --query TEXT --k N`: print a Markdown structure map for an agent prompt.
- `experiment --db PATH --tasks PATH`: run offline lexical-versus-graph recall evaluation.
- `ab --db PATH --tasks PATH --base-url URL --model MODEL`: run paired API localization trials, with `--runs`, `--seed`, and `--dry-run` controls.

Task files are small JSON documents containing a query and one or more gold relative paths. This makes the experiment reproducible on any repository without pretending that automatically generated labels are ground truth.

## Data flow

```text
target Git checkout
        |
        v
 AST parser + Git history
        |
        v
 SQLite nodes/typed edges
        |
        +--> lexical anchors --> Personalized PageRank --> structure map
        |                                              |
        +--> offline recall comparison                +--> optional API A/B
                                                        control: task only
                                                        treatment: task + map
```

The article will start with the real `chess-studio` repository graph, then show the file-level projection, compare lexical and graph rankings, and finally explain the paired evaluation. It will explain that the graph is a navigation hint: it can surface dependencies and historically coupled files that do not share the task vocabulary, but it does not guarantee that an agent will choose or edit them.

## Testing and verification

The companion project will include tests for:

- AST extraction of files, functions/classes, imports, calls, and containment.
- Stable handling of syntax errors and ignored directories.
- Co-edit pair generation and Git-unavailable fallback.
- SQLite round-trip counts and typed-edge queries.
- PageRank behavior on a small multi-hop graph and deterministic tie-breaking.
- Structure-map output and task scoring.
- OpenAI-compatible request construction and response parsing using a local fake HTTP server, without network access.
- CLI smoke tests against a temporary Git repository.

Verification will run the full test suite, compile/import checks, an offline CLI experiment against a temporary repository, `git diff --check`, and the blog repository's `make build`.

## Article shape

The post will use the blog's existing front matter and organize the narrative as:

1. Why flat text search misses code relationships.
2. The graph model, grounded in a real `chess-studio` checkout.
3. A portable SQLite implementation and repository-level visualization.
4. Anchor retrieval plus a direct PageRank-versus-keyword comparison.
5. Running the experiment on an arbitrary GitHub checkout.
6. Optional OpenAI-compatible control/treatment trials.
7. A separate Django coding-workflow case study, with explicit uncertainty.
8. Interpreting results and avoiding overstated claims.
9. Production extensions and conclusion.

Code excerpts will be short and concept-focused; the companion project will contain the complete runnable implementation.
