import { useOutletContext } from "react-router-dom";
import Empty from "../components/Empty";
import RecipeCard from "../components/RecipeCard";

export default function FavoritesPage() {
  const { data, openRecipe } = useOutletContext();
  return (!data.favorites.length ? (
    <Empty
      icon="heart"
      title="Keep the good ones close"
      headingLevel={2}
    >
      Save a recipe you love and find it here next time.
    </Empty>
  ) : (
    <div className="recipe-grid">
      {data.favorites.map((recipe) => (
        <RecipeCard
          recipe={recipe}
          key={recipe.id}
          onOpen={openRecipe}
        />
      ))}
    </div>
  ));
}
