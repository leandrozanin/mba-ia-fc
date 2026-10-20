# task-manager-api

API Flask com f?brica `create_app`, configura??o ambiental, blueprints e camadas de models, routes, services e utils.

## Configurar e executar

Requer Python 3.10+.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python seed.py
python app.py
```

A API inicia em `http://localhost:5000`. Configure `DATABASE_URL`, `SECRET_KEY`, `FLASK_DEBUG`, `PORT` e, para notifica??es, `SMTP_USER`/`SMTP_PASSWORD` no ambiente.

## Testes

```bash
python -m unittest discover -s tests -v
```
