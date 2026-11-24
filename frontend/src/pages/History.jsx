import { useOutletContext } from "react-router-dom";
import Empty from "../components/Empty";
import RecipeCard from "../components/RecipeCard";

// Same English date style as the fridge, independent of the browser language.
const viewedFormat = new Intl.DateTimeFormat("en", {
  dateStyle: "medium",
  timeStyle: "short",
});

export default function HistoryPage() {
  const { data, openRecipe } = useOutletContext();
  return !data.history.length ? (
    <Empty icon="clock" title="A little trip down memory lane" headingLevel={2}>
      Recipes appear here after you open their details.
    </Empty>
  ) : (
    <div className="mt-[25px] grid grid-cols-2 gap-[22px] mobile:grid-cols-[1fr]">
      {data.history.map((item) => (
        <div key={item.recipe.id}>
          <p className="mb-2 text-[0.8rem]">
            Viewed {viewedFormat.format(new Date(item.lastViewedAt))}
          </p>
          <RecipeCard recipe={item.recipe} onOpen={openRecipe} />
        </div>
      ))}
    </div>
  );
}
