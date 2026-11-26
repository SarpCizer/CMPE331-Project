import { useEffect, useRef, useState } from 'react';
import { Link, useOutletContext } from 'react-router-dom';
import Icon from '../components/Icon';
import PlannerMeal from '../components/PlannerMeal';

const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const meals = [['breakfast','Breakfast'], ['lunch','Lunch'], ['dinner','Main meal'], ['dessert','Dessert']];
function monday(value) {
  const date = new Date(`${value}T12:00:00Z`);
  date.setUTCDate(date.getUTCDate() - (date.getUTCDay() + 6) % 7);
  return date.toISOString().slice(0, 10);
}
function currentWeek() {
  const now = new Date();
  return monday(`${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`);
}
function shift(value, amount) {
  const date = new Date(`${value}T12:00:00Z`);
  date.setUTCDate(date.getUTCDate() + amount);
  return date.toISOString().slice(0,10);
}

export default function WeeklyPlan() {
  const { data, generated, session, api, run, busy, openRecipe, clearSession } = useOutletContext();
  const [week, setWeek] = useState(currentWeek);
  const [plan, setPlan] = useState({ entries: [] });
  const [catalog, setCatalog] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  const [result, setResult] = useState(null);
  const current = useRef(week);
  current.current = week;
  useEffect(() => {
    let active = true;
    setLoading(true); setError(''); setResult(null);
    Promise.all([api(`/weekly-plan?weekStart=${week}`), api('/weekly-plan/recipes')]).then(([value, saved]) => {
      if (active) { setPlan(value); setCatalog(saved); }
    }).catch(failure => { if (active) {
      if (failure.status === 401) clearSession('Your session ended. Please sign in again.');
      else setError(failure.message);
    } })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [week, retry, session.token]);
  const recipes = [...new Map([...catalog, ...data.favorites, ...data.history.map(item => item.recipe),
    ...generated, ...plan.entries.map(entry => entry.recipe)].map(recipe => [recipe.id, recipe])).values()];

  async function save(day, meal, recipeId, servings) {
    const requested = week;
    const value = await run(() => recipeId
      ? api(`/weekly-plan/${day}/${meal}`, { method: 'PUT', body: { weekStart: requested, recipeId, servings } })
      : api(`/weekly-plan/${day}/${meal}?weekStart=${requested}`, { method: 'DELETE' }),
    recipeId ? 'Meal saved to your week.' : 'Meal removed from your week.');
    if (value && current.current === requested) { setPlan(value); setResult(null); }
  }
  async function generate(day, meal, dish, servings) {
    const requested = week;
    const value = await run(async () => {
      try { return await api(`/weekly-plan/${day}/${meal}/generate`, {
        method: 'POST', body: { weekStart: requested, dish, servings } }); }
      catch (failure) {
        if (failure.status === 409) setRetry(value => value + 1);
        throw failure;
      }
    }, 'Recipe created and saved to your week.');
    if (value && current.current === requested) {
      setPlan(value); setResult(null);
      setCatalog(items => [...new Map([...items,...value.entries.map(item => item.recipe)].map(item => [item.id,item])).values()]);
    }
    return !!value;
  }
  return <section className="panel">
    <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
      <div><h2>A week of good food.</h2><p className="mb-0 text-sm">Choose a saved recipe or request a dish. Set portions separately for every meal, including a main meal and dessert on the same day.</p></div>
      <span className="rounded-lg bg-[#e8f0e7] px-3 py-2 text-sm text-green">{loading ? 'Loading…' : `${plan.entries.length} planned ${plan.entries.length === 1 ? 'meal' : 'meals'}`}</span>
    </div>
    <div className="mb-5 flex flex-wrap items-end gap-3">
      <button type="button" className="btn-secondary" disabled={busy} onClick={() => setWeek(shift(week,-7))}>Previous week</button>
      <div><label htmlFor="plan-week">Week containing</label><input id="plan-week" type="date" value={week} disabled={busy}
        onChange={event => { if (event.target.value) setWeek(monday(event.target.value)); }} /></div>
      <button type="button" className="btn-secondary" disabled={busy} onClick={() => setWeek(shift(week,7))}>Next week</button>
    </div>
    <p className="text-sm text-[#536958]">Week beginning {week}. Choose any date to open its Monday–Sunday week. Planning never reserves or deducts fridge ingredients.</p>
    {loading ? <p role="status">Loading weekly plan…</p> : error ? <div className="alert-error" role="alert">{error}
      <button className="btn-text" type="button" onClick={() => setRetry(value => value + 1)}>Retry weekly plan</button></div> : <>
      {!recipes.length && <p className="rounded-xl bg-[#f0f3ee] p-4">Type a dish below to create its recipe, or <Link to="/recipes">find recipes</Link> to build your saved collection.</p>}
      <div className="grid gap-5">
        {days.map((day, index) => <section key={day} aria-label={`${day} meal plan`} className="rounded-2xl border border-line p-4">
          <h3 className="mb-4 flex items-center gap-2"><Icon name="calendar" />{day}</h3>
          <div className="grid grid-cols-2 gap-4 mobile:grid-cols-1 tablet:grid-cols-1">
            {meals.map(([meal,label]) => {
              const entry = plan.entries.find(item => item.day === index && item.meal === meal);
              return <PlannerMeal key={`${week}-${meal}`} day={day} index={index} meal={meal} label={label} entry={entry}
                recipes={recipes} busy={busy} save={save} generate={generate} openRecipe={openRecipe} />;
            })}
          </div>
        </section>)}
      </div>
      <div className="mt-6 rounded-xl bg-[#e8f0e7] p-4">
        <h3>One list for the whole week.</h3>
        <p className="text-sm">We scale each dish to its planned portions, total the week, then subtract your current fridge stock once. Missing quantities are added to your existing shopping list; larger amounts already there are kept. Whole items are rounded up after totaling the week.</p>
        <button className="btn-primary mobile:w-full" type="button" disabled={busy || !plan.entries.length} onClick={async () => {
          const requested = week;
          const value = await run(() => api('/weekly-plan/shopping-items', { method: 'POST', body: { weekStart: requested } }),
            'Weekly shopping list updated.', ['shopping']);
          if (value && current.current === requested) setResult(value);
        }}>Generate weekly shopping list</button>
        {result && <div className="mt-4"><p>{result.plannedMeals} planned meals checked. <Link to="/shopping">View shopping list</Link></p>
          {result.needsReview.length > 0 && <p className="rounded-lg border border-[#d9b98e] bg-[#fff6e8] p-3 text-[#6b4318]" role="status">Amounts need review: {result.needsReview.join(', ')}. Some recipe or stock measurements could not be compared. Check these quantities before buying.</p>}
        </div>}
      </div>
    </>}
  </section>;
}
