import { Link, useOutletContext } from "react-router-dom";
import Empty from "../components/Empty";
import Icon from "../components/Icon";
import RecipeCard from "../components/RecipeCard";

export default function RecipesPage() {
  const { data, api, run, busy, generated, setGenerated, openRecipe } = useOutletContext();
  return (
    <>
      <section className="recipe-intro panel">
        <span className="eyebrow">A LITTLE INSPIRATION</span>
        <h2>Something good is already here.</h2>
        <p>
          Turn the {data.inventory.length} ingredients in your fridge
          into your next meal, with your saved preferences included.
        </p>
        <button
          className="primary"
          disabled={!data.inventory.length}
          onClick={async () => {
            const result = await run(
              () =>
                api("/recipes/generate", {
                  method: "POST",
                  body: {},
                }),
              "Recipes are ready.",
            );
            if (Array.isArray(result)) setGenerated(result);
          }}
        >
          <Icon />
          {busy ? "Finding inspiration…" : "Generate recipes"}
        </button>
        <Link className="text-link" to="/preferences">
          Edit your preferences
        </Link>
      </section>
      {!data.inventory.length ? (
        <Empty icon="fridge" title="Start with an ingredient">
          Add something to your fridge before asking for recipes.
        </Empty>
      ) : !generated.length ? (
        <Empty title="Your next meal starts here">
          Generate a few ideas from the ingredients you already have.
        </Empty>
      ) : (
        <div className="recipe-grid">
          {generated.map((recipe) => (
            <RecipeCard
              recipe={recipe}
              key={recipe.id}
              onOpen={openRecipe}
            />
          ))}
        </div>
      )}
    </>
  );
}
