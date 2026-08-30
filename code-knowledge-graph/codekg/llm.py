from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import PurePosixPath
from urllib import error, request

MAX_COMPLETION_TOKENS = 256
MAX_RESPONSE_BYTES = 64 * 1024


class LLMRequestError(RuntimeError):
    pass


class LLMResponseError(ValueError):
    pass


@dataclass(frozen=True)
class LLMRankResult:
    files: list[str]
    usage: dict[str, int]
    raw_text: str


class OpenAICompatibleClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str | None = None,
        timeout: float = 60,
        temperature: float = 0,
    ) -> None:
        self.base_url = _normalize_base_url(base_url)
        self.model = model
        self.api_key = api_key
        self.timeout = timeout
        self.temperature = temperature

    def rank_files(
        self,
        task: str,
        candidate_paths: list[str],
        *,
        structure_map: str | None = None,
    ) -> LLMRankResult:
        inventory = _normalize_inventory(candidate_paths)
        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": MAX_COMPLETION_TOKENS,
            "messages": self._build_messages(
                task=task,
                candidate_paths=inventory,
                structure_map=structure_map,
            ),
        }
        response = self._post_json("/chat/completions", payload)
        raw_text = _extract_assistant_text(response)
        content = _parse_ranked_files_object(raw_text)
        ranked_files = content.get("ranked_files", content.get("files"))
        if not isinstance(ranked_files, list):
            raise LLMResponseError(
                "assistant message must contain a valid JSON object with a ranked_files array"
            )

        files = _filter_ranked_files(ranked_files, inventory)
        usage = response.get("usage", {})
        if not isinstance(usage, dict):
            usage = {}
        return LLMRankResult(files=files, usage=usage, raw_text=raw_text)

    def _build_messages(
        self,
        *,
        task: str,
        candidate_paths: list[str],
        structure_map: str | None,
    ) -> list[dict[str, str]]:
        user_lines = [
            "Task:",
            task,
            "",
            "Candidate Relative Paths:",
            *candidate_paths,
        ]
        if structure_map:
            user_lines.extend(["", "Structure Map:", structure_map])
        return [
            {
                "role": "system",
                "content": (
                    "Return a JSON object containing a ranked_files array. "
                    "Each item must be a repository-relative POSIX path ordered from most to least relevant."
                ),
            },
            {"role": "user", "content": "\n".join(user_lines)},
        ]

    def _post_json(self, path: str, payload: dict[str, object]) -> dict[str, object]:
        body = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        http_request = request.Request(
            url=f"{self.base_url}{path}",
            data=body,
            headers=headers,
            method="POST",
        )

        try:
            with request.urlopen(http_request, timeout=self.timeout) as response:
                response_body = _read_limited(
                    response,
                    limit=MAX_RESPONSE_BYTES,
                    error_type=LLMResponseError,
                    message="OpenAI-compatible response body is too large",
                )
                return _decode_response_payload(response_body)
        except error.HTTPError as exc:
            try:
                provider_body = _read_limited(
                    exc,
                    limit=MAX_RESPONSE_BYTES,
                    error_type=LLMRequestError,
                    message=(
                        f"OpenAI-compatible request failed with status {exc.code}: "
                        "provider error body is too large"
                    ),
                ).decode("utf-8", errors="replace")
            finally:
                exc.close()
            raise LLMRequestError(
                f"OpenAI-compatible request failed with status {exc.code}: "
                f"{_redact_secret(provider_body, self.api_key)}"
            ) from exc
        except error.URLError as exc:
            raise LLMRequestError(f"OpenAI-compatible request failed: {exc.reason}") from exc


def _normalize_base_url(base_url: str) -> str:
    trimmed = base_url.rstrip("/")
    if trimmed.endswith("/v1"):
        return trimmed
    return f"{trimmed}/v1"


def _normalize_inventory(candidate_paths: list[str]) -> list[str]:
    inventory: list[str] = []
    seen: set[str] = set()
    for path in candidate_paths:
        normalized = _normalize_relative_path(path)
        if normalized is None or normalized in seen:
            continue
        seen.add(normalized)
        inventory.append(normalized)
    return inventory


def _extract_assistant_text(payload: dict[str, object]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list):
        raise LLMResponseError("response is missing an assistant message")

    for choice in choices:
        if not isinstance(choice, dict):
            continue
        message = choice.get("message")
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, dict) and isinstance(item.get("text"), str):
                    parts.append(item["text"])
            if parts:
                return "\n".join(parts)
    raise LLMResponseError("response is missing an assistant message")


def _parse_ranked_files_object(raw_text: str) -> dict[str, object]:
    for candidate in (raw_text.strip(), _extract_fenced_json(raw_text)):
        if not candidate:
            continue
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    raise LLMResponseError(
        "assistant message must contain a valid JSON object with a ranked_files array"
    )


def _extract_fenced_json(raw_text: str) -> str | None:
    fence_start = raw_text.find("```")
    while fence_start != -1:
        line_end = raw_text.find("\n", fence_start)
        if line_end == -1:
            return None
        fence_label = raw_text[fence_start + 3 : line_end].strip().lower()
        fence_close = raw_text.find("```", line_end + 1)
        if fence_close == -1:
            return None
        if fence_label in {"", "json"}:
            return raw_text[line_end + 1 : fence_close].strip()
        fence_start = raw_text.find("```", fence_close + 3)
    return None


def _filter_ranked_files(ranked_files: list[object], inventory: list[str]) -> list[str]:
    allowed = set(inventory)
    filtered: list[str] = []
    seen: set[str] = set()
    for item in ranked_files:
        if not isinstance(item, str):
            continue
        normalized = _normalize_relative_path(item)
        if normalized is None or normalized not in allowed or normalized in seen:
            continue
        seen.add(normalized)
        filtered.append(normalized)
    return filtered


def _normalize_relative_path(value: str) -> str | None:
    if _has_windows_drive_prefix(value):
        return None

    path = PurePosixPath(value.replace("\\", "/"))
    if path.is_absolute():
        return None

    parts: list[str] = []
    for part in path.parts:
        if part in {"", "."}:
            continue
        if part == "..":
            return None
        parts.append(part)

    if not parts:
        return None
    return PurePosixPath(*parts).as_posix()


def _has_windows_drive_prefix(value: str) -> bool:
    return len(value) >= 2 and value[0].isalpha() and value[1] == ":"


def _read_limited(
    response,
    *,
    limit: int,
    error_type: type[Exception],
    message: str,
) -> bytes:
    body = response.read(limit + 1)
    if len(body) > limit:
        raise error_type(message)
    return body


def _decode_response_payload(raw_body: bytes) -> dict[str, object]:
    try:
        text = raw_body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise LLMResponseError("OpenAI-compatible response body is not valid UTF-8") from exc

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMResponseError("OpenAI-compatible response body is not valid JSON") from exc

    if not isinstance(payload, dict):
        raise LLMResponseError(
            "OpenAI-compatible response body must be a top-level JSON object"
        )
    return payload


def _redact_secret(value: str, secret: str | None) -> str:
    if secret:
        return value.replace(secret, "[REDACTED]")
    return value
