from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def repo_root_from_here() -> Path:
    cur = Path(__file__).resolve().parent
    for _ in range(10):
        if (cur / "manage.py").exists() or (cur / ".git").exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    raise RuntimeError("Raiz do projeto nao encontrada.")


ROOT = repo_root_from_here()
PYTHON_EXE = Path(sys.executable).resolve()
ORQUESTRADOR = Path(__file__).resolve().parent / "orquestrador_sermoes.py"
SELECTION_PATH = ROOT / "Apenas_Local" / "operacional" / "Jason-CSV" / "selecionados_atual.json"
BROWSE_HTML = ROOT / "Apenas_Local" / "scripts" / "homologacao" / "manifest_sermoes.html"
PORT = 8766
JOBS: dict[str, dict] = {}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Helper local do Browse")
    parser.add_argument("--port", type=int, default=8766)
    return parser.parse_args()


def _run_job(job_id: str, cmd: list[str]) -> None:
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        JOBS[job_id]["pid"] = proc.pid
        stdout, stderr = proc.communicate()
        JOBS[job_id].update(
            {
                "status": "completed" if proc.returncode == 0 else "failed",
                "returncode": proc.returncode,
                "stdout": (stdout or "")[-4000:],
                "stderr": (stderr or "")[-4000:],
            }
        )
    except Exception as exc:  # noqa: BLE001
        JOBS[job_id].update(
            {
                "status": "failed",
                "returncode": -1,
                "stdout": "",
                "stderr": str(exc),
            }
        )


def build_orquestrador_cmd(
    *,
    meta: dict,
    selection_path: Path | None = None,
    execute_payload: dict | None = None,
) -> list[str]:
    input_dir_sermoes = str(meta.get("input_dir_sermoes") or "").strip()
    input_dir_artigos = str(meta.get("input_dir_artigos") or "").strip()
    workspace_artigos = str(meta.get("workspace_artigos") or "").strip()
    if not input_dir_sermoes:
        raise ValueError("input_dir_sermoes ausente")

    cmd = [
        str(PYTHON_EXE),
        str(ORQUESTRADOR),
        "--input-dir",
        input_dir_sermoes,
    ]
    if input_dir_artigos:
        cmd.extend(["--input-dir-artigos", input_dir_artigos])
    if workspace_artigos:
        cmd.extend(["--workspace-artigos", workspace_artigos])

    if execute_payload is None:
        cmd.extend(["--browse", "--scan-only"])
        return cmd

    current_context = str(execute_payload.get("current_context") or "").strip()
    if current_context:
        cmd.extend(["--execute-context", current_context])
    if selection_path:
        cmd.extend(["--selection-file", str(selection_path)])
    cmd.append("--execute")
    return cmd


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, code: int, body: str) -> None:
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):  # noqa: N802
        self._send(200, {"ok": True})

    def do_GET(self):  # noqa: N802
        if self.path.rstrip("/") == "/health":
            self._send(200, {"ok": True, "service": "browse_refresh_helper"})
            return
        if self.path.rstrip("/") == "/browse":
            if not BROWSE_HTML.exists():
                self._send(404, {"ok": False, "error": "browse_not_generated"})
                return
            self._send_html(200, BROWSE_HTML.read_text(encoding="utf-8"))
            return
        if self.path.startswith("/job-status/"):
            job_id = self.path.rsplit("/", 1)[-1].strip()
            job = JOBS.get(job_id)
            if not job:
                self._send(404, {"ok": False, "error": "job_not_found"})
                return
            self._send(
                200,
                {
                    "ok": True,
                    "job_id": job_id,
                    "status": job.get("status"),
                    "stdout": job.get("stdout", ""),
                    "stderr": job.get("stderr", ""),
                    "returncode": job.get("returncode"),
                },
            )
            return
        self._send(404, {"ok": False, "error": "not_found"})

    def do_POST(self):  # noqa: N802
        route = self.path.rstrip("/")
        if route == "/save-selection":
            try:
                raw = self.rfile.read(int(self.headers.get("Content-Length", "0") or 0))
                payload = json.loads(raw.decode("utf-8") or "{}")
                save_path = Path(str(payload.get("save_path") or SELECTION_PATH))
                save_path.parent.mkdir(parents=True, exist_ok=True)
                save_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
                self._send(200, {"ok": True, "path": str(save_path)})
                return
            except Exception as exc:  # noqa: BLE001
                self._send(500, {"ok": False, "error": str(exc)})
                return

        if route == "/execute":
            try:
                raw = self.rfile.read(int(self.headers.get("Content-Length", "0") or 0))
                payload = json.loads(raw.decode("utf-8") or "{}")
                meta = payload.get("browse_meta") or {}
                save_path = Path(str(payload.get("save_path") or SELECTION_PATH))
                save_path.parent.mkdir(parents=True, exist_ok=True)
                save_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

                cmd = build_orquestrador_cmd(
                    meta=meta,
                    selection_path=save_path,
                    execute_payload=payload,
                )
                job_id = uuid.uuid4().hex
                JOBS[job_id] = {
                    "status": "running",
                    "stdout": "",
                    "stderr": "",
                    "returncode": None,
                    "path": str(save_path),
                }
                thread = threading.Thread(
                    target=_run_job,
                    args=(job_id, cmd),
                    daemon=True,
                )
                thread.start()
                self._send(200, {"ok": True, "job_id": job_id, "status": "running", "path": str(save_path)})
                return
            except Exception as exc:  # noqa: BLE001
                self._send(500, {"ok": False, "error": str(exc)})
                return

        if route != "/refresh":
            self._send(404, {"ok": False, "error": "not_found"})
            return

        try:
            raw = self.rfile.read(int(self.headers.get("Content-Length", "0") or 0))
            payload = json.loads(raw.decode("utf-8") or "{}")
            meta = payload.get("browse_meta") or {}
            cmd = build_orquestrador_cmd(meta=meta)

            proc = subprocess.run(
                cmd,
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if proc.returncode != 0:
                self._send(
                    500,
                    {
                        "ok": False,
                        "error": "refresh_failed",
                        "stdout": (proc.stdout or "")[-2000:],
                        "stderr": (proc.stderr or "")[-2000:],
                    },
                )
                return
            self._send(200, {"ok": True, "stdout": (proc.stdout or "")[-2000:]})
        except Exception as exc:  # noqa: BLE001
            self._send(500, {"ok": False, "error": str(exc)})

    def log_message(self, format, *args):  # noqa: A003
        return


def main() -> int:
    global PORT
    args = parse_args()
    PORT = int(args.port)
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"[OK] browse_refresh_helper em http://127.0.0.1:{PORT}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
