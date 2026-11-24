import { useOutletContext } from "react-router-dom";
import Empty from "../components/Empty";
import RecipeCard from "../components/RecipeCard";

export default function FavoritesPage() {
  const { data, openRecipe } = useOutletContext();
  return !data.favorites.length ? (
    <Empty icon="heart" title="Keep the good ones close" headingLevel={2}>
      Save a recipe you love and find it here next time.
    </Empty>
  ) : (
    <div className="mt-[25px] grid grid-cols-2 gap-[22px] mobile:grid-cols-[1fr]">
      {data.favorites.map((recipe, index) => (
        <RecipeCard
          recipe={recipe}
          key={recipe.id}
          onOpen={openRecipe}
          warm={index % 2 === 1}
        />
      ))}
    </div>
  );
}
