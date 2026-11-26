import { useState } from "react";
import { useOutletContext } from "react-router-dom";
import ShoppingAmount, { amountInput } from "../components/ShoppingAmount";
import PurchaseItem from "../components/PurchaseItem";
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

function Shopping({ items, run, api, busy, refresh }) {
  const [name, setName] = useState(""),
    [error, setError] = useState(""),
    [quantity, setQuantity] = useState(""),
    [unit, setUnit] = useState("pcs"),
    [quantityError, setQuantityError] = useState(""),
    [purchasing, setPurchasing] = useState(null);
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
          const amount = amountInput(quantity, unit);
          setQuantityError(amount.error);
          setError(invalid);
          if (invalid || amount.error) {
            event.currentTarget.querySelector(invalid ? "#shopping-name" : "#shopping-quantity").focus();
            return;
          }
          if (
            await run(
              () => api("/shopping-items", { method: "POST", body: { name, ...amount.body } }),
              "Shopping item added.",
              ["shopping"],
            )
          ) {
            setName(""); setQuantity(""); setUnit("pcs");
          }
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
        <ShoppingAmount id="shopping" quantity={quantity} unit={unit}
          setQuantity={value => { setQuantity(value); setQuantityError(''); }}
          setUnit={value => { setUnit(value); setQuantityError(''); }} error={quantityError} disabled={busy} />
        <button type="submit" disabled={busy} className={inlineSubmit}>
          <Icon name="plus" className="w-[18px]" />
          Add item
        </button>
      </form>
      <p className="text-sm">Adding the same name with an amount replaces its shopping amount.</p>
      {!items.length ? (
        <Empty icon="bag" title="All set for now">
          Add an item here, or add missing ingredients from a recipe.
        </Empty>
      ) : (
        <ul className={itemList}>
          {items.map((item) => (
            <li key={item.id} className={`${itemRow} flex-wrap`}>
              <span className={itemSymbol}>
                <Icon name="bag" />
              </span>
              <strong className="block min-w-0 flex-1 text-[0.95rem] font-[550] wrap-anywhere">
                {item.name}
                {item.quantity != null && <span className="ml-2 text-[#607565]">· {item.quantity} {item.unit}</span>}
              </strong>
              <button type="button" className="btn-secondary mobile:w-full" disabled={busy}
                aria-label={`Bought — add to fridge: ${item.name}`} onClick={() => setPurchasing(item.id)}>Bought — add to fridge</button>
              <button
                className={removeButton}
                disabled={busy}
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
              {purchasing === item.id && <PurchaseItem item={item} api={api} run={run} busy={busy} refresh={refresh}
                onCancel={() => setPurchasing(null)} />}
            </li>
          ))}
        </ul>
      )}
      <p className="muted mx-0 mt-[25px] mb-0 text-[0.8rem]">
        Remove only deletes a shopping item. Use Bought — add to fridge to record a purchase.
      </p>
    </section>
  );
}

export default function ShoppingPage() {
  const { data, api, run, busy, loadResources } = useOutletContext();
  return <Shopping items={data.shopping} api={api} run={run} busy={busy}
    refresh={() => loadResources(api, ["shopping", "inventory"])} />;
}
