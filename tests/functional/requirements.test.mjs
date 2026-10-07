import test from 'node:test';
import assert from 'node:assert/strict';
import { context } from '../helpers/context.mjs';
import { recipes, fixedNow } from '../fixtures/recipes.mjs';

test('US-01-T01 register without email verification', async t => {
const c = await context(t);
const r = await c.request('POST','/accounts',{email:'alice@example.test',password:'LongPass123!'});
assert.equal(r.status,201); assert.ok(r.body.id); assert.equal(r.body.email,'alice@example.test');
assert.equal(r.body.password,undefined); assert.equal(r.body.passwordHash,undefined);
const login = await c.request('POST','/sessions',{email:'alice@example.test',password:'LongPass123!'});
assert.equal(login.status,200); assert.ok(login.body.token);
});

test('US-01-T02 reject duplicate email and invalid registration', async t => {
const c = await context(t); await c.user();
assert.equal((await c.request('POST','/accounts',{email:'ALICE@example.test',password:'LongPass123!'})).status,409);
for (const body of [{email:'bad',password:'LongPass123!'},{email:'bob@example.test',password:'short'}]) {
  assert.equal((await c.request('POST','/accounts',body)).status,400);
}
});

test('US-02-T01 accept correct credentials and reject incorrect credentials', async t => {
const c = await context(t); await c.user();
const ok = await c.request('POST','/sessions',{email:'alice@example.test',password:'LongPass123!'});
assert.equal(ok.status,200); assert.match(ok.body.token,/^[^.]+\.[^.]+\.[^.]+$/);
const bad = await c.request('POST','/sessions',{email:'alice@example.test',password:'wrong'});
assert.equal(bad.status,401); assert.equal(bad.body.token,undefined);
});

test('US-03-T01 persist and clear preferences', async t => {
const c = await context(t), token = await c.user();
const prefs = {dietary:['vegan'],allergens:['peanut']};
assert.equal((await c.request('PUT','/profile/preferences',prefs,token)).status,200);
assert.deepEqual((await c.request('GET','/profile/preferences',undefined,token)).body,prefs);
const empty = {dietary:[],allergens:[]};
assert.equal((await c.request('PUT','/profile/preferences',empty,token)).status,200);
assert.deepEqual((await c.request('GET','/profile/preferences',undefined,token)).body,empty);
});

test('US-04-T01 add an ingredient with addition timestamp', async t => {
const c = await context(t), token = await c.user();
const item = await c.add(token,'rice'); assert.ok(item.id); assert.equal(item.name,'rice');
assert.equal(item.addedAt,fixedNow);
});

test('US-04-T02 reject a blank ingredient', async t => {
const c = await context(t), token = await c.user();
assert.equal((await c.request('POST','/inventory',{name:'  '},token)).status,400);
assert.deepEqual((await c.request('GET','/inventory',undefined,token)).body,[]);
});

test('US-05-T01 list own ingredients and preserve original dates', async t => {
const c = await context(t), token = await c.user();
assert.deepEqual((await c.request('GET','/inventory',undefined,token)).body,[]);
const item = await c.add(token,'tomato'); c.setNow('2026-10-08T12:00:00.000Z');
const r = await c.request('GET','/inventory',undefined,token); assert.equal(r.status,200);
assert.deepEqual(r.body,[item]); assert.equal(r.body[0].addedAt,fixedNow);
});

test('US-06-T01 delete only the selected ingredient', async t => {
const c = await context(t), token = await c.user();
const rice = await c.add(token,'rice'), tomato = await c.add(token,'tomato');
assert.equal((await c.request('DELETE',`/inventory/${rice.id}`,undefined,token)).status,204);
assert.deepEqual((await c.request('GET','/inventory',undefined,token)).body,[tomato]);
assert.equal((await c.request('DELETE','/inventory/does-not-exist',undefined,token)).status,404);
assert.deepEqual((await c.request('GET','/inventory',undefined,token)).body,[tomato]);
});

