# ecommerce-api-legacy

API Express de checkout com f?brica de aplica??o, configura??o ambiental, hash de senha com scrypt e logs sem o n?mero integral do cart?o.

## Configurar e executar

Requer Node.js 22 LTS e npm.

```bash
npm ci
npm start
```

A API escuta em `http://localhost:3000`. `PORT`, `PAYMENT_GATEWAY_KEY` e `SMTP_USER` s?o lidos do ambiente.

## Testes

```bash
npm test
npm audit
```

A corre??o compat?vel reduziu as vulnerabilidades de 14 para 8. As restantes v?m da cadeia de build do `sqlite3`; o npm indica que a corre??o completa requer `sqlite3` 6 (major), portanto a migra??o do driver precisa ser avaliada.
