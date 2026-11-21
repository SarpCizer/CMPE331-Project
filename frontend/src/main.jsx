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
const resourceLabels = {
  inventory: "Ingredients",
  preferences: "Preferences",
  shopping: "Shopping list",
  favorites: "Favorites",
  history: "Recently viewed",
};
const pageResources = {
  fridge: "inventory",
  recipes: "inventory",
  shopping: "shopping",
  preferences: "preferences",
  favorites: "favorites",
  history: "history",
};
const initialResources = (pending = false) =>
  Object.fromEntries(
    Object.keys(paths).map((key) => [key, { pending, error: "" }]),
  );
function FieldError({ id, children }) {
  return children ? (
    <p id={id} className="field-error" role="alert">
      {children}
    </p>
  ) : null;
}
function focusInvalid(form, errors) {
  form.querySelector(`#${Object.keys(errors)[0]}`)?.focus();
}
function nameError(value, label) {
  return value.trim() ? "" : `Enter ${label} before adding it.`;
}
function splitPreferences(value) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}
function preferenceError(values) {
  if (values.length > 100) return "Use at most 100 entries in this field.";
  if (values.some((value) => [...value].length > 128))
    return "Use at most 128 characters per entry.";
  return "";
}
function ResourceError({ label, error, retry, busy }) {
  return (
    <section className="panel resource-error" role="alert">
      <h2>{label} could not be loaded</h2>
      <p>{error} Your saved data has not been replaced.</p>
      <button className="secondary" disabled={busy} onClick={retry}>
        Retry {label.toLowerCase()}
      </button>
    </section>
  );
}
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
function Empty({ icon = "leaf", title, children, headingLevel = 3 }) {
  const Heading = `h${headingLevel}`;
  return (
    <div className="empty">
      <span className="empty-icon">
        <Icon name={icon} width="30" height="30" />
      </span>
      <Heading>{title}</Heading>
      <p>{children}</p>
    </div>
  );
}

function Auth({ onSession, notice }) {
  const [register, setRegister] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(notice || ""),
    [errors, setErrors] = useState({});
  async function submit(event) {
    event.preventDefault();
    if (busy) return;
    setError("");
    const form = event.currentTarget,
      fields = new FormData(form),
      email = fields.get("email").trim(),
      password = fields.get("password");
    const invalid = {};
    if (!email || form.elements.email.validity.typeMismatch)
      invalid.email = "Enter a valid email address.";
    if (!password || (register && [...password].length < 8))
      invalid.password = register
        ? "Use at least 8 characters for your password."
        : "Enter your password.";
    setErrors(invalid);
    if (Object.keys(invalid).length) {
      focusInvalid(form, invalid);
      return;
    }
    setBusy(true);
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
      if (error.status === 409) {
        setErrors({ email: error.message });
        form.elements.email.focus();
      } else
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
      <section className="auth-story" aria-labelledby="auth-story-title">
        <Brand />
        <div className="auth-copy">
          <span className="eyebrow">A LITTLE LESS WASTE</span>
          <h1 id="auth-story-title">
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
            noValidate
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
              disabled={busy}
              aria-invalid={!!errors.email}
              aria-describedby={errors.email ? "email-error" : undefined}
              onChange={() => setErrors((value) => ({ ...value, email: "" }))}
            />
            <FieldError id="email-error">{errors.email}</FieldError>
            <label htmlFor="password">Password</label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete={register ? "new-password" : "current-password"}
              required
              minLength={register ? 8 : 1}
              maxLength="1024"
              disabled={busy}
              aria-invalid={!!errors.password}
              aria-describedby={
                [
                  register && "password-help",
                  errors.password && "password-error",
                ]
                  .filter(Boolean)
                  .join(" ") || undefined
              }
              onChange={() =>
                setErrors((value) => ({ ...value, password: "" }))
              }
            />
            {register && (
              <small id="password-help">Use at least 8 characters.</small>
            )}
            <FieldError id="password-error">{errors.password}</FieldError>
            {error && (
              <p id="auth-error" className="error" role="alert">
                {error}
              </p>
            )}
            <button
              type="submit"
              className="primary auth-submit"
              disabled={busy}
            >
              {busy ? "Please wait…" : register ? "Create account" : "Sign in"}
            </button>
          </form>
          <p className="auth-switch">
            {register ? "Already have an account?" : "New to Fridgely?"}{" "}
            <button
              className="text-button"
              disabled={busy}
              onClick={() => {
                setRegister(!register);
                setError("");
                setErrors({});
              }}
            >
              {register ? "Sign in" : "Create an account"}
            </button>
          </p>
          <p>
            <a href="/api/docs">API documentation</a>
          </p>
        </div>
      </main>
    </div>
  );
}

