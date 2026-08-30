import json
import threading
import unittest
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from codekg.llm import LLMRequestError, LLMResponseError, OpenAICompatibleClient


@dataclass
class RecordedRequest:
    path: str
    headers: dict[str, str]
    body: dict[str, object]


class _TestHandler(BaseHTTPRequestHandler):
    responses: list[tuple[int, dict[str, str], bytes]] = []
    requests: list[RecordedRequest] = []

    def do_POST(self) -> None:  # noqa: N802
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)
        body = json.loads(raw_body.decode("utf-8"))
        self.__class__.requests.append(
            RecordedRequest(
                path=self.path,
                headers={key: value for key, value in self.headers.items()},
                body=body,
            )
        )

        status, headers, payload = self.__class__.responses.pop(0)
        self.send_response(status)
        for key, value in headers.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        return


class _ThreadingHTTPServer(ThreadingHTTPServer):
    def server_bind(self) -> None:
        self.socket.bind(self.server_address)
        self.server_address = self.socket.getsockname()


class TestHTTPServer:
    def __init__(self) -> None:
        self.server = _ThreadingHTTPServer(("127.0.0.1", 0), _TestHandler)
        _TestHandler.responses = []
        _TestHandler.requests = []
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self) -> "TestHTTPServer":
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    @property
    def base_url(self) -> str:
        host, port = self.server.server_address
        return f"http://{host}:{port}"

    def enqueue_json(self, payload: dict[str, object], status: int = 200) -> None:
        _TestHandler.responses.append(
            (
                status,
                {"Content-Type": "application/json"},
                json.dumps(payload).encode("utf-8"),
            )
        )

    def enqueue_text(self, payload: str, status: int) -> None:
        _TestHandler.responses.append(
            (
                status,
                {"Content-Type": "text/plain; charset=utf-8"},
                payload.encode("utf-8"),
            )
        )

    @property
    def requests(self) -> list[RecordedRequest]:
        return list(_TestHandler.requests)


