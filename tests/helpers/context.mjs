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
  const request = (method, path, body, token) => app.request({ method, path, body, token });
  return { calls, request, setFailure: e => { failure = e; }, setNow: v => { now = v; },
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
