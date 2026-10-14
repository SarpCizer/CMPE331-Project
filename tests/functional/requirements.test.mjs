import test from 'node:test';
import assert from 'node:assert/strict';
import { context } from '../helpers/context.mjs';
import { recipes, fixedNow } from '../fixtures/recipes.mjs';

test('US-01-T01 register without email verification', async t => {
  const c = await context(t);
  const account = await c.expect('POST', '/accounts', {email:'alice@example.test', password:'LongPass123!'}, undefined, 201);
  assert.ok(account.id); assert.equal(account.email, 'alice@example.test');
  assert.equal(account.password, undefined); assert.equal(account.passwordHash, undefined);
  const login = await c.expect('POST', '/sessions', {email:'alice@example.test', password:'LongPass123!'});
  assert.ok(login.token);
});

test('US-01-T02 reject duplicate email and invalid registration without creating an account', async t => {
  const c = await context(t); await c.user();
  await c.expect('POST', '/accounts', {email:'ALICE@example.test', password:'LongPass123!'}, undefined, 409);
  await c.expect('POST', '/accounts', {email:'bad', password:'LongPass123!'}, undefined, 400);
  await c.expect('POST', '/accounts', {email:'bob@example.test', password:'short'}, undefined, 400);
  const bob = await c.expect('POST', '/accounts', {email:'bob@example.test', password:'LongPass123!'}, undefined, 201);
  assert.ok(bob.id); // Rejected registration must not have saved an account.
});

test('US-02-T01 accept correct credentials and reject incorrect credentials', async t => {
  const c = await context(t); await c.user();
  const ok = await c.expect('POST', '/sessions', {email:'alice@example.test', password:'LongPass123!'});
  assert.match(ok.token, /^[^.]+\.[^.]+\.[^.]+$/);
  const bad = await c.expect('POST', '/sessions', {email:'alice@example.test', password:'wrong'}, undefined, 401);
  assert.equal(bad.token, undefined);
});

test('US-03-T01 persist and clear preferences', async t => {
  const c = await context(t), token = await c.user();
  const prefs = {dietary:['vegan'], allergens:['peanut']};
  await c.expect('PUT', '/profile/preferences', prefs, token);
  assert.deepEqual(await c.read('/profile/preferences', token), prefs);
  const empty = {dietary:[], allergens:[]};
  await c.expect('PUT', '/profile/preferences', empty, token);
  assert.deepEqual(await c.read('/profile/preferences', token), empty);
});

test('US-04-T01 add an ingredient with addition timestamp', async t => {
  const c = await context(t), token = await c.user();
  const item = await c.add(token, 'rice');
  assert.ok(item.id); assert.equal(item.name, 'rice'); assert.equal(item.addedAt, fixedNow);
});

test('US-04-T02 reject a blank ingredient', async t => {
  const c = await context(t), token = await c.user();
  await c.expect('POST', '/inventory', {name:'  '}, token, 400);
  assert.deepEqual(await c.read('/inventory', token), []);
});

test('US-05-T01 list own ingredients and preserve original dates', async t => {
  const c = await context(t), token = await c.user();
  assert.deepEqual(await c.read('/inventory', token), []);
  const item = await c.add(token, 'tomato'); c.setNow('2026-10-08T12:00:00.000Z');
  const items = await c.read('/inventory', token);
  assert.deepEqual(items, [item]); assert.equal(items[0].addedAt, fixedNow);
});

test('US-06-T01 delete only the selected ingredient', async t => {
  const c = await context(t), token = await c.user();
  const rice = await c.add(token, 'rice'), tomato = await c.add(token, 'tomato');
  await c.expect('DELETE', `/inventory/${rice.id}`, undefined, token, 204);
  assert.deepEqual(await c.read('/inventory', token), [tomato]);
  await c.expect('DELETE', '/inventory/does-not-exist', undefined, token, 404);
  assert.deepEqual(await c.read('/inventory', token), [tomato]);
});

test('US-07-T01 send fridge and current preferences to provider without deducting inventory', async t => {
  const c = await context(t), token = await c.user();
  const item = await c.add(token, 'rice');
  await c.expect('PUT', '/profile/preferences', {dietary:['vegan'], allergens:['peanut']}, token);
  const result = await c.generate(token); assert.equal(result.length, 2);
  assert.equal(c.calls.length, 1);
  assert.deepEqual(c.calls[0], {ingredients:['rice'], dietary:['vegan'], allergens:['peanut']});
  assert.deepEqual(await c.read('/inventory', token), [item]);
});

