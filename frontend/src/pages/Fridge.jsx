import { useState } from "react";
import { Link, useOutletContext } from "react-router-dom";
import Empty from "../components/Empty";
import FieldError from "../components/FieldError";
import Icon from "../components/Icon";
import ProduceArt from "../components/ProduceArt";
import { nameError } from "../utils/forms";

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
          <Link className="primary link-button" to="/recipes">
            Find a recipe
          </Link>
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

export default function FridgePage() {
  const { data, api, run } = useOutletContext();
  return <Fridge items={data.inventory} api={api} run={run} />;
}
