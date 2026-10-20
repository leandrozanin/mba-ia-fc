const { test } = require('node:test');
const assert = require('node:assert/strict');
const { createApp } = require('../src/app');
const { hashPassword } = require('../src/utils');

test('password hashes are salted and not reversible plaintext', () => {
  const first = hashPassword('123456');
  const second = hashPassword('123456');
  assert.notEqual(first, second);
  assert.ok(first.includes(':'));
  assert.ok(!first.includes('123456'));
});

test('API boots and preserves report and checkout contracts without logging full card', async (t) => {
  const originalLog = console.log;
  const logs = [];
  console.log = (...args) => logs.push(args.join(' '));
  const app = createApp();
  const server = app.listen(0);
  t.after(() => { console.log = originalLog; server.close(); });
  const base = `http://127.0.0.1:${server.address().port}`;
  const report = await fetch(`${base}/api/admin/financial-report`);
  assert.equal(report.status, 200);
  assert.ok(Array.isArray(await report.json()));
  const checkout = await fetch(`${base}/api/checkout`, { method: 'POST', headers: {'content-type':'application/json'}, body: JSON.stringify({usr:'Teste',eml:'teste@example.com',pwd:'abc',c_id:1,card:'4111111111111111'}) });
  assert.equal(checkout.status, 200);
  assert.ok((await checkout.json()).enrollment_id);
  assert.ok(logs.every(line => !line.includes('4111111111111111')));
  assert.ok(logs.every(line => !line.includes('pk_live_')));
});
