import { useState } from "react";
import { useOutletContext } from "react-router-dom";
import Empty from "../components/Empty";
import FieldError from "../components/FieldError";
import Icon from "../components/Icon";
import { nameError } from "../utils/forms";
import {
  countBadge,
  inlineForm,
  inlineSubmit,
  itemList,
  itemRow,
  itemSymbol,
  removeButton,
  sectionHeading,
  sectionTitle,
} from "../components/listStyles";

function Shopping({ items, run, api }) {
  const [name, setName] = useState(""),
    [error, setError] = useState("");
  return (
    <section className="panel">
      <div className={sectionHeading}>
        <div>
          <h2 className={sectionTitle}>A little list for later.</h2>
          <p className="mb-0 text-[0.85rem]">
            Add what you need. Keep what you have in mind.
          </p>
        </div>
        <span className={countBadge}>
          {items.length} {items.length === 1 ? "item" : "items"}
        </span>
      </div>
      <form
        className={inlineForm}
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
        <div className="min-w-0 flex-1 mobile:basis-full">
          <label htmlFor="shopping-name" className="text-[0.8rem]">
            Add a shopping item
          </label>
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
            className="text-[0.9rem]"
            aria-invalid={!!error}
            aria-describedby={error ? "shopping-name-error" : undefined}
          />
          <FieldError id="shopping-name-error">{error}</FieldError>
        </div>
        <button type="submit" className={inlineSubmit}>
          <Icon name="plus" className="w-[18px]" />
          Add item
        </button>
      </form>
      {!items.length ? (
        <Empty icon="bag" title="All set for now">
          Add an item here, or add missing ingredients from a recipe.
        </Empty>
      ) : (
        <ul className={itemList}>
          {items.map((item) => (
            <li key={item.id} className={itemRow}>
              <span className={itemSymbol}>
                <Icon name="bag" />
              </span>
              <strong className="block min-w-0 flex-1 text-[0.95rem] font-[550] wrap-anywhere">
                {item.name}
              </strong>
              <button
                className={removeButton}
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
      <p className="muted mx-0 mt-[25px] mb-0 text-[0.8rem]">
        Removing a shopping item does not add it to your fridge.
      </p>
    </section>
  );
}

export default function ShoppingPage() {
  const { data, api, run } = useOutletContext();
  return <Shopping items={data.shopping} api={api} run={run} />;
}
