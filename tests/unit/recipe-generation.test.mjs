import assert from 'node:assert/strict';
import test from 'node:test';
import { createRecipeGenerationService } from '../../src/recipes/recipe-generation.mjs';
import { recipes } from '../fixtures/recipes.mjs';

function setup({
  input = { ingredients: ['rice'], dietary: ['vegan'], allergens: ['peanut'] },
  generate = async () => recipes,
  providerTimeoutMs = 1_000,
} = {}) {
  const ownersRead = [];
  const calls = [];
  const writes = [];
  const service = createRecipeGenerationService({
    generationInputReader: {
      async snapshot(owner) {
        ownersRead.push(owner);
        return input;
      },
    },
    recipeProvider: {
      async generate(request, signal) {
        calls.push(structuredClone(request));
        return generate(request, signal);
      },
    },
    recipeRepository: {
      async insertBatch(owner, candidates) {
        writes.push({ owner, candidates });
        return candidates.map((recipe, index) => ({ ...recipe, id: `saved-${index + 1}` }));
      },
    },
    providerTimeoutMs,
  });
  return { service, ownersRead, calls, writes };
}

test('US-07: sends only the snapshot fields and saves validated recipes for the owner', async () => {
  const input = {
    ingredients: ['rice', 'tomato'],
    dietary: ['vegan', 'gluten-free', 'vegan'],
    allergens: ['peanut'],
    email: 'private@example.test',
  };
  const before = structuredClone(input);
  const { service, ownersRead, calls, writes } = setup({
    input,
    generate: async request => {
      request.ingredients.pop();
      request.dietary.reverse();
      request.allergens.length = 0;
      return recipes.map(recipe => ({ ...recipe, providerMetadata: 'discard' }));
    },
  });
  const result = await service.generate('account-1');
  const expected = recipes.map(({ id, ...recipe }) => recipe);

  assert.deepEqual(input, before);
  assert.deepEqual(ownersRead, ['account-1']);
  assert.deepEqual(calls, [{ ingredients: before.ingredients, dietary: before.dietary, allergens: before.allergens }]);
  assert.deepEqual(writes, [{ owner: 'account-1', candidates: expected }]);
  assert.deepEqual(result, expected.map((recipe, index) => ({ ...recipe, id: `saved-${index + 1}` })));
});

test('US-07: an empty fridge makes no provider call or write', async () => {
  const { service, calls, writes } = setup({ input: { ingredients: [], dietary: [], allergens: [] } });
  await assert.rejects(service.generate('account-1'), { code: 'EMPTY_FRIDGE' });
  assert.deepEqual(calls, []);
  assert.deepEqual(writes, []);
});

test('US-07: a declared allergen blocks the entire batch even if the provider edited its input', async () => {
  const { service, writes } = setup({
    generate: async request => {
      request.allergens.pop();
      return [recipes[0], { ...recipes[1], ingredients: ['rice', ' PEANUT '] }];
    },
  });
  await assert.rejects(service.generate('account-1'), { code: 'ALLERGEN_CONFLICT' });
  assert.deepEqual(writes, []);
});

test('US-08: malformed output is rejected before any recipe is written', async t => {
  const candidate = recipes[0];
  const malformed = [
    ['null response', null],
    ['empty batch', []],
    ['non-object candidate', [null]],
    ['blank title', [{ ...candidate, title: ' ' }]],
    ['empty steps', [{ ...candidate, steps: [] }]],
    ['zero cooking time', [{ ...candidate, cookingMinutes: 0 }]],
    ['missing calories', [{ ...candidate, caloriesPerServing: undefined }]],
    ['negative calories', [{ ...candidate, caloriesPerServing: -1 }]],
    ['infinite calories', [{ ...candidate, caloriesPerServing: Infinity }]],
    ['fractional servings', [{ ...candidate, servings: 1.5 }]],
    ['blank ingredient in the second recipe', [candidate, { ...recipes[1], ingredients: [' '] }]],
    ['allergen conflict followed by malformed output', [
      { ...candidate, ingredients: ['peanut'] }, { ...recipes[1], steps: [] },
    ]],
  ];
  for (const [name, output] of malformed) {
    await t.test(name, async () => {
      const { service, writes } = setup({ generate: async () => output });
      await assert.rejects(service.generate('account-1'), { code: 'MALFORMED_OUTPUT' });
      assert.deepEqual(writes, []);
    });
  }
});

test('US-09: provider failure is retryable and omits raw diagnostics', async () => {
  let failed = false;
  const { service, writes } = setup({
    generate: async () => {
      if (failed) return recipes;
      failed = true;
      throw new Error('Example raw provider diagnostic');
    },
  });
  await assert.rejects(service.generate('account-1'), {
    code: 'PROVIDER_UNAVAILABLE',
    message: 'The recipe service is temporarily unavailable.',
    retryable: true,
  });
  assert.deepEqual(writes, []);
  assert.equal((await service.generate('account-1')).length, recipes.length);
});

test('US-09: a stalled provider is aborted and no write is attempted', async () => {
  let providerSignal;
  const { service, writes } = setup({
    providerTimeoutMs: 10,
    generate: (_input, signal) => {
      providerSignal = signal;
      return new Promise(() => {});
    },
  });
  await assert.rejects(service.generate('account-1'), { code: 'PROVIDER_UNAVAILABLE', retryable: true });
  assert.equal(providerSignal.aborted, true);
  assert.deepEqual(writes, []);
});

test('NFR-04: the provider deadline must leave time to complete the request', () => {
  assert.throws(() => setup({ providerTimeoutMs: 30_000 }), RangeError);
});
