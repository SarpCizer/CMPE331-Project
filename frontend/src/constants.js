export const initialData = () => ({
  inventory: [],
  preferences: { dietary: [], allergens: [] },
  shopping: [],
  favorites: [],
  history: [],
});
export const sections = [
  ["fridge", "My fridge", "fridge"],
  ["recipes", "Find recipes", "leaf"],
  ["weekly-plan", "Weekly meal planner", "calendar"],
  ["shopping", "Shopping list", "bag"],
  ["favorites", "Favorites", "heart"],
  ["history", "Recently viewed", "clock"],
  ["preferences", "Preferences", "settings"],
];
export const paths = {
  inventory: "/inventory",
  preferences: "/profile/preferences",
  shopping: "/shopping-items",
  favorites: "/favorites",
  history: "/history",
};
export const resourceLabels = {
  inventory: "Ingredients",
  preferences: "Preferences",
  shopping: "Shopping list",
  favorites: "Favorites",
  history: "Recently viewed",
};
export const pageResources = {
  fridge: "inventory",
  recipes: "inventory",
  shopping: "shopping",
  "weekly-plan": "favorites",
  preferences: "preferences",
  favorites: "favorites",
  history: "history",
};
export const initialResources = (pending = false) =>
  Object.fromEntries(
    Object.keys(paths).map((key) => [key, { pending, error: "" }]),
  );
