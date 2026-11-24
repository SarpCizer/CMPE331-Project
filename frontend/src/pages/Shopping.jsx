import { useState } from "react";
import { useOutletContext } from "react-router-dom";
import Empty from "../components/Empty";
import FieldError from "../components/FieldError";
import Icon from "../components/Icon";
import { nameError } from "../utils/forms";

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

export default function ShoppingPage() {
  const { data, api, run } = useOutletContext();
  return <Shopping items={data.shopping} api={api} run={run} />;
}
