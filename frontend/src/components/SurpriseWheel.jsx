import { useEffect, useRef, useState } from "react";

const colors = [
  "#174c3a",
  "#537e59",
  "#885536",
  "#486548",
  "#315f50",
  "#6e592b",
];
export default function SurpriseWheel({
  visibleRecipes = [],
  busy,
  openRecipe,
}) {
  // The wheel and the cards intentionally share one current generation.
  // Availability is reviewed in recipe details and confirmed cooking, not here.
  const recipes = visibleRecipes;
  const [selected, setSelected] = useState(null),
    [spinning, setSpinning] = useState(false),
    [rotation, setRotation] = useState(0);
  const alive = useRef(true),
    timer = useRef(null),
    angle = useRef(0),
    lock = useRef(false);
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
      clearTimeout(timer.current);
    };
  }, []);
  function refresh() {
    setSelected(null);
    angle.current = 0;
    setRotation(0);
  }
  function spin() {
    if (lock.current || busy || !recipes.length) return;
    lock.current = true;
    const values = new Uint32Array(1);
    crypto.getRandomValues(values);
    const index = Math.floor((values[0] / 4294967296) * recipes.length);
    const chosen = recipes[index];
    const target = 360 - ((index + 0.5) * 360) / recipes.length;
    angle.current += 1080 + ((target - (angle.current % 360) + 360) % 360);
    setSelected(null);
    setRotation(angle.current);
    setSpinning(true);
    timer.current = setTimeout(
      () => {
        if (alive.current) {
          setSelected(chosen);
          setSpinning(false);
        }
        lock.current = false;
      },
      matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 2200,
    );
  }
  const gradient = recipes.length
    ? `conic-gradient(${recipes.map((_, i) => `${colors[i % colors.length]} ${(i * 360) / recipes.length}deg ${((i + 1) * 360) / recipes.length}deg`).join(",")})`
    : "#e5ece2";
  return (
    <section className="panel mt-6" aria-label="Surprise me recipe wheel">
      <span className="eyebrow">LET YOUR FRIDGE DECIDE</span>
      <h2>Surprise me.</h2>
      <p>
        Every recipe shown below has a place on the wheel. Spin to choose one,
        then review ingredients and quantities before cooking. Spinning uses no
        AI requests and does not use up ingredients.
      </p>
      <div className="flex flex-wrap items-center gap-8">
        <div
          className="relative mx-auto h-[260px] w-[260px] shrink-0"
          aria-hidden="true"
        >
          <div className="absolute left-1/2 top-0 z-10 -translate-x-1/2 text-3xl text-[#b57950]">
            ▼
          </div>
          <div
            className="h-full w-full rounded-full border-8 border-[#e5ece2] shadow-inner"
            style={{
              background: gradient,
              transform: `rotate(${rotation}deg)`,
              transition:
                spinning &&
                !matchMedia("(prefers-reduced-motion: reduce)").matches
                  ? "transform 2.2s cubic-bezier(.15,.7,.15,1)"
                  : undefined,
            }}
          >
            {recipes.map((recipe, i) => (
              <span
                key={recipe.id}
                className="absolute left-1/2 top-1/2 text-xs font-semibold text-white"
                style={{
                  transform: `rotate(${((i + 0.5) * 360) / recipes.length - 90}deg) translate(40px,-50%)`,
                  transformOrigin: "0 0",
                  width: 76,
                  overflow: "hidden",
                  whiteSpace: "nowrap",
                  textOverflow: "ellipsis",
                }}
              >
                {recipes.length > 12 ? i + 1 : recipe.title}
              </span>
            ))}
          </div>
        </div>
        <div className="min-w-0 flex-1">
          <button
            type="button"
            className="btn-primary"
            disabled={busy || spinning || !visibleRecipes.length}
            onClick={spin}
          >
            {spinning ? "Choosing your meal…" : "Spin the wheel"}
          </button>
          <button
            type="button"
            className="btn-text ml-3"
            disabled={busy || spinning || !visibleRecipes.length}
            onClick={refresh}
          >
            Refresh wheel recipes
          </button>
          <div role="status" aria-live="polite" className="mt-4">
            {selected ? (
              <>
                <h3>{selected.title}</h3>
                <p>
                  {selected.servings}{" "}
                  {selected.servings === 1 ? "portion" : "portions"} ·{" "}
                  {selected.cookingMinutes} min (estimate)
                </p>
                <button
                  type="button"
                  className="btn-secondary"
                  disabled={busy || spinning}
                  onClick={() => openRecipe(selected.id)}
                >
                  View selected recipe
                </button>
              </>
            ) : spinning ? (
              <p>Choosing from the recipes shown below…</p>
            ) : recipes.length ? (
              <p>
                {recipes.length} {recipes.length === 1 ? "recipe" : "recipes"}{" "}
                from your current results ready to spin.
              </p>
            ) : (
              <p>
                Generate recipes above to fill the wheel with the same recipes
                shown below.
              </p>
            )}
          </div>
          {recipes.length > 0 && (
            <details className="mt-4">
              <summary>Recipes on the wheel ({recipes.length})</summary>
              <ul className="list-disc pl-5">
                {recipes.map((item) => (
                  <li key={item.id}>{item.title}</li>
                ))}
              </ul>
            </details>
          )}
        </div>
      </div>
    </section>
  );
}
