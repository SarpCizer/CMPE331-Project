import { Link, useOutletContext } from "react-router-dom";
import Empty from "../components/Empty";
import Icon from "../components/Icon";
import RecipeCard from "../components/RecipeCard";

export default function RecipesPage() {
  const { data, api, run, busy, generated, setGenerated, openRecipe } =
    useOutletContext();
  const stocked = data.inventory.filter(item => item.quantity == null || item.quantity > 0);
  return (
    <>
      <section className="panel bg-[#eaf0e6]">
        <span className="eyebrow">A LITTLE INSPIRATION</span>
        <h2>Something good is already here.</h2>
        <p className="max-w-[580px] text-[0.95rem]">
          Turn the {stocked.length}{" "}
          {stocked.length === 1 ? "ingredient" : "ingredients"} in your
          fridge into your next meal, with your saved preferences included.
        </p>
        <button
          className="btn-primary"
          disabled={!stocked.length}
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
        <Link
          className="link-text ml-[18px] inline-block text-[0.85rem] mobile:mt-[17px] mobile:ml-0 mobile:block"
          to="/preferences"
        >
          Edit your preferences
        </Link>
      </section>
      {!stocked.length ? (
        <Empty icon="fridge" title="Start with an ingredient">
          Add something to your fridge before asking for recipes.
        </Empty>
      ) : !generated.length ? (
        <Empty title="Your next meal starts here">
          Generate a few ideas from the ingredients you already have.
        </Empty>
      ) : (
        <div className="mt-[25px] grid grid-cols-2 gap-[22px] mobile:grid-cols-[1fr]">
          {generated.map((recipe, index) => (
            <RecipeCard
              recipe={recipe}
              key={recipe.id}
              onOpen={openRecipe}
              warm={index % 2 === 1}
            />
          ))}
        </div>
      )}
    </>
  );
}
