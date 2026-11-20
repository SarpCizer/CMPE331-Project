import test from 'node:test';
import assert from 'node:assert/strict';
import { randomUUID } from 'node:crypto';

// Real HTTP tests for the approved contract; there is no substitute application.
// Run against an isolated development database, never a shared live database.
const base = process.env.API_BASE_URL;
if (!base) throw new Error('Set API_BASE_URL to the isolated test API. Tests were not executed.');
const origin = new URL(base);
if (!['http:', 'https:'].includes(origin.protocol)) throw new Error('Expected an HTTP(S) API URL');
if (!['localhost', '127.0.0.1', '[::1]'].includes(origin.hostname) && process.env.ALLOW_REMOTE_TESTS !== '1') {
  throw new Error('Remote test databases require ALLOW_REMOTE_TESTS=1');
}
const password = `Test-${randomUUID()}!`;
const email = () => `fridgely-${randomUUID()}@example.test`;
async function request(method, path, body, token) {
  const res = await fetch(`${base.replace(/\/$/, '')}${path}`, {
    method, redirect: 'error', signal: AbortSignal.timeout(10000),
    headers: { ...(body === undefined ? {} : {'Content-Type':'application/json'}),
      ...(token ? {Authorization:`Bearer ${token}`} : {}) },
    ...(body === undefined ? {} : {body:JSON.stringify(body)}),
  });
  const text = await res.text();
  return {status:res.status, body:text ? JSON.parse(text) : undefined};
}
async function expect(method, path, body, token, status = 200) {
  const result = await request(method, path, body, token);
  // Do not include credentials, JWTs or raw provider diagnostics in failures.
  assert.equal(result.status, status, `${method} ${path}`);
  return result.body;
}
async function account() {
  const address = email();
  const user = await expect('POST', '/accounts', {email:address,password}, undefined, 201);
  const login = await expect('POST', '/sessions', {email:address,password});
  assert.equal(typeof login.token, 'string');
  return {user, address, token:login.token};
}

test('B-AUTH-01 registration returns public account fields and enables sign-in', async () => {
  const {user, address} = await account();
  assert.ok(user.id);
  assert.equal(user.email, address);
  assert.deepEqual(Object.keys(user).sort(), ['email','id']);
});

test('B-AUTH-02 normalized duplicate email is rejected', async () => {
  const {address} = await account();
  await expect('POST','/accounts',{email:address.toUpperCase(),password},undefined,409);
});

test('B-AUTH-03 invalid registration does not reserve the email', async () => {
  const address = email();
  await expect('POST','/accounts',{email:'invalid-email',password},undefined,400);
  await expect('POST','/accounts',{email:address,password:'short'},undefined,400);
  await expect('POST','/accounts',{email:address,password},undefined,201);
});

test('B-AUTH-04 wrong and unknown credentials return no token', async () => {
  const {address} = await account();
  for (const credentials of [{email:address,password:'wrong-password'}, {email:email(),password}]) {
    const denied = await expect('POST','/sessions',credentials,undefined,401);
    assert.equal(denied.token, undefined);
    assert.equal(denied.password, undefined);
    assert.equal(denied.passwordHash, undefined);
  }
});

test('B-AUTH-05 issued JWT has finite expiry and a signature', async () => {
  const {token} = await account();
  const parts = token.split('.');
  assert.equal(parts.length,3);
  assert.ok(parts[2].length);
  const claims = JSON.parse(Buffer.from(parts[1], 'base64url').toString());
  assert.ok(Number.isFinite(claims.exp));
  assert.ok(claims.exp * 1000 > Date.now());
});

test('B-PREF-01 save and explicitly clear both preference lists', async () => {
  const {token} = await account();
  const preferences = {dietary:['vegan'],allergens:['peanut']};
  assert.deepEqual(await expect('PUT','/profile/preferences',preferences,token),preferences);
  assert.deepEqual(await expect('GET','/profile/preferences',undefined,token),preferences);
  const empty = {dietary:[],allergens:[]};
  await expect('PUT','/profile/preferences',empty,token);
  assert.deepEqual(await expect('GET','/profile/preferences',undefined,token),empty);
});

