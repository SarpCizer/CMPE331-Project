import { RecipeGenerationError } from './recipe-generation.mjs';

const statusByCode = new Map([
  ['EMPTY_FRIDGE', 400],
  ['ALLERGEN_CONFLICT', 422],
  ['MALFORMED_OUTPUT', 502],
  ['PROVIDER_UNAVAILABLE', 503],
]);

/** Mount at POST /recipes/generate after the shared authentication middleware. */
export function createGenerateRecipesHandler({ recipeGenerationService, accountIdFromRequest }) {
  return async (request, response, next) => {
    try {
      const owner = accountIdFromRequest(request);
      if (!owner) return response.status(401).json({ error: 'Authentication is required.' });

      const recipes = await recipeGenerationService.generate(owner);
      return response.status(200).json(recipes);
    } catch (error) {
      if (!(error instanceof RecipeGenerationError)) return next(error);

      const status = statusByCode.get(error.code);
      if (!status) return next(error);

      const body = { error: error.message };
      if (error.retryable) body.retryable = true;
      return response.status(status).json(body);
    }
  };
}