test('US-07-T02 reject a batch containing a declared allergen conflict', async t => {
  const unsafe = {...recipes[1], ingredients:['rice', 'peanut']};
  const c = await context(t, [recipes[0], unsafe]), token = await c.user();
  const item = await c.add(token, 'rice');
  await c.expect('PUT', '/profile/preferences', {dietary:[], allergens:['peanut']}, token);
  const error = await c.expect('POST', '/recipes/generate', {}, token, 422);
  assert.ok(error.error); assert.equal(error.recipes, undefined);
  assert.deepEqual(await c.read('/inventory', token), [item]);
  assert.deepEqual(await c.read('/history', token), []);
});

test('US-07-T03 block recipe generation for an empty fridge', async t => {
  const c = await context(t), token = await c.user();
  const error = await c.expect('POST', '/recipes/generate', {}, token, 400);
  assert.ok(error.error); assert.equal(c.calls.length, 0);
});

test('US-08-T01 return complete details using the application-assigned recipe ID', async t => {
  const c = await context(t), token = await c.user(); await c.add(token, 'rice');
  const generated = await c.generate(token);
  const recipe = generated.find(item => item.title === recipes[0].title); assert.ok(recipe?.id);
  assert.deepEqual(await c.read(`/recipes/${recipe.id}`, token), {...recipes[0], id:recipe.id});
});

// Violate one rule per case so another invalid field cannot mask the check.
const malformedCases = [
  ['US-08-T02', 'empty cooking steps', recipe => ({...recipe, steps:[]})],
  ['US-08-T03', 'missing calories', recipe => {const {caloriesPerServing, ...rest} = recipe; return rest;}],
  ['US-08-T04', 'zero cooking time', recipe => ({...recipe, cookingMinutes:0})],
  ['US-08-T05', 'negative calories', recipe => ({...recipe, caloriesPerServing:-1})],
  ['US-08-T06', 'zero servings', recipe => ({...recipe, servings:0})],
  ['US-08-T07', 'blank ingredient names', recipe => ({...recipe, ingredients:[' ']})],
];
for (const [id, reason, invalidate] of malformedCases) {
  test(`${id} reject ${reason}`, async t => {
    const c = await context(t, [invalidate(structuredClone(recipes[0]))]), token = await c.user();
    const item = await c.add(token, 'rice');
    const error = await c.expect('POST', '/recipes/generate', {}, token, 502);
    assert.ok(error.error); assert.equal(error.recipes, undefined);
    assert.deepEqual(await c.read('/inventory', token), [item]);
    assert.deepEqual(await c.read('/history', token), []);
  });
}

test('US-09-T01 return retryable provider error and preserve successful state snapshots', async t => {
  const c = await context(t), token = await c.user(); await c.add(token, 'rice');
  const [recipe] = await c.generate(token);
  await c.read(`/recipes/${recipe.id}`, token);
  await c.expect('POST', '/favorites', {recipeId:recipe.id}, token);
  await c.expect('POST', '/shopping-items', {name:'onion'}, token, 201);
  const paths = ['/inventory', '/profile/preferences', '/favorites', '/history', '/shopping-items'];
  const before = await Promise.all(paths.map(path => c.read(path, token)));
  c.setFailure(new Error('Provider timeout: SECRET_KEY_EXAMPLE'));
  const error = await c.expect('POST', '/recipes/generate', {}, token, 503);
  assert.equal(error.retryable, true); assert.ok(error.error);
  assert.ok(!JSON.stringify(error).includes('SECRET_KEY_EXAMPLE'));
  assert.deepEqual(await Promise.all(paths.map(path => c.read(path, token))), before);
});

test('US-10-T01 add only missing ingredients and preserve item IDs on repeated actions', async t => {
  const c = await context(t), token = await c.user(); const rice = await c.add(token, ' RICE ');
  const generated = await c.generate(token);
  const recipe = generated.find(item => item.title === recipes[0].title); assert.ok(recipe?.id);
  await c.expect('POST', '/shopping-items', {name:' TOMATO '}, token, 201);
  await c.expect('POST', `/recipes/${recipe.id}/shopping-items`, {}, token);
  const first = await c.read('/shopping-items', token);
  await c.expect('POST', `/recipes/${recipe.id}/shopping-items`, {}, token);
  const second = await c.read('/shopping-items', token);
  assert.deepEqual(second.map(x => x.name.trim().toLowerCase()).sort(), ['onion', 'tomato']);
  assert.deepEqual(second.map(x => x.id).sort(), first.map(x => x.id).sort());
  assert.deepEqual(await c.read('/inventory', token), [rice]);
});

test('US-11-T01 manually add list and remove shopping items', async t => {
  const c = await context(t), token = await c.user();
  const item = await c.expect('POST', '/shopping-items', {name:'onion'}, token, 201);
  assert.deepEqual(await c.read('/shopping-items', token), [item]);
  await c.expect('DELETE', `/shopping-items/${item.id}`, undefined, token, 204);
  assert.deepEqual(await c.read('/shopping-items', token), []);
  assert.deepEqual(await c.read('/inventory', token), []);
  await c.expect('POST', '/shopping-items', {name:' '}, token, 400);
  assert.deepEqual(await c.read('/shopping-items', token), []);
});

