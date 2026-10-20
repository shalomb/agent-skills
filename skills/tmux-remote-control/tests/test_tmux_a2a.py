"""Tests for scripts/tmux-a2a.py. Run: python3 -m unittest -v tests/test_tmux_a2a.py  (from the skill dir)"""
import importlib.machinery
import importlib.util
import json
import os
import stat
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "tmux-a2a.py"
_loader = importlib.machinery.SourceFileLoader("tmux_a2a", str(SCRIPT))
_spec = importlib.util.spec_from_loader("tmux_a2a", _loader)
m = importlib.util.module_from_spec(_spec)
_loader.exec_module(m)

TOKEN = "t0k3n-abcdefghijklmnopqrstuvwx"


def write_info(d, name, **over):
    info = {"sessionId": name, "pid": os.getpid(), "url": "http://127.0.0.1:1", "token": TOKEN,
            "cwd": "/w", "tmuxPane": "%9", "startedAt": "2026-10-20T05:00:00.000Z"}
    info.update(over)
    p = Path(d) / f"{name}.a2a.json"
    p.write_text(json.dumps(info))
    os.chmod(p, 0o600)
    return p


class ProcTests(unittest.TestCase):
    def test_parent_parsed_after_last_paren_even_with_spaces_and_parens_in_comm(self):
        with tempfile.TemporaryDirectory() as root:
            (Path(root) / "42").mkdir()
            (Path(root) / "42" / "stat").write_text("42 (we ird) name) S 7 42 42 0 -1 4194560")
            self.assertEqual(m.proc_parent(42, root), 7)

    def test_parent_none_when_process_missing_or_garbage(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertIsNone(m.proc_parent(99, root))
            (Path(root) / "5").mkdir()
            (Path(root) / "5" / "stat").write_text("garbage")
            self.assertIsNone(m.proc_parent(5, root))

    def test_descendant_walks_the_ancestor_chain_and_stops_at_init(self):
        parents = {30: 20, 20: 10, 10: 1, 1: 0}
        po = parents.get
        self.assertTrue(m.is_descendant(30, 10, po))
        self.assertTrue(m.is_descendant(10, 10, po))
        self.assertFalse(m.is_descendant(30, 99, po))
        self.assertFalse(m.is_descendant(30, 10, lambda p: None))

    def test_descendant_survives_a_parent_cycle(self):
        self.assertFalse(m.is_descendant(1, 99, {1: 2, 2: 1}.get))


class LoopbackTests(unittest.TestCase):
    def test_only_http_loopback_urls(self):
        for ok in ("http://127.0.0.1:8080", "http://127.5.5.5:1", "http://[::1]:9", "http://localhost:3"):
            self.assertTrue(m.is_loopback_url(ok), ok)
        for bad in ("http://10.0.0.5:80", "https://127.0.0.1:1", "http://evil.example.com:80", "ftp://127.0.0.1", "", "junk",
                    "http://127.0.0.1.evil.com:80", "http://user@evil.com:80"):
            self.assertFalse(m.is_loopback_url(bad), bad)


class HandshakeTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.d = self.td.name
        os.chmod(self.d, 0o700)

    def tearDown(self):
        self.td.cleanup()

    def test_loads_valid_files_and_skips_bad_ones(self):
        write_info(self.d, "good")
        (Path(self.d) / "broken.a2a.json").write_text("{nope")
        write_info(self.d, "remote", url="http://10.1.1.1:80")
        write_info(self.d, "nopid", pid="x")
        (Path(self.d) / "ignored.txt").write_text("{}")
        self.assertEqual([h["sessionId"] for h in m.load_handshakes(self.d)], ["good"])

    def test_refuses_group_or_world_readable_files(self):
        p = write_info(self.d, "loose")
        os.chmod(p, 0o644)
        self.assertEqual(m.load_handshakes(self.d), [])

    def test_refuses_a_loose_directory(self):
        write_info(self.d, "g")
        os.chmod(self.d, 0o755)
        self.assertEqual(m.load_handshakes(self.d), [])

    def test_refuses_symlinks_and_oversized_files(self):
        real = write_info(self.d, "real")
        os.symlink(real, Path(self.d) / "link.a2a.json")
        big = Path(self.d) / "big.a2a.json"
        big.write_text(" " * 70000)
        os.chmod(big, 0o600)
        self.assertEqual([h["sessionId"] for h in m.load_handshakes(self.d)], ["real"])

    def test_missing_directory_is_empty(self):
        self.assertEqual(m.load_handshakes(os.path.join(self.d, "nope")), [])

    def test_find_endpoint_matches_by_ancestry_and_ignores_the_dead(self):
        write_info(self.d, "mine", pid=300)
        write_info(self.d, "other", pid=400)
        write_info(self.d, "dead", pid=500)
        parents = {300: 100, 400: 200, 500: 100}
        alive = lambda pid: pid != 500
        h = m.find_endpoint(self.d, pane_pid=100, parent_of=parents.get, alive=alive)
        self.assertEqual(h["sessionId"], "mine")

    def test_find_endpoint_none_when_nothing_descends_from_the_pane(self):
        write_info(self.d, "other", pid=400)
        self.assertIsNone(m.find_endpoint(self.d, 100, {400: 200}.get, lambda p: True))

    def test_find_endpoint_prefers_the_newest_when_nested(self):
        write_info(self.d, "old", pid=300, startedAt="2026-10-20T05:00:00.000Z")
        write_info(self.d, "new", pid=301, startedAt="2026-10-20T06:00:00.000Z")
        h = m.find_endpoint(self.d, 100, {300: 100, 301: 100}.get, lambda p: True)
        self.assertEqual(h["sessionId"], "new")


class Stub(BaseHTTPRequestHandler):
    script = []          # list of states returned by successive tasks/get
    reply = "the reply"
    question = "Which one?"
    sent = []
    seen_auth = []

    def log_message(self, *a):
        pass

    def do_POST(self):
        Stub.seen_auth.append(self.headers.get("Authorization"))
        if self.headers.get("Authorization") != f"Bearer {TOKEN}":
            self.send_response(401); self.end_headers(); return
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        method, params = body["method"], body.get("params", {})
        if method == "message/send":
            Stub.sent.append(params["message"]["parts"][0]["text"])
            result = {"kind": "task", "id": "T1", "contextId": "T1", "status": {"state": "submitted"}}
        else:
            state = Stub.script.pop(0) if Stub.script else "completed"
            result = {"kind": "task", "id": "T1", "contextId": "T1", "status": {"state": state}}
            if state == "completed":
                result["artifacts"] = [{"artifactId": "a", "parts": [{"kind": "text", "text": Stub.reply}]}]
            if state == "input-required":
                result["status"]["message"] = {"parts": [{"kind": "text", "text": Stub.question}]}
            if state == "failed":
                result["status"]["message"] = {"parts": [{"kind": "text", "text": "it broke"}]}
        out = json.dumps({"jsonrpc": "2.0", "id": body["id"], "result": result}).encode()
        self.send_response(200); self.send_header("Content-Length", str(len(out))); self.end_headers(); self.wfile.write(out)


class ClientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = HTTPServer(("127.0.0.1", 0), Stub)
        cls.url = f"http://127.0.0.1:{cls.srv.server_port}"
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def setUp(self):
        Stub.script, Stub.sent, Stub.seen_auth = [], [], []
        Stub.reply = "the reply"

    def wait(self, script, deadline=5.0, token=TOKEN):
        Stub.script = list(script)
        c = m.A2AClient(self.url, token)
        return m.send_and_wait(c, "do it", deadline=deadline, poll=0.01)

    def test_completed_returns_the_reply_and_sent_the_text(self):
        r = self.wait(["working", "working", "completed"])
        self.assertEqual((r.state, r.text, r.exit_code), ("completed", "the reply", 0))
        self.assertEqual(Stub.sent, ["do it"])

    def test_failed_maps_to_exit_2_with_the_message(self):
        r = self.wait(["working", "failed"])
        self.assertEqual((r.state, r.exit_code), ("failed", 2))
        self.assertIn("it broke", r.text)

    def test_canceled_maps_to_exit_2(self):
        self.assertEqual(self.wait(["canceled"]).exit_code, 2)

    def test_input_required_stops_waiting_and_carries_the_question(self):
        r = self.wait(["working", "input-required"])
        self.assertEqual((r.state, r.exit_code, r.text), ("input-required", 4, "Which one?"))

    def test_timeout_maps_to_exit_5_and_names_the_task(self):
        Stub.script = ["working"] * 1000
        c = m.A2AClient(self.url, TOKEN)
        r = m.send_and_wait(c, "x", deadline=0.15, poll=0.02)
        self.assertEqual((r.state, r.exit_code), ("working", 5))
        self.assertEqual(r.task_id, "T1")

    def test_bad_token_maps_to_exit_6_without_leaking_it(self):
        r = self.wait(["completed"], token="wrong-token-value")
        self.assertEqual(r.exit_code, 6)
        self.assertNotIn("wrong-token-value", r.text)

    def test_unreachable_endpoint_maps_to_exit_6(self):
        c = m.A2AClient("http://127.0.0.1:1", TOKEN)
        r = m.send_and_wait(c, "x", deadline=1, poll=0.01)
        self.assertEqual(r.exit_code, 6)

    def test_bearer_header_is_sent_on_every_call(self):
        self.wait(["working", "completed"])
        self.assertTrue(Stub.seen_auth and all(a == f"Bearer {TOKEN}" for a in Stub.seen_auth))


class CliTests(unittest.TestCase):
    def test_resolve_exit_3_when_no_endpoint(self):
        with tempfile.TemporaryDirectory() as d:
            os.chmod(d, 0o700)
            self.assertEqual(m.cli_send(d, pane_pid=100, text="x", deadline=1, parent_of=lambda p: None, alive=lambda p: True), (3, "", "no a2a endpoint for this pane"))

    def test_cli_output_never_contains_the_token(self):
        Stub.script, Stub.sent, Stub.seen_auth = ["completed"], [], []
        srv = HTTPServer(("127.0.0.1", 0), Stub)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            with tempfile.TemporaryDirectory() as d:
                os.chmod(d, 0o700)
                write_info(d, "s", pid=300, url=f"http://127.0.0.1:{srv.server_port}")
                code, out, err = m.cli_send(d, pane_pid=100, text="x", deadline=5, parent_of={300: 100}.get, alive=lambda p: True)
            self.assertEqual(code, 0)
            self.assertNotIn(TOKEN, out + err)
            self.assertEqual(out, "the reply")
        finally:
            srv.shutdown()
            srv.server_close()


if __name__ == "__main__":
    unittest.main()