test('US-07-T01 send fridge and current preferences to provider without deducting inventory', async t => {
const c = await context(t), token = await c.user();
const item = await c.add(token,'rice');
assert.equal((await c.request('PUT','/profile/preferences',{dietary:['vegan'],allergens:['peanut']},token)).status,200);
const result = await c.generate(token); assert.equal(result.length,2);
assert.equal(c.calls.length,1);
assert.deepEqual(c.calls[0],{ingredients:['rice'],dietary:['vegan'],allergens:['peanut']});
assert.deepEqual((await c.request('GET','/inventory',undefined,token)).body,[item]);
});

test('US-07-T02 reject declared allergen conflicts', async t => {
const unsafe = {...recipes[0],ingredients:['rice','peanut']};
const c = await context(t,[unsafe]), token = await c.user(); await c.add(token,'rice');
assert.equal((await c.request('PUT','/profile/preferences',{dietary:[],allergens:['peanut']},token)).status,200);
const r = await c.request('POST','/recipes/generate',{},token);
assert.equal(r.status,422); assert.ok(r.body.error);
assert.equal((await c.request('GET','/recipes/r1',undefined,token)).status,404);
});

test('US-07-T03 block recipe generation for an empty fridge', async t => {
const c = await context(t), token = await c.user();
const r = await c.request('POST','/recipes/generate',{},token);
assert.equal(r.status,400); assert.ok(r.body.error); assert.equal(c.calls.length,0);
});

test('US-08-T01 return complete recipe details', async t => {
const c = await context(t), token = await c.user(); await c.add(token,'rice');
await c.generate(token); const r = await c.request('GET','/recipes/r1',undefined,token);
assert.equal(r.status,200); assert.deepEqual(r.body,recipes[0]);
});

test('US-08-T02 reject malformed recipe output', async t => {
const c = await context(t,[{id:'r1',title:'Incomplete',ingredients:['rice'],steps:[],cookingMinutes:-2}]);
const token = await c.user(); await c.add(token,'rice');
assert.equal((await c.request('POST','/recipes/generate',{},token)).status,502);
assert.equal((await c.request('GET','/recipes/r1',undefined,token)).status,404);
});

test('US-09-T01 return retryable provider error and preserve state', async t => {
const c = await context(t), token = await c.user(); await c.add(token,'rice');
await c.generate(token); await c.request('GET','/recipes/r1',undefined,token);
await c.request('POST','/favorites',{recipeId:'r1'},token);
await c.request('POST','/shopping-items',{name:'onion'},token);
const paths = ['/inventory','/profile/preferences','/favorites','/history','/shopping-items'];
const before = await Promise.all(paths.map(p => c.request('GET',p,undefined,token)));
c.setFailure(new Error('Provider timeout: SECRET_KEY_EXAMPLE'));
const r = await c.request('POST','/recipes/generate',{},token);
assert.equal(r.status,503); assert.equal(r.body.retryable,true);
assert.ok(!JSON.stringify(r.body).includes('SECRET_KEY_EXAMPLE'));
const after = await Promise.all(paths.map(p => c.request('GET',p,undefined,token)));
assert.deepEqual(after,before);
});

test('US-10-T01 add only missing ingredients once', async t => {
const c = await context(t), token = await c.user(); const rice = await c.add(token,' RICE ');
await c.generate(token);
assert.equal((await c.request('POST','/shopping-items',{name:' TOMATO '},token)).status,201);
for (let i=0;i<2;i++) assert.equal((await c.request('POST','/recipes/r1/shopping-items',{},token)).status,200);
const r = await c.request('GET','/shopping-items',undefined,token); assert.equal(r.status,200);
assert.deepEqual(r.body.map(x => x.name.trim().toLowerCase()).sort(),['onion','tomato']);
assert.deepEqual((await c.request('GET','/inventory',undefined,token)).body,[rice]);
});

test('US-11-T01 manually add list and remove shopping items', async t => {
const c = await context(t), token = await c.user();
const item = await c.request('POST','/shopping-items',{name:'onion'},token); assert.equal(item.status,201);
assert.deepEqual((await c.request('GET','/shopping-items',undefined,token)).body,[item.body]);
assert.equal((await c.request('DELETE',`/shopping-items/${item.body.id}`,undefined,token)).status,204);
assert.deepEqual((await c.request('GET','/shopping-items',undefined,token)).body,[]);
assert.deepEqual((await c.request('GET','/inventory',undefined,token)).body,[]);
assert.equal((await c.request('POST','/shopping-items',{name:' '},token)).status,400);
assert.deepEqual((await c.request('GET','/shopping-items',undefined,token)).body,[]);
});

