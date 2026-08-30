from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path

from .model import Edge, Node, ParsedGraph

MAX_TEXT_BYTES = 200_000
IGNORED_DIR_NAMES = {
    ".git",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "vendor",
    "venv",
}
HIDDEN_DEPENDENCY_DIR_NAMES = {
    ".cache",
    ".eggs",
    ".hypothesis",
    ".mypy_cache",
    ".nox",
    ".parcel-cache",
    ".pnpm-store",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".yarn",
}
SOURCE_EXTENSIONS = {
    "",
    ".c",
    ".cc",
    ".cfg",
    ".conf",
    ".cpp",
    ".css",
    ".csv",
    ".go",
    ".h",
    ".hpp",
    ".html",
    ".ini",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".kt",
    ".md",
    ".php",
    ".proto",
    ".py",
    ".pyi",
    ".rb",
    ".rs",
    ".rst",
    ".scss",
    ".sh",
    ".sql",
    ".svg",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
    ".zsh",
}
SOURCE_FILENAMES = {"Dockerfile", "Makefile"}


@dataclass
class ScopeInfo:
    node_id: str
    qname: str | None
    class_qname: str | None = None
    local_symbols: dict[str, str] = field(default_factory=dict)
    imported_modules: dict[str, str] = field(default_factory=dict)
    imported_symbols: dict[str, str] = field(default_factory=dict)


@dataclass
class PythonFileInfo:
    rel_path: str
    file_node_id: str
    module_name: str | None
    package_name: str | None
    tree: ast.AST
    module_scope: ScopeInfo
    symbol_scopes: dict[str, ScopeInfo]


class SymbolCollector(ast.NodeVisitor):
    def __init__(self, rel_path: str, file_node_id: str, module_name: str | None) -> None:
        self.rel_path = rel_path
        self.file_node_id = file_node_id
        self.module_scope = ScopeInfo(node_id=file_node_id, qname=module_name)
        self.scope_stack: list[ScopeInfo] = [self.module_scope]
        self.symbol_scopes: dict[str, ScopeInfo] = {}
        self.nodes: dict[str, Node] = {}
        self.edges: set[tuple[str, str, str]] = set()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._visit_symbol(node, kind="class", class_qname=None)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_symbol(node, kind="function", class_qname=self._current_class_qname())

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_symbol(
            node,
            kind="async_function",
            class_qname=self._current_class_qname(),
        )

    def _visit_symbol(
        self,
        node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
        *,
        kind: str,
        class_qname: str | None,
    ) -> None:
        parent_scope = self.scope_stack[-1]
        qname = _join_qname(parent_scope.qname, node.name)
        if qname is None:
            return

        node_id = f"symbol:{qname}"
        self.nodes[node_id] = Node(
            id=node_id,
            kind=kind,
            path=self.rel_path,
            name=qname,
        )
        self.edges.add((parent_scope.node_id, node_id, "contains"))
        parent_scope.local_symbols[node.name] = node_id

        if kind == "class":
            class_qname = qname

        scope = ScopeInfo(node_id=node_id, qname=qname, class_qname=class_qname)
        self.symbol_scopes[qname] = scope
        self.scope_stack.append(scope)
        self.generic_visit(node)
        self.scope_stack.pop()

    def _current_class_qname(self) -> str | None:
        for scope in reversed(self.scope_stack):
            if scope.class_qname is not None:
                return scope.class_qname
        return None