class OpenAICompatibleClientTest(unittest.TestCase):
    def test_rank_files_posts_expected_request_and_parses_direct_json(self):
        with TestHTTPServer() as server:
            server.enqueue_json(
                {
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": (
                                    '{"ranked_files": ["./codekg/parser.py", '
                                    '"codekg/store.py", "codekg/parser.py", "missing.py"]}'
                                ),
                            }
                        }
                    ],
                    "usage": {"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18},
                }
            )

            client = OpenAICompatibleClient(
                base_url=f"{server.base_url}/v1",
                model="openai/test-model",
                api_key="sk-test-secret",
                temperature=0.25,
            )

            result = client.rank_files(
                task="Find where Python files are parsed into graph nodes.",
                candidate_paths=["codekg/parser.py", "codekg/store.py"],
                structure_map="### `codekg/parser.py`\n- contains: `codekg/store.py`",
            )

        self.assertEqual(["codekg/parser.py", "codekg/store.py"], result.files)
        self.assertEqual(
            {"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18},
            result.usage,
        )
        self.assertIn('"ranked_files"', result.raw_text)

        self.assertEqual(1, len(server.requests))
        request = server.requests[0]
        self.assertEqual("/v1/chat/completions", request.path)
        self.assertEqual("Bearer sk-test-secret", request.headers["Authorization"])
        self.assertEqual("application/json", request.headers["Content-Type"])
        self.assertEqual("openai/test-model", request.body["model"])
        self.assertEqual(0.25, request.body["temperature"])

        messages = request.body["messages"]
        self.assertEqual("system", messages[0]["role"])
        self.assertIn("JSON object", messages[0]["content"])
        self.assertIn("ranked_files", messages[0]["content"])
        self.assertEqual("user", messages[1]["role"])
        self.assertIn("Task:", messages[1]["content"])
        self.assertIn("Candidate Relative Paths:", messages[1]["content"])
        self.assertIn("codekg/parser.py", messages[1]["content"])
        self.assertIn("Structure Map:", messages[1]["content"])

    def test_base_url_accepts_v1_with_or_without_trailing_slash(self):
        with TestHTTPServer() as server:
            for base_url in (f"{server.base_url}/v1", f"{server.base_url}/v1/"):
                server.enqueue_json(
                    {
                        "choices": [
                            {
                                "message": {
                                    "role": "assistant",
                                    "content": '{"ranked_files": ["codekg/retrieval.py"]}',
                                }
                            }
                        ]
                    }
                )

                client = OpenAICompatibleClient(base_url=base_url, model="local-model")
                result = client.rank_files(
                    task="Find ranking logic.",
                    candidate_paths=["codekg/retrieval.py"],
                )
                self.assertEqual(["codekg/retrieval.py"], result.files)

        self.assertEqual(
            ["/v1/chat/completions", "/v1/chat/completions"],
            [request.path for request in server.requests],
        )

    def test_rank_files_parses_fenced_json_block(self):
        with TestHTTPServer() as server:
            server.enqueue_json(
                {
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": (
                                    "Here is the ranking.\n```json\n"
                                    '{"ranked_files": ["codekg/retrieval.py"]}\n'
                                    "```"
                                ),
                            }
                        }
                    ]
                }
            )

            client = OpenAICompatibleClient(base_url=server.base_url, model="local-model")
            result = client.rank_files(
                task="Find where PageRank-style propagation happens.",
                candidate_paths=["codekg/retrieval.py", "codekg/store.py"],
            )

        self.assertEqual(["codekg/retrieval.py"], result.files)

    def test_rank_files_raises_for_malformed_content(self):
        with TestHTTPServer() as server:
            server.enqueue_json(
                {
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": "not json",
                            }
                        }
                    ]
                }
            )

            client = OpenAICompatibleClient(base_url=server.base_url, model="local-model")

            with self.assertRaisesRegex(LLMResponseError, "valid JSON"):
                client.rank_files(
                    task="Find parser code.",
                    candidate_paths=["codekg/parser.py"],
                )

    def test_rank_files_raises_when_assistant_message_is_missing(self):
        with TestHTTPServer() as server:
            server.enqueue_json({"choices": [{"message": {"role": "user", "content": "hi"}}]})

            client = OpenAICompatibleClient(base_url=server.base_url, model="local-model")

            with self.assertRaisesRegex(LLMResponseError, "assistant message"):
                client.rank_files(
                    task="Find parser code.",
                    candidate_paths=["codekg/parser.py"],
                )

    def test_rank_files_omits_authorization_header_when_api_key_is_missing(self):
        with TestHTTPServer() as server:
            server.enqueue_json(
                {
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": '{"ranked_files": ["codekg/parser.py"]}',
                            }
                        }
                    ]
                }
            )

            client = OpenAICompatibleClient(base_url=server.base_url, model="local-model")
            client.rank_files(
                task="Find parser code.",
                candidate_paths=["codekg/parser.py"],
            )

        self.assertNotIn("Authorization", server.requests[0].headers)

    def test_rank_files_surfaces_http_errors_without_leaking_api_key(self):
        with TestHTTPServer() as server:
            server.enqueue_text('provider rejected key sk-test-secret', status=401)

            client = OpenAICompatibleClient(
                base_url=server.base_url,
                model="local-model",
                api_key="sk-test-secret",
            )

            with self.assertRaises(LLMRequestError) as raised:
                client.rank_files(
                    task="Find parser code.",
                    candidate_paths=["codekg/parser.py"],
                )

        message = str(raised.exception)
        self.assertIn("401", message)
        self.assertIn("provider rejected key", message)
        self.assertNotIn("Bearer sk-test-secret", message)
        self.assertNotIn("sk-test-secret", message)


if __name__ == "__main__":
    unittest.main()
