import Icon from "./Icon";

// `warm` gives every second card in a grid the alternate artwork colours.
export default function RecipeCard({ recipe, onOpen, warm = false }) {
  return (
    <article className="flex h-full flex-col overflow-hidden rounded-[19px] border border-line bg-white">
      <div
        className={`flex h-[135px] items-center justify-center gap-[17px] ${
          warm ? "bg-[#f3e9d9] text-[#795a2c]" : "bg-[#e7eddd] text-[#627c51]"
        }`}
      >
        <Icon name="leaf" width="46" height="46" />
        <span className="max-w-[100px] text-[0.65rem] leading-[1.8] font-[650] tracking-[0.16em]">
          MADE FOR YOUR KITCHEN
        </span>
      </div>
      <div className="flex flex-1 flex-col p-6">
        <h2 className="text-[1.35rem] wrap-anywhere">{recipe.title}</h2>
        <div className="mb-[9px] flex flex-wrap items-center gap-[14px] text-[0.85rem] text-[#5c715f]">
          <span className="flex items-center gap-[5px]">
            <Icon name="clock" width="16" height="16" />
            {recipe.cookingMinutes} min
          </span>
          <span className="flex items-center gap-[5px]">
            {recipe.caloriesPerServing} kcal / serving
          </span>
        </div>
        <small className="mb-[15px] text-[0.75rem]">
          Time &amp; calories are estimates · {recipe.servings}{" "}
          {recipe.servings === 1 ? "serving" : "servings"}
        </small>
        <p className="flex-1 text-[0.9rem] wrap-anywhere">
          {recipe.ingredients.join(", ")}
        </p>
        <button
          className="btn-secondary self-start"
          onClick={() => onOpen(recipe.id)}
        >
          View recipe
        </button>
      </div>
    </article>
  );
}
