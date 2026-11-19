const MAX_PROVIDER_TIMEOUT_MS = 28_000;

export class RecipeGenerationError extends Error {
  constructor(code, message, { retryable = false } = {}) {
    super(message);
    this.name = 'RecipeGenerationError';
    this.code = code;
    this.retryable = retryable;
  }
}

function malformedOutput() {
  return new RecipeGenerationError('MALFORMED_OUTPUT', 'The recipe service returned an invalid response.');
}

function isNonblank(value) {
  return typeof value === 'string' && value.trim() !== '';
}

function isNonemptyTextList(value) {
  if (!Array.isArray(value) || value.length === 0) return false;
  for (const item of value) {
    if (!isNonblank(item)) return false;
  }
  return true;
}

function validateCandidate(candidate) {
  if (candidate === null || typeof candidate !== 'object' || Array.isArray(candidate)) {
    throw malformedOutput();
  }

  const { title, ingredients, steps, cookingMinutes, caloriesPerServing, servings } = candidate;
  if (!isNonblank(title) || !isNonemptyTextList(ingredients) || !isNonemptyTextList(steps)
    || !Number.isFinite(cookingMinutes) || cookingMinutes <= 0
    || !Number.isFinite(caloriesPerServing) || caloriesPerServing < 0
    || !Number.isInteger(servings) || servings <= 0) {
    throw malformedOutput();
  }

  return { title, ingredients: [...ingredients], steps: [...steps], cookingMinutes, caloriesPerServing, servings };
}

function normalizeName(value) {
  return value.trim().toLowerCase();
}

function validateBatch(candidates, allergens) {
  if (!Array.isArray(candidates) || candidates.length === 0) throw malformedOutput();

  const recipes = Array.from(candidates, validateCandidate);
  const exclusions = new Set(allergens.map(normalizeName));
  if (recipes.some(recipe => recipe.ingredients.some(name => exclusions.has(normalizeName(name))))) {
    throw new RecipeGenerationError('ALLERGEN_CONFLICT', 'The recipe suggestions contain an excluded ingredient.');
  }
  return recipes;
}

async function requestCandidates(provider, input, timeoutMs) {
  const controller = new AbortController();
  let timer;

  try {
    const deadline = new Promise((_, reject) => {
      timer = setTimeout(() => {
        reject(new Error('Recipe provider deadline exceeded.'));
        controller.abort();
      }, timeoutMs);
    });
    return await Promise.race([provider.generate(input, controller.signal), deadline]);
  } catch {
    throw new RecipeGenerationError('PROVIDER_UNAVAILABLE', 'The recipe service is temporarily unavailable.', {
      retryable: true,
    });
  } finally {
    clearTimeout(timer);
  }
}

/**
 * The input reader completes its snapshot before returning. The recipe repository
 * assigns IDs and commits insertBatch atomically for the authenticated owner.
 */
export function createRecipeGenerationService({
  generationInputReader,
  recipeProvider,
  recipeRepository,
  providerTimeoutMs = MAX_PROVIDER_TIMEOUT_MS,
}) {
  if (!Number.isInteger(providerTimeoutMs) || providerTimeoutMs < 1 || providerTimeoutMs > MAX_PROVIDER_TIMEOUT_MS) {
    throw new RangeError('The recipe provider timeout must be between 1 and 28000 milliseconds.');
  }

  return {
    async generate(owner) {
      const { ingredients, dietary, allergens } = await generationInputReader.snapshot(owner);
      if (ingredients.length === 0) {
        throw new RecipeGenerationError('EMPTY_FRIDGE', 'Add an ingredient to your fridge before generating recipes.');
      }

      const exclusions = [...allergens];
      const input = { ingredients: [...ingredients], dietary: [...dietary], allergens: [...exclusions] };
      const candidates = await requestCandidates(recipeProvider, input, providerTimeoutMs);
      return recipeRepository.insertBatch(owner, validateBatch(candidates, exclusions));
    },
  };
}
