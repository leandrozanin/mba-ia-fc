# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Após a refatoração, segue MVC: `routes/` (HTTP), `controllers/` (casos de uso e validação), `models/` (dados e regras do modelo), `services/` (token e e-mail) e `config.py` (configuração por ambiente).

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env        # preencha SECRET_KEY (obrigatória)
python seed.py
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000` (debug desligado por padrão; veja `FLASK_DEBUG`, `HOST` e `PORT` no `.env.example`). O `seed.py` **apaga e recria** os dados do banco SQLite (`instance/tasks.db` por padrão) com usuários, categorias e tasks de exemplo.

## Autenticação

`POST /login` devolve um `token` assinado (validade em `TOKEN_MAX_AGE`). Envie-o como `Authorization: Bearer <token>` em:

- `POST/PUT/DELETE /tasks...` e `POST/PUT/DELETE /categories...` — qualquer usuário autenticado;
- `PUT /users/<id>` — o próprio usuário ou um admin; mudar `role`/`active` exige admin;
- `DELETE /users/<id>` — só admin;
- `POST /users` — aberto para cadastro com `role` `user`; outros papéis exigem token de admin.

As rotas `GET` continuam públicas.

## Testes

```bash
python -m unittest discover -s tests -t .
```

Os testes usam um SQLite temporário e não tocam no `instance/tasks.db`.
