import Icon from "./Icon";

export default function RecipeCard({ recipe, onOpen }) {
  return (
    <article className="recipe-card">
      <div className="recipe-art">
        <Icon name="leaf" width="46" height="46" />
        <span>MADE FOR YOUR KITCHEN</span>
      </div>
      <div className="recipe-content">
        <h2>{recipe.title}</h2>
        <div className="recipe-meta">
          <span>
            <Icon name="clock" width="16" height="16" />
            {recipe.cookingMinutes} min
          </span>
          <span>{recipe.caloriesPerServing} kcal / serving</span>
        </div>
        <small>
          Time &amp; calories are estimates · {recipe.servings}{" "}
          {recipe.servings === 1 ? "serving" : "servings"}
        </small>
        <p>{recipe.ingredients.join(", ")}</p>
        <button className="secondary" onClick={() => onOpen(recipe.id)}>
          View recipe
        </button>
      </div>
    </article>
  );
}
