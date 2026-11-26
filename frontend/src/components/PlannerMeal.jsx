import { useEffect, useState } from 'react';

export default function PlannerMeal({ day, index, meal, label, entry, recipes, busy, save, generate, openRecipe, remove }) {
  const [portions, setPortions] = useState(entry?.servings || 1);
  const [dish, setDish] = useState('');
  const [invalid, setInvalid] = useState('');
  const recipe = entry?.recipe;
  const id = `plan-${index}-${meal}`;
  useEffect(() => { setPortions(entry?.servings || 1); setInvalid(''); }, [entry?.servings, recipe?.id]);
  function valid() {
    const ok = Number.isInteger(Number(portions)) && Number(portions) >= 1 && Number(portions) <= 20;
    setInvalid(ok ? '' : 'Choose a whole number of portions between 1 and 20.');
    return ok;
  }
  return <div className="min-w-0 rounded-xl bg-[#f6f8f3] p-4" aria-label={`${day} ${label}`}>
    <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
      <h4 className="font-semibold">{label}</h4>
      <button type="button" className="btn-text" disabled={busy} aria-label={`Remove dish for ${day} ${label}`} onClick={async () => {
        if (await remove()) { setDish(''); setPortions(1); setInvalid(''); }
      }}>Remove dish</button>
    </div>
    <label htmlFor={`${id}-portions`}>Portions</label>
    <input id={`${id}-portions`} type="number" min="1" max="20" step="1" value={portions} disabled={busy}
      aria-describedby={invalid ? `${id}-error` : undefined} aria-invalid={!!invalid}
      onChange={event => setPortions(event.target.value)} />
    {invalid && <p id={`${id}-error`} className="text-sm text-[#9b2923]" role="alert">{invalid}</p>}
    <label htmlFor={id} className="mt-3">Saved recipe</label>
    <select id={id} className="w-full min-w-0 rounded-lg border border-line bg-white p-2" value={recipe?.id || ''}
      disabled={busy || !recipes.length} onChange={event => {
        if (!event.target.value || valid()) save(index, meal, event.target.value, Number(portions));
      }}>
      <option value="">No meal planned</option>
      {recipes.map(item => <option key={item.id} value={item.id}>{item.title}</option>)}
    </select>
    {recipe && <div className="mt-3">
      <p className="text-sm">Planned: {entry.servings} {entry.servings === 1 ? 'portion' : 'portions'} · {recipe.cookingMinutes} min (estimate)</p>
      {Number(portions) !== entry.servings && <button className="btn-secondary mb-3" type="button" disabled={busy}
        onClick={() => { if (valid()) save(index, meal, recipe.id, Number(portions)); }}>Update portions</button>}
      <details className="text-sm"><summary className="cursor-pointer font-semibold">Ingredients & preparation</summary>
        <p className="mt-3">Amounts below are for the {entry.servings} planned {entry.servings === 1 ? 'portion' : 'portions'}.</p>
        <ul className="my-3 list-disc pl-5">{recipe.ingredients.map((name, i) => <li className="wrap-anywhere" key={i}>{name} · {entry.scaledAmounts[i] || 'Amount needs review'}</li>)}</ul>
        <ol className="my-3 list-decimal pl-5">{recipe.steps.map((step,i) => <li className="mb-2 wrap-anywhere" key={i}>{step}</li>)}</ol>
      </details>
      <button className="btn-text mt-2" type="button" disabled={busy} aria-label={`View recipe for ${day} ${label}`}
        onClick={() => openRecipe(recipe.id)}>View recipe</button>
    </div>}
    <div className="mt-4 border-t border-line pt-3">
      <label htmlFor={`${id}-dish`}>Or request a dish</label>
      <input id={`${id}-dish`} value={dish} maxLength="120" disabled={busy} placeholder="e.g. Tomato sauce pasta"
        onChange={event => setDish(event.target.value)} />
      <button className="btn-secondary mt-2 w-full" type="button" disabled={busy || !dish.trim()}
        aria-label={`Create recipe & plan for ${day} ${label}`} onClick={async () => {
          if (valid() && await generate(index, meal, dish.trim(), Number(portions))) setDish('');
        }}>Create recipe & plan</button>
      <p className="mb-0 mt-2 text-xs">Creates ingredients and preparation for these portions.{recipe ? ' Replaces this meal after the new recipe is ready.' : ''}</p>
    </div>
  </div>;
}