class ReferenceResolver(ast.NodeVisitor):
    def __init__(
        self,
        file_info: PythonFileInfo,
        module_file_ids: dict[str, str],
        symbol_ids: dict[str, str],
        edge_keys: set[tuple[str, str, str]],
    ) -> None:
        self.file_info = file_info
        self.module_file_ids = module_file_ids
        self.symbol_ids = symbol_ids
        self.edge_keys = edge_keys
        self.scope_stack: list[ScopeInfo] = [file_info.module_scope]

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._visit_symbol_scope(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_symbol_scope(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_symbol_scope(node)

    def visit_Import(self, node: ast.Import) -> None:
        current_scope = self.scope_stack[-1]
        for alias in node.names:
            module_name = alias.name
            if module_name in self.module_file_ids:
                current_scope.imported_modules[alias.asname or module_name.split(".")[-1]] = module_name
                self.edge_keys.add(
                    (
                        self.file_info.file_node_id,
                        self.module_file_ids[module_name],
                        "imports",
                    )
                )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        current_scope = self.scope_stack[-1]
        base_module = _resolve_relative_module(
            self.file_info.package_name,
            node.level,
            node.module,
        )
        if base_module is None:
            return

        for alias in node.names:
            target_module = _join_qname(base_module, alias.name)
            alias_name = alias.asname or alias.name

            if target_module in self.module_file_ids:
                current_scope.imported_modules[alias_name] = target_module
                self.edge_keys.add(
                    (
                        self.file_info.file_node_id,
                        self.module_file_ids[target_module],
                        "imports",
                    )
                )
                continue

            target_symbol = _join_qname(base_module, alias.name)
            if target_symbol in self.symbol_ids:
                current_scope.imported_symbols[alias_name] = self.symbol_ids[target_symbol]
                if base_module in self.module_file_ids:
                    self.edge_keys.add(
                        (
                            self.file_info.file_node_id,
                            self.module_file_ids[base_module],
                            "imports",
                        )
                    )
                continue

            if base_module in self.module_file_ids:
                self.edge_keys.add(
                    (
                        self.file_info.file_node_id,
                        self.module_file_ids[base_module],
                        "imports",
                    )
                )

    def visit_Call(self, node: ast.Call) -> None:
        target_id = self._resolve_callable(node.func)
        if target_id is not None:
            self.edge_keys.add((self.scope_stack[-1].node_id, target_id, "calls"))
        self.generic_visit(node)

    def _visit_symbol_scope(
        self,
        node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> None:
        qname = _join_qname(self.scope_stack[-1].qname, node.name)
        if qname is None:
            self.generic_visit(node)
            return

        scope = self.file_info.symbol_scopes[qname]
        self.scope_stack.append(scope)
        self.generic_visit(node)
        self.scope_stack.pop()

    def _resolve_callable(self, node: ast.AST) -> str | None:
        if isinstance(node, ast.Name):
            return self._resolve_name(node.id)

        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            base_name = node.value.id

            if base_name in {"self", "cls"}:
                class_qname = self._current_class_qname()
                if class_qname is not None:
                    return self.symbol_ids.get(f"{class_qname}.{node.attr}")

            module_name = self._resolve_module_alias(base_name)
            if module_name is not None:
                return self.symbol_ids.get(f"{module_name}.{node.attr}")

            symbol_id = self._resolve_name(base_name)
            if symbol_id is not None:
                symbol_qname = symbol_id.removeprefix("symbol:")
                return self.symbol_ids.get(f"{symbol_qname}.{node.attr}")

        return None

    def _resolve_name(self, name: str) -> str | None:
        for scope in reversed(self.scope_stack):
            if name in scope.local_symbols:
                return scope.local_symbols[name]
            if name in scope.imported_symbols:
                return scope.imported_symbols[name]
        return None

    def _resolve_module_alias(self, name: str) -> str | None:
        for scope in reversed(self.scope_stack):
            if name in scope.imported_modules:
                return scope.imported_modules[name]
        return None

    def _current_class_qname(self) -> str | None:
        for scope in reversed(self.scope_stack):
            if scope.class_qname is not None:
                return scope.class_qname
        return None


def scan_repository(repo_root: str | Path) -> ParsedGraph:
    root = Path(repo_root)
    node_map: dict[str, Node] = {}
    edge_keys: set[tuple[str, str, str]] = set()
    warnings: list[str] = []
    python_files: list[PythonFileInfo] = []
    module_file_ids: dict[str, str] = {}
    symbol_ids: dict[str, str] = {}

    for file_path in _iter_repository_files(root):
        rel_path = file_path.relative_to(root).as_posix()
        if not _is_source_like(file_path):
            continue

        try:
            raw_bytes = _read_bounded_bytes(file_path)
            if b"\x00" in raw_bytes:
                continue
            text = raw_bytes.decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            warnings.append(f"{rel_path}: {exc.__class__.__name__}: {exc}")
            continue

        file_node_id = f"file:{rel_path}"
        node_map[file_node_id] = Node(
            id=file_node_id,
            kind="file",
            path=rel_path,
            name=file_path.name,
            text=text,
        )

        if file_path.suffix != ".py":
            continue

        try:
            tree = ast.parse(text, filename=rel_path)
        except SyntaxError as exc:
            warnings.append(f"{rel_path}: SyntaxError: {exc.msg}")
            continue

        module_name = _module_name_for_path(rel_path)
        package_name = _package_name_for_module(module_name, rel_path)
        if module_name is not None:
            module_file_ids[module_name] = file_node_id

        collector = SymbolCollector(rel_path, file_node_id, module_name)
        collector.visit(tree)
        node_map.update(collector.nodes)
        edge_keys.update(collector.edges)
        for qname, scope in collector.symbol_scopes.items():
            symbol_ids[qname] = scope.node_id
        python_files.append(
            PythonFileInfo(
                rel_path=rel_path,
                file_node_id=file_node_id,
                module_name=module_name,
                package_name=package_name,
                tree=tree,
                module_scope=collector.module_scope,
                symbol_scopes=collector.symbol_scopes,
            )
        )

    for file_info in python_files:
        resolver = ReferenceResolver(file_info, module_file_ids, symbol_ids, edge_keys)
        resolver.visit(file_info.tree)

    nodes = sorted(node_map.values(), key=_node_sort_key)
    edges = [
        Edge(src=src, dst=dst, kind=kind)
        for src, dst, kind in sorted(edge_keys, key=lambda item: (item[2], item[0], item[1]))
    ]
    return ParsedGraph(nodes=nodes, edges=edges, warnings=sorted(warnings))


def _iter_repository_files(repo_root: Path) -> list[Path]:
    files: list[Path] = []
    stack = [repo_root]
    while stack:
        current = stack.pop()
        try:
            children = sorted(current.iterdir(), key=lambda path: path.name)
        except OSError:
            continue

        directories: list[Path] = []
        for child in children:
            if child.is_dir():
                if not _should_skip_dir(child):
                    directories.append(child)
                continue
            if child.is_file():
                files.append(child)

        stack.extend(reversed(directories))
    return files


def _should_skip_dir(path: Path) -> bool:
    name = path.name
    if name in IGNORED_DIR_NAMES or name in HIDDEN_DEPENDENCY_DIR_NAMES:
        return True
    if not name.startswith("."):
        return False
    dependency_tokens = ("cache", "env", "mypy", "nox", "pytest", "ruff", "tox", "venv", "yarn")
    return any(token in name for token in dependency_tokens)


def _is_source_like(path: Path) -> bool:
    return path.name in SOURCE_FILENAMES or path.suffix.lower() in SOURCE_EXTENSIONS


def _read_bounded_bytes(path: Path) -> bytes:
    with path.open("rb") as handle:
        return handle.read(MAX_TEXT_BYTES)


def _module_name_for_path(rel_path: str) -> str | None:
    path = Path(rel_path)
    if path.name == "__init__.py":
        return ".".join(path.parts[:-1]) or None
    module_parts = list(path.with_suffix("").parts)
    return ".".join(module_parts) or None


def _join_qname(base: str | None, name: str) -> str | None:
    if base is None:
        return name
    if not base:
        return name
    return f"{base}.{name}"


def _resolve_relative_module(
    current_package: str | None,
    level: int,
    imported_module: str | None,
) -> str | None:
    if level == 0:
        return imported_module
    if current_package is None:
        return imported_module

    package_parts = [part for part in current_package.split(".") if part]
    ascend = max(level - 1, 0)
    if ascend:
        package_parts = package_parts[: max(len(package_parts) - ascend, 0)]
    base_module = ".".join(package_parts)
    if imported_module:
        return _join_qname(base_module, imported_module)
    return base_module or None


def _node_sort_key(node: Node) -> tuple[int, str, str, str]:
    kind_order = 0 if node.kind == "file" else 1
    return (kind_order, node.path, node.kind, node.name)


def _package_name_for_module(module_name: str | None, rel_path: str) -> str | None:
    if module_name is None:
        return None
    if Path(rel_path).name == "__init__.py":
        return module_name
    package_name, _, _ = module_name.rpartition(".")
    return package_name or None
