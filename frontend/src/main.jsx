import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { createApi } from "./api";
import "./styles.css";

const initialData = () => ({
  inventory: [],
  preferences: { dietary: [], allergens: [] },
  shopping: [],
  favorites: [],
  history: [],
});
const sections = [
  ["fridge", "My fridge", "fridge"],
  ["recipes", "Find recipes", "leaf"],
  ["shopping", "Shopping list", "bag"],
  ["favorites", "Favorites", "heart"],
  ["history", "Recently viewed", "clock"],
  ["preferences", "Preferences", "settings"],
];
const paths = {
  inventory: "/inventory",
  preferences: "/profile/preferences",
  shopping: "/shopping-items",
  favorites: "/favorites",
  history: "/history",
};
function savedSession() {
  try {
    const value = JSON.parse(sessionStorage.getItem("fridgely.session"));
    return typeof value?.token === "string" && typeof value?.email === "string"
      ? value
      : null;
  } catch {
    return null;
  }
}
function currentPage() {
  const value = location.hash.slice(2);
  return sections.some((s) => s[0] === value) ? value : "fridge";
}

function Icon({ name = "leaf", ...props }) {
  const drawings = {
    leaf: (
      <>
        <path d="M20 4c-7-1-14 2-14 8a6 6 0 0 0 6 6c6 0 9-7 8-14Z" />
        <path d="m4 21 11-11" />
      </>
    ),
    fridge: (
      <>
        <rect x="6" y="2" width="12" height="20" rx="2" />
        <path d="M6 10h12M9 6v1m0 7v3" />
      </>
    ),
    bag: (
      <>
        <path d="M5 8h14l1 13H4L5 8Z" />
        <path d="M8 8V6a4 4 0 0 1 8 0v2" />
      </>
    ),
    heart: (
      <path d="M20 5c-3-3-6-1-8 1-2-2-5-4-8-1-5 5 3 11 8 15 5-4 13-10 8-15Z" />
    ),
    clock: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 6v6l4 2" />
      </>
    ),
    settings: (
      <>
        <path d="M4 6h16M4 12h16M4 18h16" />
        <circle cx="8" cy="6" r="2" />
        <circle cx="16" cy="12" r="2" />
        <circle cx="10" cy="18" r="2" />
      </>
    ),
    plus: <path d="M12 5v14M5 12h14" />,
    close: <path d="m6 6 12 12M6 18 18 6" />,
  };
  return (
    <svg
      width="22"
      height="22"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    >
      {drawings[name] || drawings.leaf}
    </svg>
  );
}
function Brand() {
  return (
    <div className="brand">
      <span className="brand-mark">
        <Icon />
      </span>
      fridgely<span className="brand-dot">.</span>
    </div>
  );
}
function ProduceArt() {
  return (
    <svg className="produce-art" viewBox="0 0 230 180" aria-hidden="true">
      <ellipse cx="123" cy="163" rx="83" ry="8" fill="#d2e2d4" />
      <path d="M153 80c-30-30-10-57 28-65 9 35 3 61-28 65" fill="#6e986b" />
      <path d="M153 80c-12-27-49-34-68-17 19 30 43 38 68 17" fill="#3f7656" />
      <path d="m153 133 7-72" stroke="#245d40" strokeWidth="5" />
      <path
        d="M66 78c-28-11-43 13-39 40 4 31 30 44 51 37 18 9 43-4 47-32 5-31-15-56-42-45-7-2-11-2-17 0"
        fill="#ce6549"
      />
      <path d="m72 84-16-11 18 2 9-16 3 16 16 1-17 9" fill="#416e44" />
      <path
        d="M166 106c-31-3-39 13-33 31 8 24 33 29 53 17 21-13 12-43-20-48"
        fill="#e6b761"
      />
      <path d="m159 112 4-18" stroke="#3f7656" strokeWidth="4" />
      <path
        d="M40 105c-2 8-1 15 2 20"
        stroke="#e39176"
        strokeWidth="5"
        strokeLinecap="round"
      />
    </svg>
  );
}
function Empty({ icon = "leaf", title, children }) {
  return (
    <div className="empty">
      <span className="empty-icon">
        <Icon name={icon} width="30" height="30" />
      </span>
      <h3>{title}</h3>
      <p>{children}</p>
    </div>
  );
}

