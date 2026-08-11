"""The two seams that really touch the operating system, exercised for real.

Everything else in this group runs against fakes, which is right: a test should
not need a tunnel to check a policy. But `fetch` and `spawn` are the exact points
where the project stops reasoning and starts calling the OS, and a fake there
would prove nothing at all. Both are driven against a throwaway local server and
a throwaway child process - no network beyond loopback, no provider, no
credential.
"""

import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from peer_process import free_port

from mars777_police.infra.ngrok_ingress import fetch
from mars777_police.infra.ngrok_process import spawn

BODY = b'{"tunnels": [], "uri": "/api/tunnels"}'


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(BODY)))
        self.end_headers()
        self.wfile.write(BODY)

    def log_message(self, *args: object) -> None:
        return


@pytest.fixture
def loopback_server() -> object:
    port = free_port()
    server = HTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        server.server_close()


def test_the_real_fetcher_reads_a_loopback_agent_api_body(loopback_server: str) -> None:
    """The stdlib path that a fake fetcher can never exercise."""
    assert fetch(f"{loopback_server}/api/tunnels") == BODY


def test_the_real_fetcher_raises_an_os_error_for_a_dead_address() -> None:
    """A closed port is an `OSError`, which is what the poll loop tolerates."""
    with pytest.raises(OSError):
        fetch(f"http://127.0.0.1:{free_port()}/api/tunnels")


def test_the_real_spawner_starts_a_child_and_pipes_its_output() -> None:
    """A throwaway child, terminated immediately; no provider is involved."""
    child = spawn((sys.executable, "-c", "print('mars777-spawn-probe')"))
    try:
        assert child.stdout is not None
        assert child.stdout.readline().strip() == "mars777-spawn-probe"
    finally:
        child.terminate()
        child.wait(timeout=10)
    assert child.returncode is not None


def test_the_real_spawner_merges_stderr_into_the_single_stream() -> None:
    """One stream keeps a provider diagnostic in the same place as its log lines."""
    child = spawn((sys.executable, "-c", "import sys; sys.stderr.write('to-stderr\\n')"))
    try:
        assert child.stdout is not None
        assert child.stdout.readline().strip() == "to-stderr"
        assert child.stderr is None
    finally:
        child.terminate()
        child.wait(timeout=10)
    assert isinstance(child, subprocess.Popen)
