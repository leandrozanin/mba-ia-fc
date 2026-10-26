"""Smoke test HTTP dos projetos-alvo da skill refactor-arch.

Sobe a aplicação como subprocesso, exercita os endpoints originais em sequência
e grava método, rota, status e chaves do JSON retornado. O mesmo roteiro roda
antes (baseline) e depois da refatoração para comparar contratos.

Uso:
    python scripts/smoke_test.py <projeto> <saida.json>
    python scripts/smoke_test.py --compare <baseline.json> <depois.json>
"""
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "projects"


def venv_python(project_dir):
    candidate = project_dir / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    return str(candidate) if candidate.exists() else sys.executable


# Cada passo: (método, rota, corpo JSON ou None[, opções]).
# Opções: "headers" (valores aceitam {token}) e "capture" (guarda o campo "token" da resposta).
ADMIN = {"headers": {"X-Admin-Token": "smoke-admin-token"}}
BEARER = {"headers": {"Authorization": "Bearer {token}"}}
# Senha da conta admin do seed original; no projeto refatorado vem de SEED_USER_PASSWORD.
TASK_SEED_ADMIN = {"email": "joao@email.com", "password": "1234"}
CODE_SMELLS_STEPS = [
    ("GET", "/", None),
    ("GET", "/health", None),
    ("GET", "/produtos", None),
    ("GET", "/produtos/1", None),
    ("GET", "/produtos/999", None),
    ("GET", "/produtos/busca?q=Mouse&categoria=informatica&preco_min=10&preco_max=500", None),
    ("POST", "/produtos", {"nome": "Produto Smoke", "descricao": "teste", "preco": 10.5, "estoque": 5, "categoria": "geral"}),
    ("POST", "/produtos", {"nome": "X", "preco": 1, "estoque": 1}),
    ("PUT", "/produtos/1", {"nome": "Notebook Gamer", "descricao": "Atualizado", "preco": 5999.99, "estoque": 10, "categoria": "informatica"}),
    ("DELETE", "/produtos/11", None),
    ("GET", "/usuarios", None),
    ("GET", "/usuarios/1", None),
    ("POST", "/usuarios", {"nome": "Smoke", "email": "smoke@teste.com", "senha": "segredo-smoke"}),
    ("POST", "/login", {"email": "smoke@teste.com", "senha": "segredo-smoke"}),
    ("POST", "/login", {"email": "smoke@teste.com", "senha": "errada"}),
    ("POST", "/pedidos", {"usuario_id": 2, "itens": [{"produto_id": 2, "quantidade": 2}]}),
    ("POST", "/pedidos", {"usuario_id": 2, "itens": [{"produto_id": 2, "quantidade": 9999}]}),
    ("GET", "/pedidos", None),
    ("GET", "/pedidos/usuario/2", None),
    ("PUT", "/pedidos/1/status", {"status": "aprovado"}),
    ("PUT", "/pedidos/1/status", {"status": "invalido"}),
    ("GET", "/relatorios/vendas", None),
    ("POST", "/admin/query", {"sql": "SELECT 1"}),
    ("POST", "/admin/reset-db", None),
]

ECOMMERCE_STEPS = [
    ("POST", "/api/checkout", {"usr": "Smoke", "eml": "smoke@teste.com", "pwd": "segredo-smoke", "c_id": 1, "card": "4111111111111111"}),
    ("POST", "/api/checkout", {"usr": "Smoke2", "eml": "smoke2@teste.com", "c_id": 2, "card": "5111111111111111"}),
    ("POST", "/api/checkout", {"usr": "Recusado", "eml": "rec@teste.com", "c_id": 1, "card": "3111111111111111"}),
    ("POST", "/api/checkout", {"usr": "Curso", "eml": "c@teste.com", "c_id": 999, "card": "4111111111111111"}),
    ("POST", "/api/checkout", {"usr": "Faltando"}),
    ("GET", "/api/admin/financial-report", None, ADMIN),
    ("DELETE", "/api/users/1", None, ADMIN),
    ("GET", "/api/admin/financial-report", None, ADMIN),
    ("GET", "/api/admin/financial-report", None),
]

TASK_MANAGER_STEPS = [
    ("GET", "/", None),
    ("GET", "/health", None),
    ("GET", "/tasks", None),
    ("GET", "/tasks/1", None),
    ("GET", "/tasks/9999", None),
    ("GET", "/tasks/search?q=a", None),
    ("GET", "/tasks/stats", None),
    ("POST", "/tasks", {"title": "Task smoke", "description": "teste", "status": "pending", "priority": 2, "user_id": 1, "category_id": 1, "tags": ["smoke"]}),
    ("POST", "/tasks", {"title": "ab"}),
    ("PUT", "/tasks/1", {"status": "in_progress", "priority": 1}),
    ("PUT", "/tasks/1", {"status": "invalido"}),
    ("GET", "/users", None),
    ("GET", "/users/1", None),
    ("GET", "/users/9999", None),
    ("POST", "/users", {"name": "Smoke", "email": "smoke@teste.com", "password": "segredo-smoke"}),
    ("POST", "/users", {"name": "Smoke", "email": "invalido", "password": "segredo-smoke"}),
    ("GET", "/users/1/tasks", None),
    ("POST", "/login", {"email": "smoke@teste.com", "password": "segredo-smoke"}),
    ("POST", "/login", {"email": "smoke@teste.com", "password": "errada"}),
    ("PUT", "/users/2", {"role": "admin"}),
    ("POST", "/login", TASK_SEED_ADMIN, {"capture": "token"}),
    ("PUT", "/users/2", {"name": "Nome Atualizado"}, BEARER),
    ("GET", "/reports/summary", None),
    ("GET", "/reports/user/1", None),
    ("GET", "/categories", None),
    ("POST", "/categories", {"name": "Smoke", "description": "teste", "color": "#123456"}, BEARER),
    ("PUT", "/categories/1", {"name": "Trabalho"}, BEARER),
    ("DELETE", "/tasks/2", None),
    ("DELETE", "/categories/4", None, BEARER),
    ("DELETE", "/users/3", None, BEARER),
]


