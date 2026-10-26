process.env.LOG_LEVEL = 'silent';

const { test, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert/strict');
const { createApp } = require('../src/app');

const ADMIN = { 'x-admin-token': 'test-admin-token' };
let server;
let db;
let baseUrl;

beforeEach(async () => {
    const created = await createApp({
        config: {
            port: 0,
            databaseFile: ':memory:',
            paymentGatewayKey: 'test',
            adminApiToken: ADMIN['x-admin-token'],
            seedUserPassword: 'senha-demo',
        },
    });
    db = created.db;
    server = created.app.listen(0);
    await new Promise((resolve) => server.once('listening', resolve));
    baseUrl = `http://127.0.0.1:${server.address().port}`;
});

afterEach(async () => {
    await new Promise((resolve) => server.close(resolve));
    await db.close();
});

async function request(method, path, body, headers = {}) {
    const res = await fetch(baseUrl + path, {
        method,
        headers: { 'content-type': 'application/json', ...headers },
        body: body === undefined ? undefined : JSON.stringify(body),
    });
    const text = await res.text();
    let data = text;
    try { data = JSON.parse(text); } catch { /* resposta em texto */ }
    return { status: res.status, data };
}

const checkout = (overrides = {}) => request('POST', '/api/checkout', {
    usr: 'Ana', eml: 'ana@teste.com', pwd: 'senha-ana', c_id: 2, card: '4111111111111111', ...overrides,
});

const count = async (table) => (await db.get(`SELECT COUNT(*) AS total FROM ${table}`)).total;

test('checkout aprovado cria matrícula, pagamento e auditoria', async () => {
    const res = await checkout();
    assert.equal(res.status, 200);
    assert.equal(res.data.msg, 'Sucesso');
    assert.equal(await count('payments'), 2);
    assert.equal(await count('audit_logs'), 1);
});

test('senha é armazenada com hash scrypt', async () => {
    await checkout();
    const user = await db.get("SELECT pass FROM users WHERE email = 'ana@teste.com'");
    assert.match(user.pass, /^scrypt\$/);
});

test('pagamento recusado não deixa usuário nem matrícula', async () => {
    const res = await checkout({ card: '5111111111111111' });
    assert.equal(res.status, 400);
    assert.equal(res.data, 'Pagamento recusado');
    assert.equal(await count('users'), 1);
    assert.equal(await count('enrollments'), 1);
});

test('payload malformado retorna 400 em vez de derrubar o processo', async () => {
    assert.equal((await checkout({ card: 4111111111111111 })).status, 400);
    assert.equal((await checkout({ c_id: 'abc' })).status, 400);
    assert.equal((await checkout({ eml: 'sem-arroba' })).status, 400);
    assert.equal((await request('POST', '/api/checkout', { usr: 'x' })).status, 400);
    assert.equal((await checkout()).status, 200);
});

test('novo usuário sem senha é recusado', async () => {
    assert.equal((await checkout({ pwd: undefined })).status, 400);
});

test('usuário existente precisa da senha correta e não compra duas vezes', async () => {
    assert.equal((await checkout()).status, 200);
    assert.equal((await checkout({ pwd: 'errada', c_id: 1 })).status, 401);
    assert.equal((await checkout()).status, 409);
    assert.equal((await checkout({ c_id: 1 })).status, 200);
});

test('falha no meio do checkout faz rollback', async () => {
    await db.run('DROP TABLE audit_logs');
    assert.equal((await checkout()).status, 500);
    assert.equal(await count('users'), 1);
    assert.equal(await count('enrollments'), 1);
});

test('rotas admin exigem token', async () => {
    assert.equal((await request('GET', '/api/admin/financial-report')).status, 401);
    assert.equal((await request('DELETE', '/api/users/1', undefined, { 'x-admin-token': 'errado' })).status, 401);
});

test('relatório financeiro agrega receita por curso sem N+1', async () => {
    await checkout({ c_id: 1 });
    const res = await request('GET', '/api/admin/financial-report', undefined, ADMIN);
    assert.equal(res.status, 200);
    assert.deepEqual(res.data, [
        { course: 'Clean Architecture', revenue: 1994, students: [{ student: 'Leonan', paid: 997 }, { student: 'Ana', paid: 997 }] },
        { course: 'Docker', revenue: 0, students: [] },
    ]);
});

test('excluir usuário anonimiza dados e preserva histórico', async () => {
    const res = await request('DELETE', '/api/users/1', undefined, ADMIN);
    assert.equal(res.status, 200);
    const user = await db.get('SELECT name, email, pass FROM users WHERE id = 1');
    assert.deepEqual({ ...user }, { name: null, email: null, pass: null });
    assert.equal(await count('payments'), 1);
    assert.equal((await request('DELETE', '/api/users/1', undefined, ADMIN)).status, 404);

    const report = await request('GET', '/api/admin/financial-report', undefined, ADMIN);
    assert.equal(report.data[0].students[0].student, 'Unknown');
});
