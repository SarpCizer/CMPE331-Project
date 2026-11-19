import assert from 'node:assert/strict';
import test from 'node:test';
import { createGenerateRecipesHandler } from '../../src/recipes/generate-recipes-handler.mjs';
import { createOpenAIRecipeProvider } from '../../src/recipes/openai-recipe-provider.mjs';
import { createRecipeGenerationService } from '../../src/recipes/recipe-generation.mjs';
import { recipes } from '../fixtures/recipes.mjs';

const candidates = recipes.map(({ id, ...candidate }) => candidate);
const input = {
  ingredients: ['rice', 'tomato'],
  dietary: ['vegan'],
  allergens: ['peanut'],
};

function completed(...content) {
  return Response.json({
    status: 'completed',
    output: [{ type: 'message', role: 'assistant', content }],
  });
}

function recipeResponse(list = candidates) {
  return completed({ type: 'output_text', text: JSON.stringify({ recipes: list }) });
}

function setup({
  fetchImpl = async () => recipeResponse(),
  snapshot = async () => input,
  insertBatch,
} = {}) {
  const writes = [];
  const generation = createRecipeGenerationService({
    generationInputReader: { snapshot },
    recipeProvider: createOpenAIRecipeProvider({ apiKey: 'unit-test-key', model: 'gpt-4o-mini', fetchImpl }),
    recipeRepository: {
      async insertBatch(owner, batch) {
        writes.push({ owner, batch });
        if (insertBatch) return insertBatch(owner, batch);
        return batch.map((recipe, index) => ({ ...recipe, id: `saved-${index + 1}` }));
      },
    },
  });

  const handler = createGenerateRecipesHandler({
    recipeGenerationService: generation,
    accountIdFromRequest: request => request.auth?.accountId,
  });

  return {
    writes,
    async request(req = { auth: { accountId: 'account-1' } }) {
      const result = {};
      const response = {
        status(code) {
          result.status = code;
          return this;
        },
        json(body) {
          result.body = body;
          return this;
        },
      };
      await handler(req, response, error => { result.forwardedError = error; });
      return result;
    },
  };
}

test('US-07 and US-08: OpenAI gets structured-output instructions and the caller gets complete recipes', async () => {
  let calls = 0;
  const { request, writes } = setup({
    fetchImpl: async (url, options) => {
      calls++;
      assert.equal(url, 'https://api.openai.com/v1/responses');
      assert.equal(options.method, 'POST');
      assert.equal(options.headers.Authorization, 'Bearer unit-test-key');
      assert.ok(options.signal instanceof AbortSignal);

      const body = JSON.parse(options.body);
      assert.equal(body.model, 'gpt-4o-mini');
      assert.equal(body.store, false);
      assert.deepEqual(JSON.parse(body.input), input);
      assert.equal(body.text.format.strict, true);
      const recipeSchema = body.text.format.schema.properties.recipes.items;
      assert.deepEqual(recipeSchema.required, Object.keys(candidates[0]));
      assert.equal(recipeSchema.additionalProperties, false);

      return recipeResponse();
    },
  });
  const result = await request({ auth: { accountId: 'account-1' }, body: { owner: 'other-account' } });
  assert.equal(calls, 1);
  assert.deepEqual(writes, [{ owner: 'account-1', batch: candidates }]);
  assert.deepEqual(result, {
    status: 200,
    body: candidates.map((recipe, index) => ({ ...recipe, id: `saved-${index + 1}` })),
  });
});

test('US-07 / US-15: requests missing verified account or ingredients stop before OpenAI', async () => {
  const { request, writes } = setup({
    snapshot: async () => ({ ...input, ingredients: [] }),
    fetchImpl: async () => assert.fail('OpenAI should not be called'),
  });

  assert.equal((await request({ body: { accountId: 'account-1' } })).status, 401);
  assert.equal((await request()).status, 400);
  assert.deepEqual(writes, []);
});

test('US-07 to US-09: the handler maps provider failures and attempts zero writes', async t => {
  const cases = [
    ['excluded allergen', () => recipeResponse([{ ...candidates[0], ingredients: ['PEANUT'] }]), 422],
    ['invalid JSON', () => completed({ type: 'output_text', text: 'invalid JSON' }), 502],
    ['invalid response envelope', () => new Response('invalid JSON'), 502],
    ['refusal', () => completed({ type: 'refusal', refusal: 'Private detail' }), 502],
    ['incomplete response', () => Response.json({ status: 'incomplete', output: [] }), 502],
    ['service failed', () => Response.json({ status: 'failed', error: 'Private detail' }), 503],
    ['HTTP failure', () => new Response('Private detail', { status: 429 }), 503],
    ['network failure', () => { throw new Error('Private detail'); }, 503],
  ];
  for (const [name, fetchImpl, status] of cases) {
    await t.test(name, async () => {
      const { request, writes } = setup({ fetchImpl });
      const result = await request();
      assert.equal(result.status, status);
      assert.ok(result.body.error);
      assert.equal(result.body.retryable, status === 503 ? true : undefined);
      assert.doesNotMatch(JSON.stringify(result), /Private detail|unit-test-key/);
      assert.deepEqual(writes, []);
    });
  }
});

test('unexpected persistence errors go through the shared error handler', async () => {
  const failure = new Error('Database error');
  const { request } = setup({ insertBatch: async () => { throw failure; } });
  assert.deepEqual(await request(), { forwardedError: failure });
});
