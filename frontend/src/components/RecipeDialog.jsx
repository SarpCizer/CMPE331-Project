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
      className="recipe-dialog"
      aria-labelledby="recipe-title"
    >
      <div className="dialog-top">
        <span className="eyebrow">A LITTLE INSPIRATION</span>
        <button
          className="icon-button"
          aria-label="Close recipe"
          onClick={onClose}
        >
          <Icon name="close" />
        </button>
      </div>
      <h2 id="recipe-title">{recipe.title}</h2>
      <p className="estimate">
        Estimated {recipe.cookingMinutes} minutes · {recipe.caloriesPerServing}{" "}
        kcal per serving · {recipe.servings} servings
      </p>
      <p className="muted">
        AI-generated recipe. Review the ingredients against your dietary needs
        before cooking.
      </p>
      {error && (
        <div className="message error" role="alert">
          {error}
        </div>
      )}
      {notice && (
        <div className="message success" role="status">
          {notice}
        </div>
      )}
      {busy && <p role="status">Saving your changes…</p>}
      <h3>Ingredients</h3>
      <ul className="recipe-ingredients">
        {recipe.ingredients.map((name, index) => (
          <li key={index}>{name}</li>
        ))}
      </ul>
      <h3>Let's make it</h3>
      <ol className="steps">
        {recipe.steps.map((step, index) => (
          <li key={index}>{step}</li>
        ))}
      </ol>
      <div className="dialog-actions">
        <button
          className="primary"
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
          className="secondary"
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
          <Link className="text-link" to="/shopping" onClick={onClose}>
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
