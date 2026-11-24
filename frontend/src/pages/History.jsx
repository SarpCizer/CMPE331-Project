import { useOutletContext } from "react-router-dom";
import Empty from "../components/Empty";
import RecipeCard from "../components/RecipeCard";

export default function HistoryPage() {
  const { data, openRecipe } = useOutletContext();
  return (!data.history.length ? (
    <Empty
      icon="clock"
      title="A little trip down memory lane"
      headingLevel={2}
    >
      Recipes appear here after you open their details.
    </Empty>
  ) : (
    <div className="recipe-grid">
      {data.history.map((item) => (
        <div key={item.recipe.id}>
          <p className="viewed">
            Viewed {new Date(item.lastViewedAt).toLocaleString()}
          </p>
          <RecipeCard recipe={item.recipe} onOpen={openRecipe} />
        </div>
      ))}
    </div>
  ));
}
