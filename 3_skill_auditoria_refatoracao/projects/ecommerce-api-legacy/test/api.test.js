const { test, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert/strict');
const { createApp, createDatabase } = require('../src/app');
const { loadConfig } = require('../src/config');
const { verifyPassword } = require('../src/services/passwordHasher');

const ADMIN_TOKEN = 'test-admin-token';
const auth = { authorization: `Bearer ${ADMIN_TOKEN}` };
const validCheckout = { usr: 'Guilherme', eml: 'gui@fullcycle.com.br', pwd: 'senhaforte', c_id: 2, card: '4111222233334444' };

let db;
let server;
let baseUrl;

beforeEach(async () => {
    db = await createDatabase(':memory:');
    const app = createApp({ db, config: loadConfig({ ADMIN_TOKEN }) });
    server = app.listen(0);
    await new Promise((resolve) => server.once('listening', resolve));
    baseUrl = `http://127.0.0.1:${server.address().port}`;
});

afterEach(async () => {
    await new Promise((resolve) => server.close(resolve));
    await db.close();
});

async function request(method, path, { body, headers = {}, raw } = {}) {
    const res = await fetch(baseUrl + path, {
        method,
        headers: { 'content-type': 'application/json', ...headers },
        body: raw ?? (body && JSON.stringify(body)),
    });
    const text = await res.text();
    const isJson = (res.headers.get('content-type') || '').includes('application/json');
    return { status: res.status, body: isJson ? JSON.parse(text) : text };
}

const count = async (table) => (await db.get(`SELECT COUNT(*) AS n FROM ${table}`)).n;

test('config exige ADMIN_TOKEN', () => {
    assert.throws(() => loadConfig({}), /ADMIN_TOKEN/);
    assert.equal(loadConfig({ ADMIN_TOKEN: 'x' }).port, 3000);
});

test('checkout com sucesso mantém o contrato e persiste tudo', async () => {
    const res = await request('POST', '/api/checkout', { body: validCheckout });
    assert.equal(res.status, 200);
    assert.deepEqual(res.body, { msg: 'Sucesso', enrollment_id: 2 });
    assert.equal(await count('payments'), 2);
    assert.equal(await count('audit_logs'), 1);

    const user = await db.get("SELECT pass FROM users WHERE email = ?", [validCheckout.eml]);
    assert.match(user.pass, /^scrypt\$/);
    assert.equal(await verifyPassword('senhaforte', user.pass), true);
    assert.equal(await verifyPassword('senhafraca', user.pass), false);
});

test('checkout de usuário existente reutiliza o usuário sem exigir senha', async () => {
    const res = await request('POST', '/api/checkout', {
        body: { usr: 'Leonan', eml: 'leonan@fullcycle.com.br', c_id: 2, card: '4111222233334444' },
    });
    assert.equal(res.status, 200);
    assert.equal(await count('users'), 1);
});

test('pagamento recusado não cria usuário nem matrícula', async () => {
    const res = await request('POST', '/api/checkout', { body: { ...validCheckout, card: '5111222233334444' } });
    assert.deepEqual(res, { status: 400, body: 'Pagamento recusado' });
    assert.equal(await count('users'), 1);
    assert.equal(await count('enrollments'), 1);
});

test('curso inexistente retorna 404', async () => {
    const res = await request('POST', '/api/checkout', { body: { ...validCheckout, c_id: 99 } });
    assert.deepEqual(res, { status: 404, body: 'Curso não encontrado' });
});

test('entrada inválida retorna 400 sem derrubar o servidor', async () => {
    const invalid = [
        { usr: 'X', eml: 'x@x.com' },
        { ...validCheckout, card: 4111222233334444 },
        { ...validCheckout, card: '4111' },
        { ...validCheckout, eml: 'sem-arroba' },
        { ...validCheckout, c_id: 'abc' },
        { ...validCheckout, pwd: undefined, eml: 'novo@teste.com' },
    ];
    for (const body of invalid) {
        assert.deepEqual(await request('POST', '/api/checkout', { body }), { status: 400, body: 'Bad Request' });
    }
    assert.deepEqual(await request('POST', '/api/checkout', { raw: '{nope' }), { status: 400, body: 'Bad Request' });
    assert.equal((await request('POST', '/api/checkout', { body: validCheckout })).status, 200);
});

test('falha intermediária faz rollback do checkout', async () => {
    await db.exec('DROP TABLE audit_logs');
    const res = await request('POST', '/api/checkout', { body: validCheckout });
    assert.equal(res.status, 500);
    assert.equal(await count('users'), 1);
    assert.equal(await count('enrollments'), 1);
    assert.equal(await count('payments'), 1);
});

test('rotas administrativas exigem o token de admin', async () => {
    for (const headers of [{}, { authorization: 'Bearer errado' }, { authorization: ADMIN_TOKEN }]) {
        assert.deepEqual(await request('GET', '/api/admin/financial-report', { headers }), { status: 401, body: 'Unauthorized' });
        assert.deepEqual(await request('DELETE', '/api/users/1', { headers }), { status: 401, body: 'Unauthorized' });
    }
    assert.equal(await count('users'), 1);
});

test('relatório financeiro mantém o formato e agrega com pagamento', async () => {
    await request('POST', '/api/checkout', { body: validCheckout });
    const res = await request('GET', '/api/admin/financial-report', { headers: auth });
    assert.equal(res.status, 200);
    assert.deepEqual(res.body, [
        { course: 'Clean Architecture', revenue: 997, students: [{ student: 'Leonan', paid: 997 }] },
        { course: 'Docker', revenue: 497, students: [{ student: 'Guilherme', paid: 497 }] },
    ]);
});

test('exclusão de usuário remove matrículas e pagamentos', async () => {
    const res = await request('DELETE', '/api/users/1', { headers: auth });
    assert.equal(res.status, 200);
    assert.equal(await count('enrollments'), 0);
    assert.equal(await count('payments'), 0);

    const report = await request('GET', '/api/admin/financial-report', { headers: auth });
    assert.deepEqual(report.body[0], { course: 'Clean Architecture', revenue: 0, students: [] });
});

test('exclusão de usuário inexistente ou id inválido', async () => {
    assert.deepEqual(await request('DELETE', '/api/users/999', { headers: auth }), { status: 404, body: 'Usuário não encontrado' });
    assert.deepEqual(await request('DELETE', '/api/users/abc', { headers: auth }), { status: 400, body: 'Bad Request' });
});

test('checkouts concorrentes não colidem nas transações', async () => {
    const results = await Promise.all([1, 2, 3, 4, 5].map((i) =>
        request('POST', '/api/checkout', { body: { ...validCheckout, eml: `user${i}@teste.com` } })));
    assert.ok(results.every((r) => r.status === 200));
    assert.equal(await count('payments'), 6);
    assert.equal(await count('audit_logs'), 5);
});