test('B-PREF-02 invalid lists do not partially change preferences', async () => {
  const {token} = await account();
  const before = {dietary:['vegetarian'],allergens:['sesame']};
  await expect('PUT','/profile/preferences',before,token);
  await expect('PUT','/profile/preferences',{dietary:['vegan'],allergens:'peanut'},token,400);
  assert.deepEqual(await expect('GET','/profile/preferences',undefined,token),before);
});

const protectedRoutes = [
  ['GET','/profile/preferences'], ['PUT','/profile/preferences',{dietary:[],allergens:[]}],
  ['GET','/inventory'], ['POST','/inventory',{name:'rice'}], ['DELETE','/inventory/foreign'],
  ['POST','/recipes/generate',{}], ['GET','/recipes/foreign'],
  ['POST','/recipes/foreign/shopping-items',{}], ['GET','/shopping-items'],
  ['POST','/shopping-items',{name:'rice'}], ['DELETE','/shopping-items/foreign'],
  ['POST','/favorites',{recipeId:'foreign'}], ['GET','/favorites'],
  ['DELETE','/favorites/foreign'], ['GET','/history'],
];
test('B-SEC-01 every protected method rejects missing and malformed tokens', async () => {
  for (const token of [undefined,'invalid.token.signature']) {
    for (const [method,path,body] of protectedRoutes) await expect(method,path,body,token,401);
  }
});

test('B-SEC-02 a modified JWT payload is rejected', async () => {
  const {token} = await account();
  const [header,payload,signature] = token.split('.');
  const claims = JSON.parse(Buffer.from(payload,'base64url').toString());
  claims.sub = randomUUID();
  const modified = `${header}.${Buffer.from(JSON.stringify(claims)).toString('base64url')}.${signature}`;
  await expect('GET','/inventory',undefined,modified,401);
});

test('B-SEC-05 unsigned JWT algorithm cannot bypass verification', async () => {
  const {token} = await account();
  const payload = token.split('.')[1];
  const header = Buffer.from(JSON.stringify({alg:'none',typ:'JWT'})).toString('base64url');
  await expect('GET','/inventory',undefined,`${header}.${payload}.`,401);
});

test('B-SEC-03 two users cannot list or delete each other inventory', async () => {
  const alice = await account(), bob = await account();
  const saved = await expect('POST','/inventory',{name:'alice-only-rice'},alice.token,201);
  assert.ok(saved.id);
  assert.equal(saved.name,'alice-only-rice');
  assert.ok(Number.isFinite(Date.parse(saved.addedAt)));
  assert.deepEqual(await expect('GET','/inventory',undefined,bob.token),[]);
  const denied = await request('DELETE',`/inventory/${saved.id}`,undefined,bob.token);
  assert.ok([403,404].includes(denied.status));
  assert.deepEqual(await expect('GET','/inventory',undefined,alice.token),[saved]);
  await expect('DELETE',`/inventory/${saved.id}`,undefined,alice.token,204);
  assert.deepEqual(await expect('GET','/inventory',undefined,alice.token),[]);
});

test('B-SEC-04 profile and shopping remain isolated, including supplied owner IDs', async () => {
  const alice = await account(), bob = await account();
  const preferences = {dietary:['vegan'],allergens:['peanut']};
  await expect('PUT','/profile/preferences',preferences,alice.token);
  const item = await expect('POST','/shopping-items',{name:'alice-only-oats'},alice.token,201);
  assert.deepEqual(await expect('GET','/profile/preferences',undefined,bob.token),{dietary:[],allergens:[]});
  const forgedList = await request('GET',`/shopping-items?userId=${encodeURIComponent(alice.user.id)}`,undefined,bob.token);
  assert.ok([200,400].includes(forgedList.status));
  if (forgedList.status === 200) assert.deepEqual(forgedList.body,[]);
  const denied = await request('DELETE',`/shopping-items/${item.id}`,undefined,bob.token);
  assert.ok([403,404].includes(denied.status));
  assert.deepEqual(await expect('GET','/shopping-items',undefined,alice.token),[item]);
  assert.deepEqual(await expect('GET','/favorites',undefined,bob.token),[]);
  assert.deepEqual(await expect('GET','/history',undefined,bob.token),[]);
  assert.deepEqual(await expect('GET','/profile/preferences',undefined,alice.token),preferences);
});
