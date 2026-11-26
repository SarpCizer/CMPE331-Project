"""Trusted mood choices: preferences guide recipes, never override restrictions."""
from typing import Literal

Mood = Literal['lazy', 'high-protein', 'sweet', 'budget', 'quick', 'healthy']

MOOD_GUIDANCE = {
    'lazy': 'Choose very easy recipes with minimal hands-on preparation, few steps and little washing up. Total preparation and cooking time must be at most 15 minutes.',
    'high-protein': 'Prioritize protein-rich ingredients that fit the saved dietary preferences. Do not invent protein measurements or claim a verified nutrition target.',
    'sweet': 'Suggest sweet snacks, desserts or naturally sweet dishes that fit the saved dietary preferences.',
    'budget': 'Prioritize ingredients already in the fridge, common affordable staples and minimal extra ingredients. Do not invent prices, savings or a guaranteed cost.',
    'quick': 'Choose straightforward recipes with few steps and a total preparation and cooking time of at most 20 minutes.',
    'healthy': 'Favor balanced meals with vegetables, fiber and suitable protein sources within the saved dietary preferences. Avoid medical, weight-loss or guaranteed health claims.',
}
MOOD_MAX_MINUTES = {'lazy': 15, 'quick': 20}
