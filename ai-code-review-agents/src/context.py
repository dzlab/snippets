"""Repository chunking, embedding, and retrieval."""

from __future__ import annotations

import ast
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openai import OpenAI


@dataclass(frozen=True)
class Chunk:
    content: str
    type: str
    name: str
    file_path: str
    line_start: int
    line_end: int


class CodeChunker(ast.NodeVisitor):
    def __init__(self, source_code: str, file_path: str):
        self.source_code = source_code
        self.file_path = file_path
        self.source_lines = source_code.splitlines()
        self.chunks: list[Chunk] = []

    def _source_segment(self, node: ast.AST) -> str:
        if not hasattr(node, "lineno") or not hasattr(node, "end_lineno"):
            return ""
        return "\n".join(self.source_lines[node.lineno - 1 : node.end_lineno])

    def visit_FunctionDef(self, node: ast.FunctionDef):
        chunk_type = "test" if node.name.startswith("test_") else "function"
        self.chunks.append(Chunk(
            content=self._source_segment(node),
            type=chunk_type,
            name=node.name,
            file_path=self.file_path,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
        ))

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.chunks.append(Chunk(
            content=self._source_segment(node),
            type="function",
            name=node.name,
            file_path=self.file_path,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
        ))

    def visit_ClassDef(self, node: ast.ClassDef):
        self.chunks.append(Chunk(
            content=self._source_segment(node),
            type="class",
            name=node.name,
            file_path=self.file_path,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
        ))
        self.generic_visit(node)


def chunk_code(source_code: str, file_path: str) -> list[Chunk]:
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return []

    chunker = CodeChunker(source_code, file_path)
    chunker.visit(tree)
    return chunker.chunks


def chunk_repository(repo_files: dict[str, str]) -> list[Chunk]:
    chunks: list[Chunk] = []
    for file_path, source_code in repo_files.items():
        if file_path.endswith(".py"):
            chunks.extend(chunk_code(source_code, file_path))
    return chunks


def chunk_to_text(chunk: Chunk) -> str:
    return (
        f"{chunk.type}: {chunk.name}\n"
        f"file: {chunk.file_path}:{chunk.line_start}-{chunk.line_end}\n\n"
        f"{chunk.content}"
    )


def embed_chunks(
    chunks: list[Chunk],
    openai_client: "OpenAI",
    model: str = "text-embedding-3-large",
    batch_size: int = 100,
) -> list[dict]:
    texts = [chunk_to_text(chunk) for chunk in chunks]
    embeddings = []

    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        response = openai_client.embeddings.create(model=model, input=batch)
        embeddings.extend(item.embedding for item in response.data)

    return [
        {
            "chunk": chunk,
            "text": text,
            "embedding": embedding,
            "metadata": {
                "type": chunk.type,
                "name": chunk.name,
                "file_path": chunk.file_path,
                "line_start": chunk.line_start,
                "line_end": chunk.line_end,
            },
        }
        for chunk, text, embedding in zip(chunks, texts, embeddings)
    ]


class ContextRetriever:
    def __init__(
        self,
        openai_client: "OpenAI",
        collection_name: str = "code_chunks",
        embedding_model: str = "text-embedding-3-large",
    ):
        import chromadb
        from chromadb.config import Settings

        self.openai_client = openai_client
        self.embedding_model = embedding_model
        self.client = chromadb.Client(Settings(
            anonymized_telemetry=False,
            is_persistent=False,
        ))
        self.collection_name = collection_name
        self.collection = None

    def create_index(self, embedded_chunks: list[dict]):
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass

        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "Code chunks for AI review context"},
        )
        self.collection.add(
            ids=[f"chunk_{idx}" for idx in range(len(embedded_chunks))],
            embeddings=[item["embedding"] for item in embedded_chunks],
            documents=[item["text"] for item in embedded_chunks],
            metadatas=[item["metadata"] for item in embedded_chunks],
        )

    def retrieve(self, query: str, n_results: int = 5) -> list[dict]:
        if self.collection is None:
            raise ValueError("Index not created. Call create_index() first.")

        response = self.openai_client.embeddings.create(
            model=self.embedding_model,
            input=query,
        )
        query_embedding = response.data[0].embedding
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
        )

        return [
            {
                "content": results["documents"][0][idx],
                "metadata": results["metadatas"][0][idx],
                "distance": results["distances"][0][idx],
            }
            for idx in range(len(results["ids"][0]))
        ]

    def retrieve_for_pr(self, pr: dict, n_results: int = 10) -> str:
        query = f"{pr['title']}\n\n{pr['diff']}"
        results = self.retrieve(query, n_results=n_results)
        context_parts = []

        for item in results:
            meta = item["metadata"]
            context_parts.append(
                f"# {meta['type']}: {meta['name']} "
                f"({meta['file_path']}:{meta['line_start']}-{meta['line_end']})\n"
                f"{item['content']}"
            )

        return "\n\n".join(context_parts)


def build_selective_context_fn(
    repo: dict[str, str],
    openai_client: "OpenAI",
    embedding_model: str = "text-embedding-3-large",
    n_results: int = 10,
) -> Callable[[dict], str]:
    chunks = chunk_repository(repo)
    embedded_chunks = embed_chunks(chunks, openai_client, model=embedding_model)

    retriever = ContextRetriever(
        openai_client=openai_client,
        embedding_model=embedding_model,
    )
    retriever.create_index(embedded_chunks)

    def context_fn(pr: dict) -> str:
        return retriever.retrieve_for_pr(pr, n_results=n_results)

    return context_fn


def full_repository_context(repo: dict[str, str]) -> Callable[[dict], str]:
    context = "\n\n".join(f"# {path}\n{content}" for path, content in repo.items())
    return lambda _: context
