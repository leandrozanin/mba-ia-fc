# code-smells-project

API Flask de e-commerce com composi??o em `app.py`, configura??o em `config/`, rotas em `views/`, controllers, models e tratamento de erros em `middlewares/`.

## Configurar e executar

Requer Python 3.10+.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:SECRET_KEY = [guid]::NewGuid().ToString('N')
python app.py
```

A API inicia em `http://localhost:5000`. SQLite usa `loja.db`; `DATABASE_PATH` altera o caminho. `FLASK_DEBUG=true` habilita debug.

## Testes

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
```