test('US-12-T01 save favorites idempotently without inventory changes', async t => {
  const c = await context(t), token = await c.user(); const item = await c.add(token, 'rice');
  const [recipe] = await c.generate(token);
  for (let i=0; i<2; i++) await c.expect('POST', '/favorites', {recipeId:recipe.id}, token);
  assert.deepEqual(await c.read('/favorites', token), [recipe]);
  assert.deepEqual(await c.read('/inventory', token), [item]);
});

test('US-13-T01 remove a favorite while retaining viewed history', async t => {
  const c = await context(t), token = await c.user(); await c.add(token, 'rice');
  const [recipe] = await c.generate(token);
  assert.deepEqual(await c.read('/favorites', token), []);
  await c.read(`/recipes/${recipe.id}`, token);
  await c.expect('POST', '/favorites', {recipeId:recipe.id}, token);
  await c.expect('DELETE', `/favorites/${recipe.id}`, undefined, token, 204);
  assert.deepEqual(await c.read('/favorites', token), []);
  const history = await c.read('/history', token);
  assert.equal(history.length, 1); assert.equal(history[0].recipe.id, recipe.id);
});

test('US-14-T01 record views and update history in newest-first order', async t => {
  const c = await context(t), token = await c.user(); const item = await c.add(token, 'rice');
  const [first, second] = await c.generate(token);
  assert.deepEqual(await c.read('/history', token), []);
  await c.read(`/recipes/${first.id}`, token);
  c.setNow('2026-10-07T13:00:00.000Z'); await c.read(`/recipes/${second.id}`, token);
  c.setNow('2026-10-07T14:00:00.000Z'); await c.read(`/recipes/${first.id}`, token);
  const history = await c.read('/history', token);
  assert.deepEqual(history.map(x => x.recipe.id), [first.id, second.id]);
  assert.equal(history[0].lastViewedAt, '2026-10-07T14:00:00.000Z');
  assert.deepEqual(await c.read('/inventory', token), [item]);
});

test('US-15-T01 deny requests with no token or a malformed token', async t => {
  const c = await context(t);
  for (const path of ['/inventory', '/profile/preferences', '/shopping-items', '/favorites', '/history']) {
    for (const token of [undefined, 'invalid-token']) await c.expect('GET', path, undefined, token, 401);
  }
});

test('US-15-T02 isolate personal data and deny access to another users objects', async t => {
  const c = await context(t), alice = await c.user(), bob = await c.user('bob@example.test');
  const item = await c.add(alice, 'rice'), [recipe] = await c.generate(alice);
  await c.read(`/recipes/${recipe.id}`, alice);
  await c.expect('POST', '/favorites', {recipeId:recipe.id}, alice);
  const shop = await c.expect('POST', '/shopping-items', {name:'onion'}, alice, 201);
  const alicePrefs = {dietary:['vegan'], allergens:['peanut']};
  await c.expect('PUT', '/profile/preferences', alicePrefs, alice);
  assert.deepEqual(await c.read('/profile/preferences', bob), {dietary:[], allergens:[]});
  for (const path of ['/inventory', '/shopping-items', '/favorites', '/history']) {
    assert.deepEqual(await c.read(path, bob), []);
  }
  for (const [method, path, body] of [
    ['DELETE', `/inventory/${item.id}`], ['DELETE', `/shopping-items/${shop.id}`],
    ['GET', `/recipes/${recipe.id}`], ['DELETE', `/favorites/${recipe.id}`],
    ['POST', '/favorites', {recipeId:recipe.id}], ['POST', `/recipes/${recipe.id}/shopping-items`, {}],
  ]) assert.ok([403, 404].includes((await c.request(method, path, body, bob)).status), `${method} ${path} must deny cross-user access`);
  await c.expect('PUT', '/profile/preferences', {dietary:[], allergens:[]}, bob);
  assert.deepEqual(await c.read('/profile/preferences', alice), alicePrefs);
  assert.deepEqual(await c.read('/inventory', alice), [item]);
  assert.deepEqual(await c.read('/shopping-items', alice), [shop]);
  assert.deepEqual(await c.read('/favorites', alice), [recipe]);
});

test('US-15-T03 reject an authentic token after its expiry', async t => {
  const c = await context(t), token = await c.user();
  await c.read('/inventory', token); // The issued token works before expiry.
  const claims = JSON.parse(Buffer.from(token.split('.')[1], 'base64url').toString('utf8'));
  assert.ok(Number.isFinite(claims.exp), 'Issued JWT must contain a finite expiry');
  c.setNow(new Date((claims.exp + 1) * 1000).toISOString());
  for (const path of ['/inventory', '/profile/preferences', '/shopping-items', '/favorites', '/history']) {
    await c.expect('GET', path, undefined, token, 401);
  }
});