test('US-12-T01 save favorites idempotently without inventory changes', async t => {
const c = await context(t), token = await c.user(); const item = await c.add(token,'rice'); await c.generate(token);
for (let i=0;i<2;i++) assert.equal((await c.request('POST','/favorites',{recipeId:'r1'},token)).status,200);
assert.deepEqual((await c.request('GET','/favorites',undefined,token)).body,[recipes[0]]);
assert.deepEqual((await c.request('GET','/inventory',undefined,token)).body,[item]);
});

test('US-13-T01 remove a favorite while retaining viewed history', async t => {
const c = await context(t), token = await c.user(); await c.add(token,'rice'); await c.generate(token);
assert.deepEqual((await c.request('GET','/favorites',undefined,token)).body,[]);
await c.request('GET','/recipes/r1',undefined,token);
await c.request('POST','/favorites',{recipeId:'r1'},token);
assert.equal((await c.request('DELETE','/favorites/r1',undefined,token)).status,204);
assert.deepEqual((await c.request('GET','/favorites',undefined,token)).body,[]);
assert.equal((await c.request('GET','/history',undefined,token)).body[0].recipe.id,'r1');
});

test('US-14-T01 record views and update history in newest-first order', async t => {
const c = await context(t), token = await c.user(); const item = await c.add(token,'rice'); await c.generate(token);
assert.deepEqual((await c.request('GET','/history',undefined,token)).body,[]);
await c.request('GET','/recipes/r1',undefined,token);
c.setNow('2026-10-07T13:00:00.000Z'); await c.request('GET','/recipes/r2',undefined,token);
c.setNow('2026-10-07T14:00:00.000Z'); await c.request('GET','/recipes/r1',undefined,token);
const r = await c.request('GET','/history',undefined,token); assert.equal(r.status,200);
assert.deepEqual(r.body.map(x => x.recipe.id),['r1','r2']);
assert.equal(r.body[0].lastViewedAt,'2026-10-07T14:00:00.000Z');
assert.deepEqual((await c.request('GET','/inventory',undefined,token)).body,[item]);
});

test('US-15-T01 deny requests without a valid token', async t => {
const c = await context(t); await c.user();
for (const path of ['/inventory','/profile/preferences','/shopping-items','/favorites','/history']) {
  for (const token of [undefined,'invalid-token','eyJhbGciOiJub25lIn0.eyJleHAiOjF9.']) {
    assert.equal((await c.request('GET',path,undefined,token)).status,401);
  }
}
});

test('US-15-T02 isolate user lists and deny access to another users objects', async t => {
const c = await context(t), alice = await c.user(), bob = await c.user('bob@example.test');
const item = await c.add(alice,'rice'); await c.generate(alice);
await c.request('GET','/recipes/r1',undefined,alice);
await c.request('POST','/favorites',{recipeId:'r1'},alice);
const shop = await c.request('POST','/shopping-items',{name:'onion'},alice); assert.equal(shop.status,201);
for (const path of ['/inventory','/shopping-items','/favorites','/history']) {
  const r = await c.request('GET',path,undefined,bob); assert.equal(r.status,200); assert.deepEqual(r.body,[]);
}
for (const [method,path,body] of [
  ['DELETE',`/inventory/${item.id}`],['DELETE',`/shopping-items/${shop.body.id}`],
  ['GET','/recipes/r1'],['POST','/favorites',{recipeId:'r1'}],['POST','/recipes/r1/shopping-items',{}],
]) assert.ok([403,404].includes((await c.request(method,path,body,bob)).status));
assert.deepEqual((await c.request('GET','/inventory',undefined,alice)).body,[item]);
assert.deepEqual((await c.request('GET','/shopping-items',undefined,alice)).body,[shop.body]);
assert.deepEqual((await c.request('GET','/favorites',undefined,alice)).body,[recipes[0]]);
});