function Auth({ onSession, notice }) {
  const [register, setRegister] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(notice || "");
  async function submit(event) {
    event.preventDefault();
    setError("");
    setBusy(true);
    const fields = new FormData(event.currentTarget),
      email = fields.get("email").trim(),
      password = fields.get("password");
    try {
      const api = createApi();
      if (register)
        await api("/accounts", { method: "POST", body: { email, password } });
      const result = await api("/sessions", {
        method: "POST",
        body: { email, password },
      });
      onSession({ email: email.toLowerCase(), token: result.token });
    } catch (error) {
      setError(
        error.status === 401
          ? "Email or password is incorrect. Please try again."
          : error.message,
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="auth-layout">
      <section className="auth-story">
        <Brand />
        <div className="auth-copy">
          <span className="eyebrow">A LITTLE LESS WASTE</span>
          <h1>
            Good things
            <br />
            start in
            <br />
            <em>your fridge.</em>
          </h1>
          <p>
            Make room for better meals. Keep track of what you have and find a
            little inspiration for what comes next.
          </p>
          <ProduceArt />
        </div>
        <span className="auth-footer">
          A thoughtful kitchen, one ingredient at a time.
        </span>
      </section>
      <main className="auth-main">
        <div className="auth-card">
          <span className="eyebrow">YOUR KITCHEN COMPANION</span>
          <h2>{register ? "A fresh start." : "Welcome back."}</h2>
          <p>
            {register
              ? "Create an account and make the most of what you have."
              : "Sign in to your own little corner of the kitchen."}
          </p>
          <form
            onSubmit={submit}
            aria-describedby={error ? "auth-error" : undefined}
          >
            <label htmlFor="email">Email address</label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              maxLength="254"
              placeholder="you@example.com"
            />
            <label htmlFor="password">Password</label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete={register ? "new-password" : "current-password"}
              required
              minLength={register ? 8 : 1}
              maxLength="1024"
              aria-describedby={register ? "password-help" : undefined}
            />
            {register && (
              <small id="password-help">Use at least 8 characters.</small>
            )}
            {error && (
              <p id="auth-error" className="error" role="alert">
                {error}
              </p>
            )}
            <button type="submit" className="primary auth-submit" disabled={busy}>
              {busy ? "Please wait…" : register ? "Create account" : "Sign in"}
            </button>
          </form>
          <p className="auth-switch">
            {register ? "Already have an account?" : "New to Fridgely?"}{" "}
            <button
              className="text-button"
              onClick={() => {
                setRegister(!register);
                setError("");
              }}
            >
              {register ? "Sign in" : "Create an account"}
            </button>
          </p>
        </div>
      </main>
    </div>
  );
}

function Fridge({ items, run, api }) {
  const [name, setName] = useState(""),
    [search, setSearch] = useState("");
  async function add(event) {
    event.preventDefault();
    if (
      await run(
        () => api("/inventory", { method: "POST", body: { name } }),
        "Ingredient added.",
      )
    )
      setName("");
  }
  const visible = items.filter((item) =>
    item.name.toLocaleLowerCase().includes(search.toLocaleLowerCase()),
  );
  return (
    <>
      <section className="hero">
        <div>
          <span className="eyebrow">A KITCHEN FULL OF POSSIBILITIES</span>
          <h2>
            Use what you have.
            <br />
            <em>Love what you make.</em>
          </h2>
          <p>Your next good meal might already be in the fridge.</p>
          <a className="primary link-button" href="#/recipes">
            Find a recipe
          </a>
        </div>
        <ProduceArt />
      </section>
      <div className="stat-row">
        <div>
          <Icon name="fridge" />
          <strong>{items.length}</strong>
          <span>
            {items.length === 1 ? "ingredient" : "ingredients"} in your fridge
          </span>
        </div>
        <div>
          <Icon name="leaf" />
          <span>
            Less forgotten food.
            <br />
            <strong className="small-strong">
              More everyday possibilities.
            </strong>
          </span>
        </div>
      </div>
      <section className="panel">
        <div className="section-heading">
          <div>
            <h2>Your ingredients</h2>
            <p>A small list with a lot of potential.</p>
          </div>
          <span className="count">
            {items.length} {items.length === 1 ? "item" : "items"}
          </span>
        </div>
        <form className="inline-form" onSubmit={add}>
          <div className="grow">
            <label htmlFor="ingredient">Add an ingredient</label>
            <input
              id="ingredient"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              maxLength="256"
              placeholder="Tomatoes, rice, a little inspiration…"
            />
          </div>
          <button type="submit" className="primary" disabled={!name.trim()}>
            <Icon name="plus" />
            Add ingredient
          </button>
        </form>
        {items.length > 0 && (
          <div className="search-field">
            <label htmlFor="search">Search your fridge</label>
            <input
              id="search"
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Find an ingredient"
            />
          </div>
        )}
        {!visible.length ? (
          <Empty
            icon="fridge"
            title={items.length ? "No matching ingredients" : "A fresh canvas"}
          >
            {items.length
              ? "Try a different search."
              : "Add your first ingredient to start finding meals."}
          </Empty>
        ) : (
          <ul className="ingredient-list">
            {visible.map((item) => (
              <li key={item.id}>
                <span className="ingredient-symbol">
                  <Icon name="leaf" />
                </span>
                <div className="grow">
                  <strong>{item.name}</strong>
                  <span>
                    Added{" "}
                    {new Intl.DateTimeFormat("en", {
                      dateStyle: "medium",
                    }).format(new Date(item.addedAt))}
                  </span>
                </div>
                <button
                  className="quiet"
                  aria-label={`Remove ${item.name}`}
                  onClick={() =>
                    run(
                      () => api(`/inventory/${item.id}`, { method: "DELETE" }),
                      "Ingredient removed.",
                    )
                  }
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  );
}

function RecipeCard({ recipe, onOpen }) {
  return (
    <article className="recipe-card">
      <div className="recipe-art">
        <Icon name="leaf" width="46" height="46" />
        <span>MADE FOR YOUR KITCHEN</span>
      </div>
      <div className="recipe-content">
        <h3>{recipe.title}</h3>
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
function RecipeDialog({ recipe, onClose, run, api, favorites }) {
  const dialog = useRef(null);
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
          onClick={() =>
            run(
              () =>
                api(`/recipes/${recipe.id}/shopping-items`, {
                  method: "POST",
                  body: {},
                }),
              "Missing ingredients added to shopping.",
            )
          }
        >
          Add missing ingredients
        </button>
        <button
          className="secondary"
          onClick={() =>
            run(
              () =>
                api(saved ? `/favorites/${recipe.id}` : "/favorites", {
                  method: saved ? "DELETE" : "POST",
                  ...(saved ? {} : { body: { recipeId: recipe.id } }),
                }),
              saved ? "Favorite removed." : "Recipe saved to favorites.",
            )
          }
        >
          {saved ? "Remove favorite" : "Save favorite"}
        </button>
      </div>
    </dialog>
  );
}

function Preferences({ value, run, api }) {
  const [dietary, setDietary] = useState(value.dietary.join(", ")),
    [allergens, setAllergens] = useState(value.allergens.join(", "));
  useEffect(() => {
    setDietary(value.dietary.join(", "));
    setAllergens(value.allergens.join(", "));
  }, [value]);
  const split = (value) =>
    value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  return (
    <section className="panel preferences">
      <span className="eyebrow">MAKE IT YOURS</span>
      <h2>A kitchen that knows you.</h2>
      <p>Your saved preferences are included whenever you ask for recipes.</p>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          run(
            () =>
              api("/profile/preferences", {
                method: "PUT",
                body: { dietary: split(dietary), allergens: split(allergens) },
              }),
            "Preferences saved.",
          );
        }}
      >
        <label htmlFor="dietary">Dietary preferences</label>
        <input
          id="dietary"
          value={dietary}
          onChange={(e) => setDietary(e.target.value)}
          placeholder="Vegetarian, vegan…"
          aria-describedby="dietary-help"
        />
        <small id="dietary-help">Separate preferences with commas.</small>
        <label htmlFor="allergens">Ingredients to exclude</label>
        <input
          id="allergens"
          value={allergens}
          onChange={(e) => setAllergens(e.target.value)}
          placeholder="Peanut, sesame…"
          aria-describedby="allergens-help"
        />
        <small id="allergens-help">
          Use ingredient names, separated by commas. Review recipe ingredients
          before cooking.
        </small>
        <button type="submit" className="primary">Save preferences</button>
        <p className="muted">
          Clear either field and save to remove its saved entries.
        </p>
      </form>
    </section>
  );
}

function Shopping({ items, run, api }) {
  const [name, setName] = useState("");
  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <h2>A little list for later.</h2>
          <p>Add what you need. Keep what you have in mind.</p>
        </div>
        <span className="count">
          {items.length} {items.length === 1 ? "item" : "items"}
        </span>
      </div>
      <form
        className="inline-form"
        onSubmit={async (event) => {
          event.preventDefault();
          if (
            await run(
              () => api("/shopping-items", { method: "POST", body: { name } }),
              "Shopping item added.",
            )
          )
            setName("");
        }}
      >
        <div className="grow">
          <label htmlFor="shopping-name">Add a shopping item</label>
          <input
            id="shopping-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            maxLength="256"
            placeholder="What do you need?"
          />
        </div>
        <button type="submit" className="primary" disabled={!name.trim()}>
          <Icon name="plus" />
          Add item
        </button>
      </form>
      {!items.length ? (
        <Empty icon="bag" title="All set for now">
          Add an item here, or add missing ingredients from a recipe.
        </Empty>
      ) : (
        <ul className="ingredient-list">
          {items.map((item) => (
            <li key={item.id}>
              <span className="ingredient-symbol">
                <Icon name="bag" />
              </span>
              <strong className="grow">{item.name}</strong>
              <button
                className="quiet"
                aria-label={`Remove ${item.name}`}
                onClick={() =>
                  run(
                    () =>
                      api(`/shopping-items/${item.id}`, { method: "DELETE" }),
                    "Shopping item removed.",
                  )
                }
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}
      <p className="muted list-note">
        Removing a shopping item does not add it to your fridge.
      </p>
    </section>
  );
}

function App() {
  const [session, setSession] = useState(savedSession),
    [data, setData] = useState(initialData),
    [page, setPage] = useState(currentPage),
    [generated, setGenerated] = useState([]),
    [selected, setSelected] = useState(null),
    [busy, setBusy] = useState(false),
    [loading, setLoading] = useState(!!session),
    [error, setError] = useState(""),
    [notice, setNotice] = useState("");
  const generation = useRef(0),
    controller = useRef(new AbortController()),
    busyRef = useRef(false);
  const api = createApi(session?.token, controller.current.signal);
  useEffect(() => {
    const change = () => {
      setPage(currentPage());
      setNotice("");
    };
    window.addEventListener("hashchange", change);
    return () => window.removeEventListener("hashchange", change);
  }, []);
  function clearSession(message = "") {
    generation.current++;
    controller.current.abort();
    controller.current = new AbortController();
    busyRef.current = false;
    sessionStorage.removeItem("fridgely.session");
    setSession(null);
    setData(initialData());
    setGenerated([]);
    setSelected(null);
    setBusy(false);
    setLoading(false);
    setError("");
    setNotice(message);
  }
  function signIn(value) {
    clearSession();
    sessionStorage.setItem("fridgely.session", JSON.stringify(value));
    setSession(value);
    setLoading(true);
    setNotice("");
  }
  async function readState(request) {
    const entries = await Promise.all(
      Object.entries(paths).map(async ([key, path]) => [
        key,
        await request(path),
      ]),
    );
    return Object.fromEntries(entries);
  }
  useEffect(() => {
    if (!session) return;
    const version = generation.current,
      request = createApi(session.token, controller.current.signal);
    setLoading(true);
    readState(request)
      .then((value) => {
        if (version === generation.current) {
          setData(value);
          setError("");
        }
      })
      .catch((error) => {
        if (version !== generation.current || error.name === "AbortError")
          return;
        if (error.status === 401)
          clearSession("Your session ended. Please sign in again.");
        else setError(error.message);
      })
      .finally(() => {
        if (version === generation.current) setLoading(false);
      });
  }, [session]);
  async function run(operation, message) {
    if (busyRef.current) return false;
    const version = generation.current;
    busyRef.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const result = await operation();
      const fresh = await readState(api);
      if (version !== generation.current) return false;
      setData(fresh);
      if (message) setNotice(message);
      return result ?? true;
    } catch (error) {
      if (version !== generation.current || error.name === "AbortError")
        return false;
      if (error.status === 401)
        clearSession("Your session ended. Please sign in again.");
      else setError(error.message);
      return false;
    } finally {
      if (version === generation.current) {
        busyRef.current = false;
        setBusy(false);
      }
    }
  }
  async function openRecipe(id) {
    const recipe = await run(() => api(`/recipes/${id}`));
    if (recipe && typeof recipe === "object") setSelected(recipe);
  }
  if (!session) return <Auth key={notice} onSession={signIn} notice={notice} />;
  const section = sections.find((s) => s[0] === page);
  return (
    <div className="app-layout">
      <a
        className="skip-link"
        href="#main-content"
        onClick={(event) => {
          event.preventDefault();
          document.getElementById("main-content").focus();
        }}
      >
        Skip to content
      </a>
      <aside className="sidebar">
        <Brand />
        <div className="nav-caption">YOUR KITCHEN</div>
        <nav aria-label="Main navigation">
          {sections.map(([key, label, icon]) => (
            <a
              href={`#/${key}`}
              key={key}
              className={page === key ? "active" : ""}
              aria-current={page === key ? "page" : undefined}
            >
              <Icon name={icon} />
              {label}
              {key === "fridge" && (
                <span className="nav-count" aria-hidden="true">
                  {data.inventory.length}
                </span>
              )}
            </a>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <span className="avatar">{session.email[0].toUpperCase()}</span>
          <div className="account">
            <span title={session.email}>{session.email}</span>
            <button onClick={() => clearSession()}>Sign out</button>
          </div>
        </div>
      </aside>
      <main
        id="main-content"
        tabIndex="-1"
        className="main"
        aria-busy={busy || loading}
      >
        <header className="page-header">
          <div>
            <span className="eyebrow">LESS WASTE. MORE TASTE.</span>
            <h1>{section[1]}</h1>
          </div>
          <span className="header-note">
            <Icon />A little better, every day.
          </span>
        </header>
        {error && (
          <div className="message error" role="alert">
            {error}
            <button
              className="text-button"
              onClick={() => run(async () => true, "Data refreshed.")}
            >
              Refresh data
            </button>
          </div>
        )}
        {notice && (
          <div className="message success" role="status">
            {notice}
          </div>
        )}
        {loading ? (
          <div className="loading" role="status">
            Opening your kitchen…
          </div>
        ) : (
          <fieldset
            className="content-fieldset"
            aria-label="Kitchen actions"
            disabled={busy}
          >
            {page === "fridge" && (
              <Fridge items={data.inventory} api={api} run={run} />
            )}
            {page === "preferences" && (
              <Preferences value={data.preferences} api={api} run={run} />
            )}
            {page === "shopping" && (
              <Shopping items={data.shopping} api={api} run={run} />
            )}
            {page === "recipes" && (
              <>
                <section className="recipe-intro panel">
                  <span className="eyebrow">A LITTLE INSPIRATION</span>
                  <h2>Something good is already here.</h2>
                  <p>
                    Turn the {data.inventory.length} ingredients in your fridge
                    into your next meal, with your saved preferences included.
                  </p>
                  <button
                    className="primary"
                    disabled={!data.inventory.length}
                    onClick={async () => {
                      const result = await run(
                        () =>
                          api("/recipes/generate", {
                            method: "POST",
                            body: {},
                          }),
                        "Recipes are ready.",
                      );
                      if (Array.isArray(result)) setGenerated(result);
                    }}
                  >
                    <Icon />
                    {busy ? "Finding inspiration…" : "Generate recipes"}
                  </button>
                  <a className="text-link" href="#/preferences">
                    Edit your preferences
                  </a>
                </section>
                {!data.inventory.length ? (
                  <Empty icon="fridge" title="Start with an ingredient">
                    Add something to your fridge before asking for recipes.
                  </Empty>
                ) : !generated.length ? (
                  <Empty title="Your next meal starts here">
                    Generate a few ideas from the ingredients you already have.
                  </Empty>
                ) : (
                  <div className="recipe-grid">
                    {generated.map((recipe) => (
                      <RecipeCard
                        recipe={recipe}
                        key={recipe.id}
                        onOpen={openRecipe}
                      />
                    ))}
                  </div>
                )}
              </>
            )}
            {page === "favorites" &&
              (!data.favorites.length ? (
                <Empty icon="heart" title="Keep the good ones close">
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
              ))}
            {page === "history" &&
              (!data.history.length ? (
                <Empty icon="clock" title="A little trip down memory lane">
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
              ))}
          </fieldset>
        )}
        <footer className="page-footer">
          <Brand />
          <span>A little less waste. A lot more possibility.</span>
        </footer>
      </main>
      {selected && (
        <RecipeDialog
          recipe={selected}
          favorites={data.favorites}
          onClose={() => setSelected(null)}
          run={run}
          api={api}
        />
      )}
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