function Fridge({ items, run, api }) {
  const [name, setName] = useState(""),
    [search, setSearch] = useState(""),
    [error, setError] = useState("");
  async function add(event) {
    event.preventDefault();
    const invalid = nameError(name, "an ingredient");
    setError(invalid);
    if (invalid) {
      event.currentTarget.querySelector("input").focus();
      return;
    }
    if (
      await run(
        () => api("/inventory", { method: "POST", body: { name } }),
        "Ingredient added.",
        ["inventory"],
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
        <form className="inline-form" noValidate onSubmit={add}>
          <div className="grow">
            <label htmlFor="ingredient">Add an ingredient</label>
            <input
              id="ingredient"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                setError("");
              }}
              required
              maxLength="256"
              placeholder="Tomatoes, rice, a little inspiration…"
              aria-invalid={!!error}
              aria-describedby={error ? "ingredient-error" : undefined}
            />
            <FieldError id="ingredient-error">{error}</FieldError>
          </div>
          <button type="submit" className="primary">
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
                      ["inventory"],
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
function RecipeDialog({
  recipe,
  onClose,
  run,
  api,
  favorites,
  busy,
  error,
  notice,
  favoriteState,
  retryFavorites,
}) {
  const dialog = useRef(null);
  const [shoppingAdded, setShoppingAdded] = useState(false);
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
      {error && (
        <div className="message error" role="alert">
          {error}
        </div>
      )}
      {notice && (
        <div className="message success" role="status">
          {notice}
        </div>
      )}
      {busy && <p role="status">Saving your changes…</p>}
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
          disabled={busy}
          onClick={async () => {
            const result = await run(
              () =>
                api(`/recipes/${recipe.id}/shopping-items`, {
                  method: "POST",
                  body: {},
                }),
              "Missing ingredients added to shopping.",
              ["shopping"],
            );
            if (result) setShoppingAdded(true);
          }}
        >
          Add missing ingredients
        </button>
        <button
          className="secondary"
          disabled={busy || favoriteState.pending || !!favoriteState.error}
          onClick={() =>
            run(
              () =>
                api(saved ? `/favorites/${recipe.id}` : "/favorites", {
                  method: saved ? "DELETE" : "POST",
                  ...(saved ? {} : { body: { recipeId: recipe.id } }),
                }),
              saved ? "Favorite removed." : "Recipe saved to favorites.",
              ["favorites"],
            )
          }
        >
          {saved ? "Remove favorite" : "Save favorite"}
        </button>
        {shoppingAdded && (
          <a className="text-link" href="#/shopping" onClick={onClose}>
            View shopping list
          </a>
        )}
      </div>
      {favoriteState.pending && <p role="status">Loading favorites…</p>}
      {favoriteState.error && (
        <ResourceError
          label="Favorites"
          error={favoriteState.error}
          retry={retryFavorites}
          busy={busy}
        />
      )}
    </dialog>
  );
}

function Preferences({ value, run, api }) {
  const [dietary, setDietary] = useState(value.dietary.join(", ")),
    [allergens, setAllergens] = useState(value.allergens.join(", ")),
    [errors, setErrors] = useState({});
  useEffect(() => {
    setDietary(value.dietary.join(", "));
    setAllergens(value.allergens.join(", "));
  }, [value]);
  function submit(event) {
    event.preventDefault();
    const body = {
      dietary: splitPreferences(dietary),
      allergens: splitPreferences(allergens),
    };
    const invalid = Object.fromEntries(
      Object.entries(body)
        .map(([key, values]) => [key, preferenceError(values)])
        .filter(([, message]) => message),
    );
    setErrors(invalid);
    if (Object.keys(invalid).length) {
      focusInvalid(event.currentTarget, invalid);
      return;
    }
    run(
      () => api("/profile/preferences", { method: "PUT", body }),
      "Preferences saved.",
      ["preferences"],
    );
  }
  return (
    <section className="panel preferences">
      <span className="eyebrow">MAKE IT YOURS</span>
      <h2>A kitchen that knows you.</h2>
      <p>Your saved preferences are included whenever you ask for recipes.</p>
      <form noValidate onSubmit={submit}>
        <label htmlFor="dietary">Dietary preferences</label>
        <input
          id="dietary"
          value={dietary}
          onChange={(e) => {
            setDietary(e.target.value);
            setErrors((value) => ({ ...value, dietary: "" }));
          }}
          placeholder="Vegetarian, vegan…"
          aria-invalid={!!errors.dietary}
          aria-describedby={`dietary-help${errors.dietary ? " dietary-error" : ""}`}
        />
        <small id="dietary-help">Separate preferences with commas.</small>
        <FieldError id="dietary-error">{errors.dietary}</FieldError>
        <label htmlFor="allergens">Ingredients to exclude</label>
        <input
          id="allergens"
          value={allergens}
          onChange={(e) => {
            setAllergens(e.target.value);
            setErrors((value) => ({ ...value, allergens: "" }));
          }}
          placeholder="Peanut, sesame…"
          aria-invalid={!!errors.allergens}
          aria-describedby={`allergens-help${errors.allergens ? " allergens-error" : ""}`}
        />
        <small id="allergens-help">
          Use ingredient names, separated by commas. Review recipe ingredients
          before cooking.
        </small>
        <FieldError id="allergens-error">{errors.allergens}</FieldError>
        <button type="submit" className="primary">
          Save preferences
        </button>
        <p className="muted">
          Clear either field and save to remove its saved entries.
        </p>
      </form>
    </section>
  );
}

function Shopping({ items, run, api }) {
  const [name, setName] = useState(""),
    [error, setError] = useState("");
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
        noValidate
        onSubmit={async (event) => {
          event.preventDefault();
          const invalid = nameError(name, "a shopping item");
          setError(invalid);
          if (invalid) {
            event.currentTarget.querySelector("input").focus();
            return;
          }
          if (
            await run(
              () => api("/shopping-items", { method: "POST", body: { name } }),
              "Shopping item added.",
              ["shopping"],
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
            onChange={(e) => {
              setName(e.target.value);
              setError("");
            }}
            required
            maxLength="256"
            placeholder="What do you need?"
            aria-invalid={!!error}
            aria-describedby={error ? "shopping-name-error" : undefined}
          />
          <FieldError id="shopping-name-error">{error}</FieldError>
        </div>
        <button type="submit" className="primary">
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
                    ["shopping"],
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
    [resources, setResources] = useState(() => initialResources(!!session)),
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
      setError("");
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
    setResources(initialResources());
    setError("");
    setNotice(message);
  }
  function signIn(value) {
    clearSession();
    sessionStorage.setItem("fridgely.session", JSON.stringify(value));
    setSession(value);
    setResources(initialResources(true));
    setNotice("");
  }
  async function loadResources(request, keys, version = generation.current) {
    setResources((value) => ({
      ...value,
      ...Object.fromEntries(
        keys.map((key) => [key, { pending: true, error: "" }]),
      ),
    }));
    const results = await Promise.all(
      keys.map(async (key) => {
        try {
          const result = await request(paths[key]);
          if (version !== generation.current) return false;
          setData((value) => ({ ...value, [key]: result }));
          setResources((value) => ({
            ...value,
            [key]: { pending: false, error: "" },
          }));
          return true;
        } catch (error) {
          if (version !== generation.current || error.name === "AbortError")
            return false;
          if (error.status === 401)
            clearSession("Your session ended. Please sign in again.");
          else
            setResources((value) => ({
              ...value,
              [key]: { pending: false, error: error.message },
            }));
          return false;
        }
      }),
    );
    return results.every(Boolean);
  }
  useEffect(() => {
    if (!session) return;
    const version = generation.current,
      request = createApi(session.token, controller.current.signal);
    void loadResources(request, Object.keys(paths), version);
  }, [session]);
  async function run(operation, message, refresh = []) {
    if (busyRef.current) return false;
    const version = generation.current;
    busyRef.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const result = await operation();
      if (version !== generation.current) return false;
      const refreshed = await loadResources(api, refresh, version);
      if (version !== generation.current) return false;
      if (message)
        setNotice(
          refreshed
            ? message
            : `${message} Some saved data could not be refreshed. Use Retry to load it again.`,
        );
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
    const recipe = await run(() => api(`/recipes/${id}`), "", ["history"]);
    if (recipe && typeof recipe === "object") setSelected(recipe);
  }
  if (!session) return <Auth key={notice} onSession={signIn} notice={notice} />;
  const section = sections.find((s) => s[0] === page);
  const resource = pageResources[page],
    state = resources[resource],
    loading = state.pending;
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
        {error && !selected && (
          <div className="message error" role="alert">
            {error}
            <button
              className="text-button"
              disabled={busy}
              onClick={() =>
                run(async () => true, "Data refreshed.", Object.keys(paths))
              }
            >
              Refresh data
            </button>
          </div>
        )}
        {notice && !selected && (
          <div className="message success" role="status">
            {notice}
          </div>
        )}
        {loading ? (
          <div className="loading" role="status">
            Loading {resourceLabels[resource].toLowerCase()}…
          </div>
        ) : state.error ? (
          <ResourceError
            label={resourceLabels[resource]}
            error={state.error}
            retry={() => loadResources(api, [resource])}
            busy={busy}
          />
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
              ))}
            {page === "history" &&
              (!data.history.length ? (
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
              ))}
          </fieldset>
        )}
        <footer className="page-footer">
          <Brand />
          <span>A little less waste. A lot more possibility.</span>
          <a href="/api/docs">API documentation</a>
        </footer>
      </main>
      {selected && (
        <RecipeDialog
          recipe={selected}
          favorites={data.favorites}
          favoriteState={resources.favorites}
          retryFavorites={() => loadResources(api, ["favorites"])}
          busy={busy}
          error={error}
          notice={notice}
          onClose={() => setSelected(null)}
          run={run}
          api={api}
        />
      )}
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
