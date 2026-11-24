import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import Icon from "./Icon";
import ResourceError from "./ResourceError";

export default function RecipeDialog({
  recipe,
  onClose,
  run,
  api,
  favorites,
  busy,
  error,
  notice,
  favoriteState,
  retryFavorites,
}) {
  const dialog = useRef(null);
  const [shoppingAdded, setShoppingAdded] = useState(false);
  useEffect(() => {
    const element = dialog.current;
    element.showModal();
    return () => element.close();
  }, []);
  const saved = favorites.some((item) => item.id === recipe.id);
  return (
    <dialog
      ref={dialog}
      onCancel={onClose}
      className="max-h-[85vh] w-[min(680px,calc(100vw_-_32px))] overflow-auto rounded-[24px] border border-line bg-[#fcfdfb] p-[30px] text-ink backdrop:bg-[#17322180] backdrop:[backdrop-filter:blur(3px)] motion-safe:open:animate-appear mobile:p-[23px]"
      aria-labelledby="recipe-title"
    >
      <div className="flex items-center justify-between gap-3">
        <span className="eyebrow m-0">A LITTLE INSPIRATION</span>
        <button
          className="flex rounded-[50%] bg-[#edf1e9] p-2 text-green"
          aria-label="Close recipe"
          onClick={onClose}
        >
          <Icon name="close" />
        </button>
      </div>
      <h2
        id="recipe-title"
        className="mt-[22px] text-[2rem] wrap-anywhere mobile:text-[1.75rem]"
      >
        {recipe.title}
      </h2>
      <p className="rounded-[10px] bg-[#edf2e7] p-3 text-[0.85rem] text-[#50644e]">
        Estimated {recipe.cookingMinutes} minutes · {recipe.caloriesPerServing}{" "}
        kcal per serving · {recipe.servings} servings
      </p>
      <p className="muted">
        AI-generated recipe. Review the ingredients against your dietary needs
        before cooking.
      </p>
      {error && (
        <div className="alert-error message" role="alert">
          {error}
        </div>
      )}
      {notice && (
        <div className="alert-success message" role="status">
          {notice}
        </div>
      )}
      {busy && <p role="status">Saving your changes…</p>}
      <h3 className="mt-7">Ingredients</h3>
      <ul className="flex list-none flex-wrap gap-2 p-0">
        {recipe.ingredients.map((name, index) => (
          <li
            key={index}
            className="max-w-full rounded-lg border border-[#d8e2d2] px-[10px] py-[5px] text-[0.9rem] wrap-anywhere"
          >
            {name}
          </li>
        ))}
      </ul>
      <h3 className="mt-7">Let's make it</h3>
      <ol className="pl-6">
        {recipe.steps.map((step, index) => (
          <li
            key={index}
            className="mb-[14px] pl-[7px] wrap-anywhere marker:font-[650] marker:text-[#658260]"
          >
            {step}
          </li>
        ))}
      </ol>
      <div className="mt-[30px] flex flex-wrap gap-3">
        <button
          className="btn-primary mobile:w-full"
          disabled={busy}
          onClick={async () => {
            const result = await run(
              () =>
                api(`/recipes/${recipe.id}/shopping-items`, {
                  method: "POST",
                  body: {},
                }),
              "Missing ingredients added to shopping.",
              ["shopping"],
            );
            if (result) setShoppingAdded(true);
          }}
        >
          Add missing ingredients
        </button>
        <button
          className="btn-secondary mobile:w-full"
          disabled={busy || favoriteState.pending || !!favoriteState.error}
          onClick={() =>
            run(
              () =>
                api(saved ? `/favorites/${recipe.id}` : "/favorites", {
                  method: saved ? "DELETE" : "POST",
                  ...(saved ? {} : { body: { recipeId: recipe.id } }),
                }),
              saved ? "Favorite removed." : "Recipe saved to favorites.",
              ["favorites"],
            )
          }
        >
          {saved ? "Remove favorite" : "Save favorite"}
        </button>
        {shoppingAdded && (
          <Link className="link-text" to="/shopping" onClick={onClose}>
            View shopping list
          </Link>
        )}
      </div>
      {favoriteState.pending && <p role="status">Loading favorites…</p>}
      {favoriteState.error && (
        <ResourceError
          label="Favorites"
          error={favoriteState.error}
          retry={retryFavorites}
          busy={busy}
        />
      )}
    </dialog>
  );
}
