"""Small, explicit checks for defects observed in real generated recipes.

This is not a general food-safety or semantic certification engine.
Thermometer endpoints: https://www.fda.gov/food/buy-store-serve-safe-food/safe-food-handling
"""
import re


def review_seasoning(recipe, names):
    for name, amount in zip(names, recipe.ingredientAmounts or []):
        if 'salt' in re.findall(r'[a-z]+', name):
            number, unit = amount.split()
            if unit not in {'g', 'kg'}:
                raise ValueError('Seasoning needs a measured cooking amount, not a stock package.')
            # A conservative recipe sanity bound, not a dietary recommendation.
            grams = float(number) * (1000 if unit == 'kg' else 1)
            if grams > 10 * recipe.servings:
                raise ValueError('The seasoning amount needs review before this recipe can be used.')


def review_toast(recipe, names):
    toast_dish = re.search(r'\btoast\b', recipe.title.casefold())
    uses_toast = any(re.search(r'\b(?:butter toast|slices? of toast|toast slices?)\b', step.casefold()) for step in recipe.steps)
    if (toast_dish or uses_toast) and not any(
        'bread' in name or 'toast' in name for name in names
    ):
        raise ValueError('Toast preparation is missing its bread ingredient.')



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
