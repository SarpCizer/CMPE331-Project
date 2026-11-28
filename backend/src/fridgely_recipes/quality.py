"""Small, explicit checks for defects observed in real generated recipes.

This is not a general food-safety or semantic certification engine.
Thermometer endpoints: https://www.fda.gov/food/buy-store-serve-safe-food/safe-food-handling
"""
import re
import math


class RecipeQualityError(ValueError):
    """A fixed, nonprivate reason for withholding an unusable content candidate."""
    def __init__(self, code):
        super().__init__(code)
        self.code = code


HERBS = {'herb', 'herbs', 'parsley', 'basil', 'oregano', 'cilantro', 'coriander',
         'dill', 'rosemary', 'thyme', 'mint', 'chives'}
CHECKED_EXTRAS = {
    'oil': {'oil'}, 'bread': {'bread', 'toast'}, 'lemon': {'lemon', 'lemons'},
    'lemons': {'lemon', 'lemons'}, 'herb': HERBS, 'herbs': HERBS,
    **{name: {name} for name in HERBS - {'herb', 'herbs'}},
}


def optional_side(words):
    if words[:1] == ['garnish'] or words[:2] == ['serve', 'with']:
        return True
    return (len(words) >= 3 and words[0] == 'serve' and
            words[1] in {'hot', 'warm', 'cold', 'chilled'} and words[2] == 'with')


def review_unlisted_extras(recipe, names):
    """Check the observed English extras; this is not arbitrary-food NLP.

    Remove only standalone optional accompaniments. A required undosed cooking
    ingredient invalidates the candidate; never invent a quantity or replacement.
    """
    listed = {word for name in names for word in re.findall(r'[a-z]+', name)}
    steps = []
    for step in recipe.steps:
        text = step.casefold().strip()
        tokens = re.findall(r'[a-z]+', text)
        words = set(tokens)
        missing = any(word in words and not (aliases & listed) for word, aliases in CHECKED_EXTRAS.items())
        if missing:
            if optional_side(tokens):
                continue
            raise RecipeQualityError('unlisted_step_ingredient')
        steps.append(step)
    if not steps:
        raise RecipeQualityError('missing_preparation')
    return recipe if steps == recipe.steps else recipe.model_copy(update={'steps': steps})


def known_dose(amount):
    parts = amount.split()
    if len(parts) != 2 or parts[1] not in {'g', 'kg', 'ml', 'L', 'pcs', 'pack', 'bunch'}:
        return None
    try:
        number = float(parts[0])
    except ValueError:
        return None
    return (number, parts[1]) if math.isfinite(number) and number > 0 else None


def review_seasoning(recipe, names):
    for name, amount in zip(names, recipe.ingredientAmounts or []):
        if 'salt' in re.findall(r'[a-z]+', name):
            dose = known_dose(amount)
            if dose is None:
                # Preserve legacy display/review; the provider adapter rejects
                # ambiguous new AI amounts and cooking still requires review.
                continue
            number, unit = dose
            if unit not in {'g', 'kg'}:
                raise RecipeQualityError('unmeasured_seasoning')
            # A conservative recipe sanity bound, not a dietary recommendation.
            grams = number * (1000 if unit == 'kg' else 1)
            if grams > 10 * recipe.servings:
                raise RecipeQualityError('excessive_seasoning')


def review_toast(recipe, names):
    toast_dish = re.search(r'\btoast\b', recipe.title.casefold())
    uses_toast = any(re.search(r'\b(?:butter toast|slices? of toast|toast slices?)\b', step.casefold()) for step in recipe.steps)
    if (toast_dish or uses_toast) and not any(
        'bread' in name or 'toast' in name for name in names
    ):
        raise RecipeQualityError('missing_bread')



def protein_notes(names):
    notes = []
    words = {word for name in names for word in re.findall(r'[a-z]+', name)}
    if words & {'chicken', 'turkey', 'duck', 'poultry'}:
        notes.append('Before serving poultry, use a food thermometer in the thickest part to verify at least 74 C (165 F); browning alone does not establish doneness.')
    if words & {'fish', 'salmon', 'cod', 'trout', 'tilapia', 'haddock'}:
        notes.append('Before serving fish, use a food thermometer to verify an internal temperature of at least 63 C (145 F).')
    return notes


def review_recipe(recipe):
    names = [name.casefold().strip() for name in recipe.ingredients]
    review_seasoning(recipe, names)
    recipe = review_unlisted_extras(recipe, names)
    review_toast(recipe, names)
    # Preserve the generated instructions and attach an explicit endpoint before
    # any serving step. Colour alone is not a poultry/fish doneness check.
    notes = protein_notes(names)
    if notes:
        steps = list(recipe.steps)
        index = next((i for i, step in enumerate(steps) if re.search(r'\bserv(e|ing)\b', step.casefold())), len(steps))
        steps[index:index] = notes
        recipe = recipe.model_copy(update={'steps': steps})
    return recipe