def project_config(name):
    project_dir = PROJECTS / name
    py = venv_python(project_dir)
    if name == "code-smells-project":
        return {
            "dir": project_dir,
            "port": 5000,
            "setup": [],
            "cmd": [py, "app.py"],
            "env": {"SECRET_KEY": "smoke-test-only", "DATABASE_PATH": "smoke.db"},
            "cleanup": ["loja.db", "smoke.db"],
            "steps": CODE_SMELLS_STEPS,
        }
    if name == "ecommerce-api-legacy":
        return {
            "dir": project_dir,
            "port": 3000,
            "setup": [],
            "cmd": ["node", "src/app.js"],
            "env": {"PAYMENT_GATEWAY_KEY": "smoke-test-only", "ADMIN_API_TOKEN": ADMIN["headers"]["X-Admin-Token"]},
            "cleanup": [],
            "steps": ECOMMERCE_STEPS,
        }
    if name == "task-manager-api":
        return {
            "dir": project_dir,
            "port": 5000,
            "setup": [[py, "seed.py"]],
            "cmd": [py, "app.py"],
            "env": {"SECRET_KEY": "smoke-test-only", "DATABASE_URL": "sqlite:///smoke.db", "SEED_USER_PASSWORD": TASK_SEED_ADMIN["password"]},
            "cleanup": ["instance", "tasks.db", "smoke.db"],
            "steps": TASK_MANAGER_STEPS,
        }
    raise SystemExit(f"Projeto desconhecido: {name}")


def cleanup(project_dir, entries):
    for entry in entries:
        path = project_dir / entry
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        elif path.exists():
            path.unlink()


def stop(server):
    # O reloader do Flask em debug cria um processo filho; encerra a árvore inteira.
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(server.pid)], capture_output=True)
    else:
        server.terminate()
    server.wait(timeout=10)
    time.sleep(0.5)


def wait_port(port, timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                return True
        time.sleep(0.3)
    return False


def call(port, method, path, body, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    for name, value in (headers or {}).items():
        req.add_header(name, value)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status, raw = resp.status, resp.read()
    except urllib.error.HTTPError as err:
        status, raw = err.code, err.read()
    try:
        payload = json.loads(raw)
        keys = sorted(payload.keys()) if isinstance(payload, dict) else type(payload).__name__
    except ValueError:
        payload, keys = raw.decode(errors="replace")[:120], "text"
    return status, keys, payload


def run(name, output):
    cfg = project_config(name)
    project_dir = cfg["dir"]
    cleanup(project_dir, cfg["cleanup"])
    env = {**os.environ, **cfg["env"], "PYTHONIOENCODING": "utf-8"}
    for command in cfg["setup"]:
        subprocess.run(command, cwd=project_dir, env=env, check=True, capture_output=True)

    log_path = Path(output).with_suffix(".server.log")
    with open(log_path, "w", encoding="utf-8") as log:
        server = subprocess.Popen(cfg["cmd"], cwd=project_dir, env=env, stdout=log, stderr=subprocess.STDOUT)
        try:
            booted = wait_port(cfg["port"])
            results = []
            context = {"token": ""}
            if booted:
                for method, path, body, *extra in cfg["steps"]:
                    options = extra[0] if extra else {}
                    headers = {k: v.format(**context) for k, v in options.get("headers", {}).items()}
                    status, keys, payload = call(cfg["port"], method, path, body, headers)
                    if options.get("capture") and isinstance(payload, dict) and payload.get("token"):
                        context["token"] = payload["token"]
                    results.append({"method": method, "path": path, "status": status, "keys": keys, "body": payload})
                    print(f"{status}  {method:6} {path}")
        finally:
            stop(server)
    cleanup(project_dir, cfg["cleanup"])

    report = {"project": name, "booted": booted, "results": results}
    Path(output).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"boot={'ok' if booted else 'FALHOU'}  requests={len(results)}  saida={output}")
    return 0 if booted else 1


def compare(baseline_path, after_path):
    baseline = json.loads(Path(baseline_path).read_text(encoding="utf-8"))
    after = json.loads(Path(after_path).read_text(encoding="utf-8"))
    print(f"| Método | Rota | Antes | Depois | Chaves JSON iguais |")
    print(f"|---|---|---:|---:|---|")
    for before, now in zip(baseline["results"], after["results"]):
        same_keys = "sim" if before["keys"] == now["keys"] else f"{before['keys']} → {now['keys']}"
        print(f"| {now['method']} | `{now['path']}` | {before['status']} | {now['status']} | {same_keys} |")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) == 4 and sys.argv[1] == "--compare":
        sys.exit(compare(sys.argv[2], sys.argv[3]))
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sys.exit(run(sys.argv[1], sys.argv[2]))
