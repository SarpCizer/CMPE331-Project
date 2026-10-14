import assert from 'node:assert/strict';
import { createAcceptanceApp } from '../../src/acceptance-app.mjs';
import { recipes, fixedNow } from '../fixtures/recipes.mjs';

export async function context(t, output = recipes) {
  const calls = [];
  let failure;
  let now = fixedNow;
  const app = await createAcceptanceApp({
    clock: () => now,
    recipeProvider: { async generate(input) {
      calls.push(structuredClone(input));
      if (failure) throw failure;
      return structuredClone(output);
    } },
  });
  t.after(() => app.close());
  // Detach snapshots so later mutations cannot hide a state-preservation failure.
  const request = async (method, path, body, token) => structuredClone(
    await app.request({ method, path, body: structuredClone(body), token }));
  const expect = async (method, path, body, token, status = 200) => {
    const response = await request(method, path, body, token);
    assert.equal(response.status, status, `${method} ${path}: expected ${status}, got ${response.status}`);
    return response.body;
  };
  const read = (path, token) => expect('GET', path, undefined, token);
  return { calls, request, expect, read, setFailure: e => { failure = e; }, setNow: v => { now = v; },
    async user(email = 'alice@example.test') {
      const reg = await request('POST', '/accounts', { email, password: 'LongPass123!' });
      assert.equal(reg.status, 201, 'Registration must create an account');
      const login = await request('POST', '/sessions', { email, password: 'LongPass123!' });
      assert.equal(login.status, 200, 'Sign-in must succeed');
      assert.ok(login.body.token, 'Sign-in must return a token');
      return login.body.token;
    },
    async add(token, name) {
      const res = await request('POST', '/inventory', { name }, token);
      assert.equal(res.status, 201); return res.body;
    },
    async generate(token) {
      const res = await request('POST', '/recipes/generate', {}, token);
      assert.equal(res.status, 200); return res.body;
    },
  };
}
